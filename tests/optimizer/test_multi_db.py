"""Multi-database cooperation tests at the optimizer-plan layer.

TODO(spec-019 Slice 1, tests/optimizer/test_multi_db.py — NEW): pre-staged
scaffold per ``docs/spec-019-multi_db-0_0_7.md`` Slice 1. Worker 2 replaces
the ``raise NotImplementedError`` body in each test below with the
pseudocode that follows it.

Scope (per spec Decision 5 + Test plan ``### tests/optimizer/test_multi_db.py``):
this file holds the **two** optimizer-plan-level multi-db tests — neither
exercises FK-id elision, so neither needs a ``router.db_for_read`` mock.

- Test (f) — ``OptimizationPlan.apply(qs)`` preserves ``qs._db`` for an
  explicit ``Model.objects.using("shard_b").all()`` parent. Pins
  Decision 3 axis 2.
- Test (g) — consumer-provided ``OptimizerHint.prefetch(Prefetch(queryset=
  Child.objects.using("shard_b").all()))`` round-trips through plan
  construction with the inner queryset's ``_db`` intact. Pins Decision 3
  axis 3 — generated child querysets are intentionally NOT in scope per
  Decision 2.

The other five Slice 1 tests (FK-id elision branches + strictness
connection-agnostic shape) live in ``tests/types/test_resolvers.py`` per
rev2 H4 + rev3 R2 — both ``_build_fk_id_stub`` and ``_check_n1`` live in
``django_strawberry_framework/types/resolvers.py``, so the source-mirror
partner is the resolver-tests module.

Convention rules (rev2 S11): per-test docstrings are convention-matching
only — ``pyproject.toml [tool.ruff.lint.per-file-ignores]`` covers
``tests/**/*.py = ["D", "ANN", ...]``, so docstrings and annotations are
not gate-forced. No ``# noqa`` suppressions needed.

Single pytest item per test; NO ``pytest.mark.parametrize`` fan-out so the
collected-item count matches the spec contract (two items from this file).
"""

# TODO(spec-019 V1 — rev4 ``plan_optimizations`` call shape): the live
# signature at ``django_strawberry_framework/optimizer/walker.py:28-32``
# is::
#
#     def plan_optimizations(
#         selected_fields: list[Any],
#         model: type[models.Model],
#         info: Any | None = None,
#         *,
#         source_type: type | None = None,
#     ) -> OptimizationPlan:
#
# There is no positional ``parent_type``. Test (f) uses two positionals
# (no ``info``, no ``source_type`` — axis 2 does not exercise per-type
# hint lookup). Test (g) uses ``source_type=ParentType`` keyword so the
# walker picks up the parent type's ``Meta.optimizer_hints``.


def test_optimization_plan_apply_preserves_explicit_using_alias():
    """Decision 3 axis 2 — explicit ``.using()`` ``_db`` survives ``plan.apply``."""
    # TODO(spec-019 Slice 1 — test (f)): build the plan and assert _db survives.
    #
    # Pseudocode (per spec Test plan + rev4 V1 call-shape correction):
    #
    #     # 1. Build a fixture DjangoType with one FK relation (mirror the
    #     #    existing tests/optimizer/test_plans.py fixtures).
    #     class ParentType(DjangoType):
    #         class Meta:
    #             model = ParentModel
    #             fields = ("id", "name", "child")  # one FK ``child``
    #
    #     finalize_django_types()
    #
    #     # 2. Synthesize a selection-tree input for plan_optimizations.
    #     #    The shape mirrors tests/optimizer/test_plans.py — a list of
    #     #    selected GraphQL field nodes whose names match the model
    #     #    field names. See test_plans.py for the SimpleNamespace
    #     #    pattern with .name / .selections attributes.
    #     selected_fields = [SimpleNamespace(name="id", selections=[]), ...]
    #
    #     # 3. Build the plan — two positionals only. No ``info``, no
    #     #    ``source_type``: this axis does NOT need the per-type
    #     #    optimizer_hints lookup.
    #     plan = plan_optimizations(selected_fields, ParentModel)
    #
    #     # 4. Apply the plan to an explicitly-routed queryset and assert
    #     #    the alias survives.
    #     qs = ParentModel.objects.using("shard_b").all()
    #     result = plan.apply(qs)
    #     assert result._db == "shard_b"
    #
    # Verified at django_strawberry_framework/optimizer/plans.py:122 that
    # OptimizationPlan.apply calls only(), select_related(),
    # prefetch_related() on the queryset — all of which preserve _db by
    # Django queryset contract. The test pins that we don't accidentally
    # rebuild the queryset from scratch in a future refactor.
    raise NotImplementedError("TODO(spec-019 Slice 1 — test f)")


