"""Fail-loud converter-dispatch skeleton shared by the form + serializer converters (spec-039 P1.4).

The single owner of the ordered-precheck -> MRO-walk -> raising-fallthrough
control flow both ``forms/converter.py::convert_form_field`` and
``rest_framework/serializer_converter.py::convert_serializer_field`` run. Before
spec-039 the form converter spelled this walk free-standing; the serializer
converter would have been the second copy of the subtle no-silent-catch-all
contract. Promoting the skeleton single-sites it so the GOAL-mandated
"unmapped field RAISES, never silently becomes ``String``" contract is written
once (spec-039 Decision 4 / the Cross-flavor DRY obligation P1.4).

What lives here is mechanics only. Each caller supplies its own flavor-specific
prechecks (the ``isinstance`` kind detections a relation / file / multi-choice
field must win on BEFORE the scalar walk reaches a parent class), its own scalar
registry (``forms.Field`` -> annotation for the form side, DRF
``serializers.Field`` -> annotation for the serializer side), and its own
fallthrough error factory (the package's ``ConfigurationError`` either way). The
two key spaces stay strictly separate; this module imports neither
``django.forms`` nor ``rest_framework``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def convert_with_mro(
    field: Any,
    *,
    isinstance_prechecks: list[tuple[type | tuple[type, ...], Callable[[Any], Any]]],
    scalar_registry: dict[type, Any],
    fallthrough_error_factory: Callable[[Any], Exception],
) -> Any:
    """Dispatch ``field`` to a conversion via ordered prechecks, an MRO walk, then a raise.

    The flavor-agnostic body of ``forms/converter.py::convert_form_field`` (and
    ``rest_framework/serializer_converter.py::convert_serializer_field``), single-sited
    so the no-silent-catch-all contract lands once (spec-039 P1.4).

    Control flow, in order:

    1. **Ordered ``isinstance`` prechecks.** Each entry is ``(types, handler)``;
       the first entry whose ``isinstance(field, types)`` is true calls
       ``handler(field)`` and returns its result. Order is load-bearing: a
       relation / file / multi-choice field subclasses a scalar field whose
       registry entry would otherwise win, so the more-specific kind MUST be
       checked first (``ModelChoiceField`` before ``ChoiceField`` -> ``str``;
       DRF ``PrimaryKeyRelatedField`` / ``FileField`` before any scalar). A
       precheck handler may itself return ``None`` only if the caller wants the
       walk to continue, but the standard callers always produce a conversion.

    2. **Scalar registry MRO walk.** Walks ``type(field).__mro__`` against
       ``scalar_registry`` so the MOST-specific registered class wins regardless
       of dict insertion order (``FloatField`` / ``DecimalField`` resolve to
       their own entry, NOT the ``IntegerField`` they subclass; a supported
       field's UNregistered subclass resolves to its parent's scalar -
       ``EmailField`` under ``CharField``). The registry VALUE is returned
       as-is: a caller stores whatever conversion shape it wants (a bare
       annotation, or a ``(annotation, kind)`` pair / a callable the caller
       interprets).

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
            if result is not None:
                return result
    for klass in type(field).__mro__:
        if klass in scalar_registry:
            return scalar_registry[klass]
    raise fallthrough_error_factory(field)
