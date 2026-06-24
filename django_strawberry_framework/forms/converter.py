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

**Fail-loud dispatch (P2).** The registry registers each supported class
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

**The reverse map (P1).** The generated input GraphQL names follow the
cross-flavor ``036`` convention (a ``ModelChoiceField`` named ``category`` emits
``categoryId`` / python attr ``category_id``), but a bound Django form is keyed
by FORM-field name (``ItemModelForm(data={"category": pk})``, never
``{"category_id": pk}``). So ``forms/inputs.py`` retains, per generated input
field, a ``FormInputFieldSpec(input_attr, graphql_name, form_field_name, kind)``
record that ``forms/resolvers.py`` (Slice 3) consults at decode to produce a
form-field-keyed payload, where ``kind`` is one of the four module constants
below.
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from dataclasses import dataclass
from typing import Any

from django import forms

from ..exceptions import ConfigurationError

# The four decode kinds the reverse-map record carries. Pinned as module
# constants so the Slice 3 resolver and the tests address ONE source of truth
# instead of bare ``"scalar"`` / ``"relation_single"`` literals scattered across
# the converter / the input builder (spec-038 Decision 7 P1).
SCALAR: str = "scalar"
RELATION_SINGLE: str = "relation_single"
RELATION_MULTI: str = "relation_multi"
FILE: str = "file"


@dataclass(frozen=True)
class FormInputFieldSpec:
    """Per-generated-input-field metadata for the form-field-keyed decode (spec-038 P1).

    Sibling of ``utils/inputs.py::GeneratedInputFieldSpec`` but carries a
    ``form_field_name`` + a ``kind`` flag instead of a ``django_source_path``:
    the form decode needs the FORM-field key (not an ORM lookup path) and the
    decode kind (``scalar`` / ``relation_single`` / ``relation_multi`` /
    ``file``), because a bound Django form validates by form-field name and the
    relation / file kinds drive distinct decode paths in ``forms/resolvers.py``.

    - ``input_attr`` - the generated Strawberry dataclass attr (``category_id``
      for an FK relation, ``name`` for a scalar).
    - ``graphql_name`` - the camel-cased GraphQL wire name (``categoryId``).
    - ``form_field_name`` - the form's own declared field name (``category``),
      the key the bound form validates under.
    - ``kind`` - one of ``SCALAR`` / ``RELATION_SINGLE`` / ``RELATION_MULTI`` /
      ``FILE``.
    """

    input_attr: str
    graphql_name: str
    form_field_name: str
    kind: str


class FormFieldConversion:
    """The model-less annotation + decode kind ``convert_form_field`` returns.

    ``required`` is the form field's own ``field.required``. ``annotation`` is
    the resolved Strawberry annotation for a SCALAR field; for a relation / file
    field the annotation is finalized at the ``forms/inputs.py`` build site
    (where the backing column - if any - and the related primary ``DjangoType``
    are known, so the Relay-``GlobalID``-vs-raw-pk id type can be resolved), so
    those kinds carry ``annotation=None`` here and only the ``kind`` is
    authoritative.
    """

    __slots__ = ("annotation", "kind", "required")

    def __init__(
        self,
        *,
        annotation: Any,
        kind: str,
        required: bool,
    ) -> None:
        self.annotation = annotation
        self.kind = kind
        self.required = required


# Each supported ``forms.Field`` class -> the scalar annotation it maps to.
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
# ``UUIDField`` subclasses ``CharField``, so a linear "first ``isinstance`` wins"
# walk would mis-map them to the parent's scalar. The MRO walk visits the field's
# own class first, so each resolves to its own entry.
_SCALAR_FORM_FIELDS: dict[type[forms.Field], Any] = {
    forms.CharField: str,
    forms.ChoiceField: str,
    forms.IntegerField: int,
    forms.FloatField: float,
    forms.DecimalField: decimal.Decimal,
    forms.NullBooleanField: bool | None,
    forms.BooleanField: bool,
    forms.UUIDField: uuid.UUID,
    forms.DateTimeField: datetime.datetime,
    forms.DateField: datetime.date,
    forms.TimeField: datetime.time,
}