def test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias():
    """Decision 3 axis 3 — ``OptimizerHint.prefetch(Prefetch(queryset=using))`` round-trips ``_db``."""
    # TODO(spec-019 Slice 1 — test (g)): pin consumer-provided Prefetch _db round-trip.
    #
    # Pseudocode (per spec Test plan + rev2 H2 narrowing + rev4 V1 call-shape):
    #
    #     # 1. Build a fixture parent DjangoType that pins a per-relation
    #     #    consumer-provided Prefetch via Meta.optimizer_hints.
    #     from django.db.models import Prefetch
    #     from django_strawberry_framework import OptimizerHint
    #
    #     class ParentType(DjangoType):
    #         class Meta:
    #             model = ParentModel
    #             fields = ("id", "name", "children")
    #             optimizer_hints = {
    #                 "children": OptimizerHint.prefetch(
    #                     Prefetch(
    #                         "children",
    #                         queryset=ChildModel.objects.using("shard_b").all(),
    #                     ),
    #                 ),
    #             }
    #
    #     finalize_django_types()
    #
    #     # 2. Build selection tree that selects the ``children`` relation
    #     #    (so the walker hits the hint dispatch at walker.py:241-257).
    #     selected_fields = [SimpleNamespace(name="children", selections=[
    #         SimpleNamespace(name="id", selections=[]),
    #     ])]
    #
    #     # 3. Build the plan — source_type=ParentType so the walker calls
    #     #    _resolve_optimizer_hints(ParentType) at walker.py:119-126
    #     #    and finds the consumer's hint. Without source_type the
    #     #    walker falls back to registry.get(model) which finds the
    #     #    SAME type here (single registration) but a future refactor
    #     #    that distinguishes resolver-type from model-primary would
    #     #    break this test silently — keyword is the explicit pin.
    #     plan = plan_optimizations(
    #         selected_fields,
    #         ParentModel,
    #         source_type=ParentType,
    #     )
    #
    #     # 4. Apply to an UNROUTED parent queryset — the consumer's
    #     #    hint is what carries the alias, not the parent qs.
    #     result = plan.apply(ParentModel.objects.all())
    #
    #     # 5. Introspect the resulting Prefetch and assert _db survives.
    #     # _prefetch_related_lookups holds the Prefetch objects after
    #     # qs.prefetch_related(*plan.prefetch_related) (plans.py:135-137).
    #     prefetches = result._prefetch_related_lookups
    #     prefetch = next(p for p in prefetches if p.prefetch_through == "children")
    #     assert prefetch.queryset._db == "shard_b"
    #
    # Verified at django_strawberry_framework/optimizer/walker.py:503-532
    # that _prefetch_hint_for_path either returns the consumer's Prefetch
    # unchanged (when the lookup already matches the full_path) or builds
    # a fresh Prefetch with ``queryset=prefetch.queryset`` — same queryset
    # object reference either way, so _db is preserved by reference.
    #
    # IMPORTANT: this test pins ONLY the consumer-provided alias round
    # trip. Generated Prefetch child querysets do NOT inherit the parent
    # alias — rev2 H2 narrowed the contract; production-code expansion
    # is BACKLOG.md item 41 post-1.0.0 work, explicitly deferred per
    # Decision 2 (zero production code change).
    raise NotImplementedError("TODO(spec-019 Slice 1 — test g)")
