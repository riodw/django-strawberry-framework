"""Form-field -> Strawberry annotation conversion + the per-input-field reverse map (spec-038).

This module is the genuinely net-new machinery for the **model-less case**
(spec-038 Decision 7): a plain ``forms.Form`` field (a ``captcha``, a
``confirm_email``) has no Django model column and so no read-side equivalent in
``types/converters.py``. ``convert_form_field`` is the ``forms.Field``-keyed
registry that maps such a field to its Strawberry annotation + required-ness, in
the graphene-django ``convert_form_field`` parity shape, raised through the
package's own ``ConfigurationError``.

It is NOT a parallel copy of the read-side scalar table. A ``ModelForm`` field
that HAS a backing model column routes through the read-side
``convert_scalar`` / ``convert_choices_to_enum`` / ``relation_input_annotation``
at the ``forms/inputs.py`` build site (keyed on the resolved ``models.Field``),
so a ``choices`` form field resolves to the SAME generated enum the read
``DjangoType`` synthesizes (the symmetric wire contract). The two key spaces -
``forms.Field`` here, ``models.Field`` on the read side - stay strictly separate.

**Fail-loud dispatch.** The registry registers each supported class
*individually* (so subclasses map via the MRO walk - ``EmailField`` /
``SlugField`` / ``URLField`` / ``RegexField`` under ``CharField``), handles a
bare ``forms.Field`` as an explicit exact-type special case -> ``str``, and the
fallthrough (unregistered) default **raises** ``ConfigurationError`` naming the
field and class. Crucially there is **no base-``forms.Field`` catch-all
registration**: registering ``forms.Field`` -> ``str`` would shadow the raise so
every custom ``forms.Field`` subclass silently became ``String`` (the
graphene-django ``ImproperlyConfigured`` parity, lost). A custom
``class CustomField(forms.Field)`` with no supported ancestor therefore hits the
raising default.

**The reverse map.** The generated input GraphQL names follow the
cross-flavor ``036`` convention (a ``ModelChoiceField`` named ``category`` emits
``categoryId`` / python attr ``category_id``), but a bound Django form is keyed
by FORM-field name (``ItemModelForm(data={"category": pk})``, never
``{"category_id": pk}``). So ``forms/inputs.py`` retains, per generated input
field, a ``utils/inputs.py::InputFieldSpec`` (``target_name`` = form field name)
that ``forms/resolvers.py`` consults at decode to produce a
form-field-keyed payload, where ``kind`` is one of the four module constants
below. This module owns only the kind constants + ``convert_form_field``; the
reverse-map record type is single-sited on ``InputFieldSpec``.
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from typing import Any

import strawberry
from django import forms

from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_type_name
from ..utils.converters import (
    convert_with_mro,
    finish_field_conversion,
    make_kind_converter,
    make_scalar_converter,
)

# The four decode kinds the reverse-map record carries. Single-sourced in
# ``utils/inputs.py`` (one conceptual enum, not a per-flavor
# copy); re-exported here (the ``as`` form marks the explicit re-export) so the
# form resolver, the input builder, and the tests keep addressing them on
# this module (spec-038 Decision 7 P1).
from ..utils.inputs import FILE as FILE
from ..utils.inputs import RELATION_MULTI as RELATION_MULTI
from ..utils.inputs import RELATION_SINGLE as RELATION_SINGLE
from ..utils.inputs import SCALAR as SCALAR
from ..utils.inputs import FieldConversionBase


class FormFieldConversion(FieldConversionBase):
    """The model-less annotation + decode kind ``convert_form_field`` returns.

    ``required`` is the form field's own ``field.required``, except the exact
    built-in ``NullBooleanField`` which is always optional (Django's
    ``validate`` is a no-op and GraphQL cannot express required-nullable inputs -
    graphene-django parity). A validating ``NullBooleanField`` subclass keeps
    its declared requiredness and therefore resolves to a non-null ``bool``
    annotation, so GraphQL cannot permit omission while the generated dataclass
    still requires the value. ``annotation`` is the resolved Strawberry
    annotation for a SCALAR field; for a relation / file field the annotation is
    finalized at the ``forms/inputs.py`` build site (where the backing model
    column - if any - and the related primary ``DjangoType`` are known, so the
    Relay-``GlobalID``-vs-raw-pk id type can be resolved), so those kinds carry
    ``annotation=None`` here and
    only the ``kind`` is authoritative. The ``(annotation, kind, required)``
    value-object shape is the shared ``utils/inputs.py::FieldConversionBase``.
    """

    __slots__ = ()


def form_field_required(field: forms.Field, *, column: Any = None) -> bool:
    """The effective GraphQL-input requiredness of any form field (the one rule).

    An exact ``NullBooleanField`` has a no-op ``validate``, so its
    ``field.required`` is normally meaningless (omit / ``None`` both pass).
    Two shapes must retain declared requiredness, however:

    - a custom subclass may override validation and genuinely reject omission;
    - a ModelForm field backed by a non-null model column reaches model
      validation after the form field's no-op and rejects ``None``.

    GraphQL cannot express "required but nullable", but the non-null column
    shape has a non-null ``bool`` annotation already, so keeping
    ``required=True`` accurately rejects omission and null before execution.

    This is the SINGLE requiredness decision, shared by ``convert_form_field``
    (the annotation path) and ``forms/inputs.py``'s build site + create/partial
    required-field discovery, so the column-backed and column-less paths cannot
    drift. It is a pure attribute + ``isinstance`` read - it never converts - so
    required-field discovery over the full declared field set never raises on an
    excluded unsupported field.
    """
    if type(field) is not forms.NullBooleanField:
        return field.required
    if column is not None and not getattr(column, "null", True):
        return field.required
    return False


def _null_boolean_converter(field: forms.NullBooleanField) -> FormFieldConversion:
    """Convert ``NullBooleanField`` with an annotation matching requiredness.

    The exact built-in field keeps ``bool | None`` + an optional input default
    because its ``validate`` is a no-op. A subclass that restores real required
    validation must instead produce ``bool`` + no default; otherwise the
    generated GraphQL field is nullable while Strawberry's input dataclass still
    requires the keyword, allowing omission to reach a constructor ``TypeError``.
    """
    required = form_field_required(field)
    annotation = bool if required else bool | None
    return FormFieldConversion(annotation=annotation, kind=SCALAR, required=required)


def _scalar_converter(annotation: Any) -> Any:
    """Return a form scalar-table converter (``form_field_required`` for requiredness)."""
    return make_scalar_converter(
        FormFieldConversion,
        annotation,
        required_of=form_field_required,
    )


def _kind_converter(kind: str, annotation: Any = None) -> Any:
    """Return a form kind-precheck converter (``form_field_required`` for requiredness)."""
    return make_kind_converter(
        FormFieldConversion,
        kind,
        annotation=annotation,
        required_of=form_field_required,
    )


# Each supported ``forms.Field`` class -> a ``make_scalar_converter`` callable.
# Registered individually (not via a base-``Field`` catch-all) so subclasses map
# through the MRO walk in ``convert_form_field`` - ``EmailField`` / ``SlugField``
# / ``URLField`` / ``RegexField`` resolve under ``CharField``, the parity
# behavior. ``ChoiceField`` -> ``str`` is the model-less default; a ``ChoiceField``
# over a ModelForm model's ``choices`` is routed through the read-side enum at the
# build site instead. ``ModelChoiceField`` / ``ModelMultipleChoiceField`` /
# ``MultipleChoiceField`` / ``FileField`` / ``ImageField`` are deliberately NOT in
# this scalar table - they resolve by ``kind`` in ``convert_form_field`` before the
# walk reaches it.
#
# Resolution is a ``type(field).__mro__`` walk against this dict (the same idiom
# ``types/converters.py::scalar_for_field`` uses on the read side), so the
# MOST-specific registered class wins regardless of dict insertion order:
# ``FloatField`` / ``DecimalField`` both subclass ``IntegerField`` and
# ``UUIDField`` / ``JSONField`` subclass ``CharField``, so a linear "first
# ``isinstance`` wins" walk would mis-map them to the parent's scalar. The MRO
# walk visits the field's own class first, so each resolves to its own entry.
# ``JSONField`` must stay an explicit row (``strawberry.scalars.JSON``) - without
# it the CharField parent would silently type JSON payloads as ``String``,
# rejecting object / array literals that Django's form field (and the serializer
# / model scalar tables) accept as structured JSON.
_SCALAR_FORM_FIELDS: dict[type[forms.Field], Any] = {
    forms.CharField: _scalar_converter(str),
    forms.ChoiceField: _scalar_converter(str),
    forms.IntegerField: _scalar_converter(int),
    forms.FloatField: _scalar_converter(float),
    forms.DecimalField: _scalar_converter(decimal.Decimal),
    forms.NullBooleanField: _null_boolean_converter,
    forms.BooleanField: _scalar_converter(bool),
    forms.UUIDField: _scalar_converter(uuid.UUID),
    forms.JSONField: _scalar_converter(strawberry.scalars.JSON),
    forms.DateTimeField: _scalar_converter(datetime.datetime),
    forms.DateField: _scalar_converter(datetime.date),
    forms.TimeField: _scalar_converter(datetime.time),
}


def _bare_form_field(field: forms.Field) -> FormFieldConversion | None:
    """Exact-type ``forms.Field`` -> ``str``; any subclass continues the MRO walk.

    NOT a catch-all: an ``isinstance`` match that always returned a conversion
    would shadow the raising fallthrough. Returning ``None`` lets
    ``convert_with_mro`` continue. Ordered LAST in the precheck list so a
    supported subclass has already been offered to the scalar registry.
    """
    if type(field) is forms.Field:
        return FormFieldConversion(
            annotation=str,
            kind=SCALAR,
            required=form_field_required(field),
        )
    return None


# Kind prechecks that must win BEFORE the scalar walk reaches a parent class
# (``ModelChoiceField`` subclasses ``ChoiceField`` -> ``str``, etc.). Relation /
# file annotations are finalized at the build site (``annotation=None``).
_CONVERT_RELATION_MULTI = _kind_converter(RELATION_MULTI)
_CONVERT_RELATION_SINGLE = _kind_converter(RELATION_SINGLE)
_CONVERT_FILE = _kind_converter(FILE)
_CONVERT_MULTIPLE_CHOICE = _kind_converter(SCALAR, list[str])


def convert_form_field(field: forms.Field) -> FormFieldConversion:
    """Map a model-less ``forms.Field`` to its Strawberry annotation + decode kind.

    Returns a ``FormFieldConversion`` carrying the resolved scalar
    ``annotation`` (``None`` for the relation / file kinds, finalized at the
    build site), the decode ``kind``, and ``required`` from
    ``form_field_required`` (forced ``False`` for ``NullBooleanField`` - see
    ``FormFieldConversion``).

    Dispatch rides the shared ``utils/converters.py::convert_with_mro``
    skeleton (ordered prechecks, then the scalar registry MRO walk, then a
    raising fallthrough) with ``finish_field_conversion`` invoking a
    ``make_scalar_converter`` registry hit. It is NOT a
    ``functools.singledispatch`` with a ``forms.Field`` -> ``str`` catch-all
    (which would shadow the raise so every custom field silently became
    ``String`` - spec-038 Decision 7 P2):

    - relation / file kinds are matched first by ``isinstance`` (``ModelChoiceField``
      subclasses ``ChoiceField``, so it MUST win before the scalar walk reaches
      ``ChoiceField`` -> ``str``; ``FileField`` / ``ImageField`` likewise);
    - then ``MultipleChoiceField`` -> ``list[str]`` (it subclasses ``ChoiceField``
      and so must be checked before the scalar ``ChoiceField`` entry);
    - then the scalar registry MRO walk (``EmailField`` resolves under
      ``CharField``; ``FloatField`` / ``DecimalField`` resolve to their own
      entries, NOT the ``IntegerField`` they subclass, because the walk visits
      the field's own class first - the same reason ``UUIDField`` does not
      collapse to its ``CharField`` parent);
    - then the explicit exact-type special case ``type(field) is forms.Field``
      -> ``str`` (the listed "base ``Field`` -> ``str``", NOT a catch-all);
    - else the fallthrough **raises** ``ConfigurationError`` naming the field /
      class.

    The relation / multi pre-checks run before the scalar walk because
    ``ModelChoiceField`` / ``ModelMultipleChoiceField`` / ``MultipleChoiceField``
    all subclass ``ChoiceField`` (which the scalar table maps to ``str``), so the
    more-specific kind must win.
    """
    result = convert_with_mro(
        field,
        isinstance_prechecks=[
            (forms.ModelMultipleChoiceField, _CONVERT_RELATION_MULTI),
            (forms.ModelChoiceField, _CONVERT_RELATION_SINGLE),
            (forms.FileField, _CONVERT_FILE),
            (forms.MultipleChoiceField, _CONVERT_MULTIPLE_CHOICE),
            (forms.Field, _bare_form_field),
        ],
        scalar_registry=_SCALAR_FORM_FIELDS,
        fallthrough_error_factory=_unsupported_form_field,
    )
    return finish_field_conversion(result, field)


def _unsupported_form_field(field: forms.Field) -> ConfigurationError:
    """Build the fail-loud ``ConfigurationError`` for an unmapped ``forms.Field``.

    The fallthrough factory ``convert_with_mro`` raises when a field is matched by
    neither a precheck nor the scalar registry: an unregistered ``forms.Field``
    subclass with no supported ancestor (the graphene-django
    ``ImproperlyConfigured`` parity, raised as the package's own
    ``ConfigurationError``). Spelt as a factory so the no-catch-all contract -
    raise, never silently coerce to ``str`` - stays in this module's wording.
    Hostile ``__name__`` / ``__repr__`` ride the shared
    ``exceptions._safe_type_name`` / ``_safe_arg_repr`` guards.
    """
    return ConfigurationError(
        f"Unsupported form field type {_safe_type_name(field)!r} on form "
        f"field {_safe_arg_repr(field)}. convert_form_field has no mapping "
        "for it and no supported ancestor; register a supported base class, or "
        "supply a custom input_class field for it.",
    )
