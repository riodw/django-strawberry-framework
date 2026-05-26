"""Multi-database cooperation tests at the optimizer-plan layer.

Scope (per spec ``docs/spec-019-multi_db-0_0_7.md`` Decision 5 + Test plan
``### tests/optimizer/test_multi_db.py``): this file holds the
optimizer-plan-level multi-db test that cannot be earned through a live
``/graphql/`` query against the example project. It does not exercise
FK-id elision, so it does not need a ``router.db_for_read`` mock.

- Consumer-provided ``OptimizerHint.prefetch(Prefetch(queryset=
  Child.objects.using("shard_b").all()))`` round-trips through plan
  construction with the inner queryset's ``_db`` intact. Pins Decision 3
  axis 3 — generated child querysets are intentionally NOT in scope per
  Decision 2.

Decision 3 axis 2 (explicit ``.using(alias)`` ``_db`` preservation through
``OptimizationPlan.apply``) is verified transitively by the Slice 2 live
``/graphql/`` test ``test_using_shard_b_resolver_returns_rows_seeded_on_shard_b``
in ``examples/fakeshop/test_query/test_multi_db.py``: if a future refactor
caused ``OptimizationPlan.apply`` to drop ``_db``, the resolver's
``Book.objects.using("shard_b")`` queryset would route to ``default``,
return zero rows, and the live test's seeded-titles assertion would fail.
Per ``AGENTS.md`` line 9, real-world live-HTTP coverage is preferred over
package-internal mocking when both reach the line.

The five resolver-level Slice 1 tests (FK-id elision branches + strictness
connection-agnostic shape) live in ``tests/types/test_resolvers.py`` per
rev2 H4 + rev3 R2 — both ``_build_fk_id_stub`` and ``_check_n1`` live in
``django_strawberry_framework/types/resolvers.py``, so the source-mirror
partner is the resolver-tests module.

Single pytest item; NO ``pytest.mark.parametrize`` fan-out so the
collected-item count matches the spec contract (one item from this file).
"""

from types import SimpleNamespace

from apps.products.models import Category, Item
from django.db.models import Prefetch

from django_strawberry_framework import OptimizerHint
from django_strawberry_framework.optimizer.field_meta import FieldMeta
from django_strawberry_framework.optimizer.walker import plan_optimizations
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.utils.strings import snake_case


def _sel(name, selections=None):
    """Build a synthetic ``SelectedField`` mirroring ``tests/optimizer/test_walker.py``."""
    return SimpleNamespace(
        name=name,
        alias=None,
        directives={},
        arguments={},
        selections=selections or [],
    )


def _register_type_definition(model, type_cls, *, optimizer_hints=None):
    """Register a minimal definition for walker-only synthetic type classes.

    Mirrors the helper at ``tests/optimizer/test_walker.py::_register_type_definition`` —
    inlined here per Worker 1's plan to keep this file's fixtures local
    and avoid cross-test-module import coupling.
    """
    selected_fields = tuple(model._meta.get_fields())
    registry.register(model, type_cls, primary=False)
    registry.register_definition(
        type_cls,
        DjangoTypeDefinition(
            origin=type_cls,
            model=model,
            name=None,
            description=None,
            fields_spec=None,
            exclude_spec=None,
            selected_fields=selected_fields,
            field_map={
                snake_case(field.name): FieldMeta.from_django_field(field) for field in selected_fields
            },
            optimizer_hints=optimizer_hints or {},
            has_custom_get_queryset=type_cls.has_custom_get_queryset(),
        ),
    )


def test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias():
    """Decision 3 axis 3 — ``OptimizerHint.prefetch(Prefetch(queryset=using))`` round-trips ``_db``."""

    class ParentType:
        @classmethod
        def has_custom_get_queryset(cls):
            return False

    explicit = Prefetch("items", queryset=Item.objects.using("shard_b").all())

    registry.clear()
    try:
        _register_type_definition(
            Category,
            ParentType,
            optimizer_hints={"items": OptimizerHint.prefetch(explicit)},
        )
        # ``source_type=ParentType`` so the walker's
        # ``_resolve_optimizer_hints(ParentType)``
        # (``django_strawberry_framework/optimizer/walker.py::_resolve_optimizer_hints``)
        # finds the consumer's hint instead of falling back to the
        # primary type lookup.
        plan = plan_optimizations(
            [_sel("items", selections=[_sel("id")])],
            Category,
            source_type=ParentType,
        )
    finally:
        registry.clear()

    # Apply against an UNROUTED parent queryset — the consumer's hint is
    # what carries the child alias, not the parent qs (rev2 H2 — generated
    # child querysets do NOT inherit the parent alias).
    result = plan.apply(Category.objects.all())

    # The walker either returns the consumer's ``Prefetch`` unchanged or
    # builds a fresh one with ``queryset=prefetch.queryset`` — same
    # queryset object reference either way, so ``_db`` survives by
    # reference. Verified at ``django_strawberry_framework/optimizer/walker.py::_prefetch_hint_for_path``.
    prefetch = next(p for p in result._prefetch_related_lookups if p.prefetch_through == "items")
    assert prefetch.queryset._db == "shard_b"
