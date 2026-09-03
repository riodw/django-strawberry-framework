"""Fail-loud converter-dispatch skeleton shared by write-field and filter-input converters.

The single owner of the ordered-precheck -> MRO-walk -> raising-fallthrough
control flow ``forms/converter.py::convert_form_field``,
``rest_framework/serializer_converter.py::convert_serializer_field``, and
the filter convert / normalize pair in ``filters/inputs.py`` run. Before
spec-039 the form converter spelled this walk free-standing; the serializer
converter would have been the second copy of the subtle no-silent-catch-all
contract. Promoting the skeleton single-sites it so the GOAL-mandated
"unmapped field RAISES, never silently becomes ``String``" contract is written
once (spec-039 Decision 4). Filter convert/normalize share the same walk so
their kind order cannot drift (spec-053 C3).

What lives here is mechanics only. Each caller supplies its own flavor-specific
prechecks (the ``isinstance`` kind detections a relation / file / multi-choice
field must win on BEFORE the scalar walk reaches a parent class), its own scalar
registry (``forms.Field`` vs DRF ``serializers.Field`` keys - the two key spaces
stay strictly separate; this module imports neither ``django.forms`` nor
``rest_framework``; filter-input riders pass an empty registry), and its own
fallthrough error factory (the package's ``ConfigurationError`` either way).

The scalar-table VALUE shape is also single-sited here, without merging those
key spaces: ``make_scalar_converter`` / ``make_kind_converter`` build the
``FieldConversionBase`` callables both registries store, and
``finish_field_conversion`` is the post-walk invoke both ``convert_*_field``
callers share (prechecks return a finished instance; registry hits return a
callable that still needs ``field``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .inputs import SCALAR, FieldConversionBase

__all__ = [
    "MRO_CONTINUE",
    "convert_with_mro",
    "finish_field_conversion",
    "make_kind_converter",
    "make_scalar_converter",
]


class _MroContinue:
    """Sentinel: a precheck matched, but ``convert_with_mro`` should keep walking.

    ``None`` is a successful conversion (filter ``normalize_input_value`` may
    unwrap an enum member whose ``.value`` is ``None``). The bare-``forms.Field``
    exact-type precheck returns this sentinel for subclasses so the scalar
    registry can still run.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "MRO_CONTINUE"


MRO_CONTINUE = _MroContinue()


