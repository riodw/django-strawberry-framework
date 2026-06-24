"""Form-mutations subsystem - the Django-``Form`` / ``ModelForm`` write side (spec-038).

A four-module subpackage in the spirit of ``mutations/`` (the module names
mirror it per spec-038 Decision 4):

- ``converter.py`` (Slice 1) - ``convert_form_field(field)``, the
  ``forms.Field``-keyed -> Strawberry annotation + required-ness registry for
  the model-less case (the graphene-django ``convert_form_field`` parity shape),
  plus the per-generated-input-field reverse-map record
  (``input_attr`` -> ``(form_field_name, kind)``) the Slice 3 resolver consults
  to build a form-field-keyed payload.
- ``inputs.py`` (Slice 1) - generated ``<FormClass>Input`` /
  ``<FormClass>PartialInput`` ``@strawberry.input`` classes built from a form's
  declared ``base_fields``, reusing the ``utils/inputs.py`` materialize / build
  core (the same machinery ``mutations/inputs.py`` wraps).
- ``sets.py`` (Slice 2) - the ``DjangoFormMutation`` / ``DjangoModelFormMutation``
  bases, their ``Meta`` validation, and the finalizer phase-2.5 bind.
- ``resolvers.py`` (Slice 3) - the sync + async instantiate -> ``is_valid()`` ->
  ``form.errors`` -> ``save()`` -> optimizer re-fetch -> payload pipeline.

Slice 2 adds ``sets.py`` (the two bases + ``Meta`` validation + the phase-2.5
bind) and the public re-exports below; the package-root ``__init__.py`` exports
``DjangoFormMutation`` / ``DjangoModelFormMutation`` from here. ``resolvers.py``
remains a Slice 3 concern.
"""

from __future__ import annotations

from .sets import DjangoFormMutation, DjangoModelFormMutation

__all__: tuple[str, ...] = ("DjangoFormMutation", "DjangoModelFormMutation")
