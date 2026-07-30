"""Form-mutations subsystem - the Django-``Form`` / ``ModelForm`` write side (spec-038).

A four-module subpackage in the spirit of ``mutations/`` (the module names
mirror it per spec-038 Decision 4):

- ``converter.py`` - ``convert_form_field(field)``, the
  ``forms.Field``-keyed -> Strawberry annotation + required-ness registry for
  the model-less case (the graphene-django ``convert_form_field`` parity shape),
  plus the decode-kind constants the resolver consults. The
  reverse-map record itself is ``utils/inputs.py::InputFieldSpec``
  (``target_name`` = form field name), built by ``forms/inputs.py``.
- ``inputs.py`` - generated ``<FormClass>Input`` /
  ``<FormClass>PartialInput`` ``@strawberry.input`` classes built from a form's
  declared ``base_fields``, reusing the ``utils/inputs.py`` materialize / build
  core (the same machinery ``mutations/inputs.py`` wraps).
- ``sets.py`` - the ``DjangoFormMutation`` / ``DjangoModelFormMutation``
  bases, their ``Meta`` validation, and the finalizer phase-2.5 bind.
- ``resolvers.py`` - the sync + async instantiate -> ``is_valid()`` ->
  ``form.errors`` -> ``save()`` -> optimizer re-fetch -> payload pipeline.

``sets.py`` (the two bases + ``Meta`` validation + the phase-2.5 bind) backs the
public re-exports below; the package-root ``__init__.py`` exports
``DjangoFormMutation`` / ``DjangoModelFormMutation`` from here.
"""

from __future__ import annotations

from .sets import DjangoFormMutation, DjangoModelFormMutation

__all__: tuple[str, ...] = ("DjangoFormMutation", "DjangoModelFormMutation")