def convert_form_field(field: forms.Field) -> FormFieldConversion:
    """Map a model-less ``forms.Field`` to its Strawberry annotation + decode kind.

    Returns a ``FormFieldConversion`` carrying the resolved scalar
    ``annotation`` (``None`` for the relation / file kinds, finalized at the
    build site), the decode ``kind``, and ``required`` from ``field.required``.

    Dispatch is a ``type(field).__mro__`` walk over an individually-registered
    registry with a **raising fallthrough**, NOT a ``functools.singledispatch``
    with a ``forms.Field`` -> ``str`` catch-all (which would shadow the raise so
    every custom field silently became ``String`` - spec-038 Decision 7 P2):

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
    required = field.required

    # Relation kinds first: ``ModelMultipleChoiceField`` subclasses
    # ``ModelChoiceField`` subclasses ``ChoiceField``, so check the multi case
    # before the single before any ``ChoiceField`` scalar mapping. The relation
    # annotation is finalized at the build site (Relay-vs-raw-pk id type needs
    # the related primary ``DjangoType``), so ``annotation=None`` here.
    if isinstance(field, forms.ModelMultipleChoiceField):
        return FormFieldConversion(annotation=None, kind=RELATION_MULTI, required=required)
    if isinstance(field, forms.ModelChoiceField):
        return FormFieldConversion(annotation=None, kind=RELATION_SINGLE, required=required)

    # File kinds -> the ``Upload`` scalar (annotation finalized at the build
    # site alongside the scalar/relation branches, for a single ``kind``-driven
    # build loop). ``ImageField`` subclasses ``FileField``.
    if isinstance(field, forms.FileField):
        return FormFieldConversion(annotation=None, kind=FILE, required=required)

    # ``MultipleChoiceField`` (non-model) -> ``list[str]``; subclasses
    # ``ChoiceField`` so it must precede the scalar ``ChoiceField`` -> ``str``.
    if isinstance(field, forms.MultipleChoiceField):
        return FormFieldConversion(annotation=list[str], kind=SCALAR, required=required)

    # Scalar registry: walk ``type(field).__mro__`` so the MOST-specific
    # registered class wins (``NullBooleanField`` -> ``bool | None`` before its
    # ``BooleanField`` parent; ``FloatField`` / ``DecimalField`` / ``UUIDField``
    # before the ``IntegerField`` / ``CharField`` they subclass) while a
    # supported field's UNregistered subclass still resolves to its parent's
    # scalar (``EmailField`` / ``SlugField`` / ``URLField`` / ``RegexField`` under
    # ``CharField``). Mirrors ``types/converters.py::scalar_for_field``.
    for klass in type(field).__mro__:
        if klass in _SCALAR_FORM_FIELDS:
            return FormFieldConversion(
                annotation=_SCALAR_FORM_FIELDS[klass],
                kind=SCALAR,
                required=required,
            )

    # The base ``forms.Field`` is an explicit exact-type special case -> ``str``
    # (the listed "base ``Field`` -> ``str``"), NOT a catch-all registration:
    # registering it in ``_SCALAR_FORM_FIELDS`` would make the MRO walk match
    # EVERY ``forms.Field`` subclass, shadowing the raise below.
    if type(field) is forms.Field:
        return FormFieldConversion(annotation=str, kind=SCALAR, required=required)

    # Fallthrough: an unregistered ``forms.Field`` subclass with no supported
    # ancestor. Raise (the graphene-django ``ImproperlyConfigured`` parity,
    # raised as the package's own ``ConfigurationError``) rather than silently
    # coercing to ``str`` - the load-bearing fail-loud contract.
    raise ConfigurationError(
        f"Unsupported form field type {type(field).__name__!r} on form field "
        f"{field!r}. convert_form_field has no mapping for it and no supported "
        "ancestor; register a supported base class, or supply a custom input_class "
        "field for it.",
    )