def convert_with_mro(
    field: Any,
    *,
    isinstance_prechecks: list[tuple[type | tuple[type, ...], Callable[[Any], Any]]],
    scalar_registry: dict[type, Any],
    fallthrough_error_factory: Callable[[Any], Exception],
) -> Any:
    """Dispatch ``field`` to a conversion via ordered prechecks, an MRO walk, then a raise.

    The flavor-agnostic body of ``forms/converter.py::convert_form_field``,
    ``rest_framework/serializer_converter.py::convert_serializer_field``, and
    the filter convert / normalize pair, single-sited so the no-silent-catch-all
    contract (and the filter kind order) lands once.

    Control flow, in order:

    1. **Ordered ``isinstance`` prechecks.** Each entry is ``(types, handler)``;
       the first entry whose ``isinstance(field, types)`` is true calls
       ``handler(field)`` and returns its result. Order is load-bearing: a
       relation / file / multi-choice field subclasses a scalar field whose
       registry entry would otherwise win, so the more-specific kind MUST be
       checked first (``ModelChoiceField`` before ``ChoiceField`` -> ``str``;
       DRF ``PrimaryKeyRelatedField`` / ``FileField`` before any scalar). A
       precheck handler may return ``MRO_CONTINUE`` to keep walking (the
       bare-``forms.Field`` exact-type pattern, and filter normalize skipping
       convert-only kinds). ``None`` is a real result, not a continue signal.

    2. **Scalar registry MRO walk.** Walks the field class's real ``__mro__``
       (read through ``type``'s raw getset descriptor so a hostile metaclass
       cannot intercept the read) against ``scalar_registry`` so the
       MOST-specific registered class wins regardless of dict insertion order
       (``FloatField`` / ``DecimalField`` resolve to their own entry, NOT the
       ``IntegerField`` they subclass; a supported field's UNregistered
       subclass resolves to its parent's scalar - ``EmailField`` under
       ``CharField``). The registry VALUE is returned as-is: the two write
       converters store ``make_scalar_converter`` callables and invoke them via
       ``finish_field_conversion``; tests of this skeleton may store any value
       (including a bare string).

    3. **Raising fallthrough.** A field matched by neither path is unsupported;
       ``fallthrough_error_factory(field)`` is raised (the package's
       ``ConfigurationError``). There is deliberately NO base-class catch-all
       registration: registering ``forms.Field`` / ``serializers.Field`` ->
       ``str`` would make the MRO walk match EVERY subclass and shadow this
       raise, the exact fail-loud regression the GOAL forbids.
    """
    for types, handler in isinstance_prechecks:
        if isinstance(field, types):
            result = handler(field)
            if result is not MRO_CONTINUE:
                return result
    # Read the actual MRO through ``type.__dict__``'s raw ``__mro__`` getset
    # descriptor rather than through any attribute-lookup protocol on the field
    # class's metaclass. A consumer-defined metaclass can override
    # ``__getattribute__`` - or define ``__mro__`` itself (a data descriptor on
    # the metaclass wins inside ``type.__getattribute__``'s own algorithm) - and
    # make any ``type(field).__mro__`` spelling raise or lie while the class
    # remains a valid field; conversion must still reach the typed
    # unsupported-field path.
    # Snapshot the registry once with the C-level dict copy: an exact-dict copy
    # runs no key/user protocol (no ``items`` / ``keys`` / ``__iter__`` / key
    # ``__hash__`` / ``__eq__`` dispatch) and is atomic under the GIL, so a
    # consumer registration on another thread cannot surface as "dictionary
    # changed size during iteration" mid-walk. The scan itself stays identity
    # based: a consumer metaclass may provide a hostile ``__hash__`` or
    # equality implementation, and ordinary dict membership would invoke it
    # before the converter can reach its parent or typed fallthrough.
    registry_entries = dict(scalar_registry)
    for klass in type.__dict__["__mro__"].__get__(type(field)):
        for registered, converter in registry_entries.items():
            if registered is klass:
                return converter
    raise fallthrough_error_factory(field)


def make_kind_converter(
    conversion_cls: type,
    kind: str,
    *,
    annotation: Any = None,
    required_of: Callable[[Any], bool] | None = None,
) -> Callable[[Any], Any]:
    """Return a converter emitting a ``conversion_cls`` instance for a fixed kind.

    The scalar-table / kind-precheck VALUE shape both write converters share
    without merging their KEY spaces. ``required_of`` is the genuine requiredness
    variation: omitted, the converter reads ``field.required`` (serializer);
    the form table passes ``form_field_required`` (NullBoolean).
    """

    def _convert(field: Any) -> Any:
        required = field.required if required_of is None else required_of(field)
        return conversion_cls(annotation=annotation, kind=kind, required=required)

    return _convert


def make_scalar_converter(
    conversion_cls: type,
    annotation: Any,
    *,
    required_of: Callable[[Any], bool] | None = None,
) -> Callable[[Any], Any]:
    """Return a converter emitting a ``SCALAR``-kind conversion for a fixed annotation.

    Convenience over ``make_kind_converter`` for the scalar-table rows: kind is
    always ``SCALAR``, and ``annotation`` is required (the Python / Strawberry
    scalar the flavor's field class maps to).
    """
    return make_kind_converter(
        conversion_cls,
        SCALAR,
        annotation=annotation,
        required_of=required_of,
    )


def finish_field_conversion(result: Any, field: Any) -> Any:
    """Turn a ``convert_with_mro`` result into a ``FieldConversionBase`` instance.

    Precheck handlers return a finished conversion; scalar-table entries are
    ``make_scalar_converter`` callables that still need ``field``. Both write
    converters share this split so the skeleton can stay value-agnostic (its
    tests pin non-callable registry values).
    """
    if isinstance(result, FieldConversionBase):
        return result
    return result(field)
