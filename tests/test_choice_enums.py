"""Tests for choice-field enum generation and caching.

The fakeshop models do not declare ``choices`` fields, so this file ships
a small in-test fixture model registered against the default app config
so the choice-enum path is exercised without polluting the example schema.

Wiring path: a session-scoped fixture defines a ``ChoiceFixture`` model
with a ``status = TextField(choices=[...])`` declaration, registers it
through ``django.apps`` for the duration of the session, and tears down
afterwards. See ``django.db.models.options.Options.contribute_to_class``
and ``Apps.register_model`` for the underlying mechanism; mirror what
``django-graphene-filters`` does in its choice-enum tests.
"""

import pytest


@pytest.fixture(scope="session")
def choice_fixture_model():
    """Build and register the in-test ``ChoiceFixture`` model for the session.

    TODO(slice 7): implement. The fixture should:

    1. Define a ``ChoiceFixture(models.Model)`` with at least one
       ``TextField(choices=[("a", "Alpha"), ("b", "Beta")])`` column.
    2. Register the model with ``django.apps.apps`` under a synthetic
       app label (e.g. ``"_dst_test_fixture"``).
    3. Yield the model class.
    4. On teardown, unregister to avoid leaking state into other tests.
    """
    pytest.skip("TODO(slice 7): in-test fixture model wiring pending")


@pytest.mark.skip(reason="TODO(slice 7): enum generation")
def test_choice_field_generates_strawberry_enum_named_typename_fieldname_enum(choice_fixture_model):
    """A ``DjangoType`` over ChoiceFixture should expose a ``ChoiceFixtureTypeStatusEnum``."""


@pytest.mark.skip(reason="TODO(slice 7): registry caching")
def test_choice_enum_cached_in_registry_keyed_by_model_field(choice_fixture_model):
    """``registry.get_enum(ChoiceFixture, "status")`` must return the generated enum after build."""


@pytest.mark.skip(reason="TODO(slice 7): cross-type enum reuse")
def test_two_djangotypes_reading_same_choice_field_share_one_enum(choice_fixture_model):
    """Two ``DjangoType``s pointing at ChoiceFixture.status must share the same enum object."""
