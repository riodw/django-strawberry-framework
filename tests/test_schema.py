"""Permanent behavioral tests for django_strawberry_framework.schema."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import strawberry

from django_strawberry_framework.extensions.error_policy import DjangoErrorPolicyExtension
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.schema import (
    DjangoMutationExecutionContext,
    DjangoSchema,
    _extension_entry_matches,
    _with_error_policy_extension,
    _with_resource_policy_extension,
)


class CustomErrorPolicyExtension(DjangoErrorPolicyExtension):
    pass


class CustomResourcePolicyExtension(DjangoResourcePolicyExtension):
    pass


@strawberry.type
class DummyQuery:
    @strawberry.field
    def hello(self) -> str:
        return "world"

    @strawberry.field
    def error_field(self) -> str:
        raise ValueError("Simulated field error")


@strawberry.type
class DummyMutation:
    @strawberry.mutation
    def plain_mutation(self) -> str:
        return "plain"


def test_schema_init_with_none_and_iterable_extensions():
    schema_none = DjangoSchema(query=DummyQuery, extensions=None)
    assert len(schema_none.extensions) >= 2

    schema_tuple = DjangoSchema(query=DummyQuery, extensions=(CustomErrorPolicyExtension,))
    assert any(
        isinstance(ext, type) and issubclass(ext, CustomErrorPolicyExtension)
        for ext in schema_tuple.extensions
    )

    def ext_gen():
        yield CustomErrorPolicyExtension

    schema_gen = DjangoSchema(query=DummyQuery, extensions=ext_gen())
    assert any(
        isinstance(ext, type) and issubclass(ext, CustomErrorPolicyExtension)
        for ext in schema_gen.extensions
    )


def test_schema_init_with_none_execution_context_class_falls_back():
    schema = DjangoSchema(query=DummyQuery, execution_context_class=None)
    assert schema.execution_context_class is DjangoMutationExecutionContext


def test_with_resource_policy_extension_shapes():
    assert _with_resource_policy_extension([]) == [DjangoResourcePolicyExtension]
    assert _with_resource_policy_extension(None) == [DjangoResourcePolicyExtension]
    assert _with_resource_policy_extension([DjangoResourcePolicyExtension]) == [
        DjangoResourcePolicyExtension,
    ]
    assert _with_resource_policy_extension([CustomResourcePolicyExtension]) == [
        CustomResourcePolicyExtension,
    ]


def test_with_error_policy_extension_shapes():
    assert _with_error_policy_extension([]) == [DjangoErrorPolicyExtension]
    assert _with_error_policy_extension([DjangoErrorPolicyExtension]) == [
        DjangoErrorPolicyExtension,
    ]
    assert _with_error_policy_extension([CustomErrorPolicyExtension]) == [
        CustomErrorPolicyExtension,
    ]


def test_extension_entry_matches_adversarial():
    assert _extension_entry_matches(DjangoErrorPolicyExtension(), DjangoErrorPolicyExtension)
    assert not _extension_entry_matches(
        DjangoResourcePolicyExtension(),
        DjangoErrorPolicyExtension,
    )
    assert not _extension_entry_matches(object(), DjangoErrorPolicyExtension)
    assert not _extension_entry_matches(123, DjangoErrorPolicyExtension)
    assert not _extension_entry_matches("string", DjangoErrorPolicyExtension)
    assert not _extension_entry_matches(None, DjangoErrorPolicyExtension)

    class BrokenMeta(type):
        def __subclasscheck__(cls, subclass):
            raise TypeError("Hostile metaclass check")

    class BrokenClass(metaclass=BrokenMeta):
        pass

    assert not _extension_entry_matches(DjangoErrorPolicyExtension, BrokenClass)
    assert not _extension_entry_matches(DjangoErrorPolicyExtension(), BrokenClass)


def test_get_extensions_sync_and_async():
    schema = DjangoSchema(query=DummyQuery)
    sync_exts = schema.get_extensions(sync=True)
    async_exts = schema.get_extensions(sync=False)
    assert len(sync_exts) >= 2
    assert len(async_exts) >= 2


def test_get_extensions_with_custom_factory_dedup():
    def error_factory():
        return DjangoErrorPolicyExtension()

    schema = DjangoSchema(query=DummyQuery, extensions=[error_factory])
    exts = schema.get_extensions(sync=True)
    error_exts = [e for e in exts if isinstance(e, DjangoErrorPolicyExtension)]
    assert len(error_exts) == 1


def test_get_extensions_when_explicitly_passed_class():
    schema = DjangoSchema(query=DummyQuery, extensions=[CustomErrorPolicyExtension])
    exts = schema.get_extensions(sync=True)
    error_exts = [e for e in exts if isinstance(e, DjangoErrorPolicyExtension)]
    assert len(error_exts) == 1
    assert isinstance(error_exts[0], CustomErrorPolicyExtension)


def test_marked_mutation_class_safe_on_none_parent_and_malformed_nodes():
    schema = DjangoSchema(query=DummyQuery)
    graphql_schema = schema._schema

    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx.schema = graphql_schema

    # parent_type is None when schema.mutation_type is None (query-only schema)
    assert ctx._marked_mutation_class(None, []) is None
    assert ctx._marked_mutation_class(None, None) is None

    # Schema with mutation
    schema_with_mut = DjangoSchema(query=DummyQuery, mutation=DummyMutation)
    ctx_mut = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx_mut.schema = schema_with_mut._schema
    mut_type = schema_with_mut._schema.mutation_type

    # parent_type is None when schema.mutation_type is present
    assert ctx_mut._marked_mutation_class(None, []) is None

    # field_nodes is empty / None / malformed
    assert ctx_mut._marked_mutation_class(mut_type, []) is None
    assert ctx_mut._marked_mutation_class(mut_type, None) is None
    assert ctx_mut._marked_mutation_class(mut_type, [object()]) is None

    # Introspection field (__typename)
    class FakeNode:
        name = type("Name", (), {"value": "__typename"})()

    assert ctx_mut._marked_mutation_class(mut_type, [FakeNode()]) is None

    # Plain strawberry mutation (unmarked)
    class PlainMutNode:
        name = type("Name", (), {"value": "plainMutation"})()

    assert ctx_mut._marked_mutation_class(mut_type, [PlainMutNode()]) is None

    # Missing field from parent_type.fields
    class MissingNode:
        name = type("Name", (), {"value": "doesNotExist"})()

    assert ctx_mut._marked_mutation_class(mut_type, [MissingNode()]) is None

    # parent_type with non-dict fields
    class NonDictFieldsParent:
        fields = ["not", "a", "dict"]

    ctx_non_dict = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx_non_dict.schema = SimpleNamespace(mutation_type=NonDictFieldsParent)
    named_node = SimpleNamespace(name=SimpleNamespace(value="some_mutation"))
    assert ctx_non_dict._marked_mutation_class(NonDictFieldsParent, [named_node]) is None


def test_execution_errors_fallback():
    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    assert ctx._execution_errors() == []

    ctx.collected_errors = object()
    assert ctx._execution_errors() == []


def test_schema_execute_sync_query():
    schema = DjangoSchema(query=DummyQuery)
    result = schema.execute_sync("query { hello }")
    assert result.errors is None
    assert result.data == {"hello": "world"}


@pytest.mark.asyncio
async def test_schema_execute_async_query():
    schema = DjangoSchema(query=DummyQuery)
    result = await schema.execute("query { hello }")
    assert result.errors is None
    assert result.data == {"hello": "world"}


def test_schema_execute_sync_error():
    schema = DjangoSchema(query=DummyQuery)
    result = schema.execute_sync("query { errorField }")
    assert result.errors is not None
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_schema_execute_async_error():
    schema = DjangoSchema(query=DummyQuery)
    result = await schema.execute("query { errorField }")
    assert result.errors is not None
    assert len(result.errors) == 1
