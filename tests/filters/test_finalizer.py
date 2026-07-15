"""Finalizer tests for filter binding, owner-aware materialization, and orphan validation.

Covers:

- ``Meta.filterset_class`` validation (positive + negative).
- Four-subpass ordering per H1 of rev8 (every owner bound BEFORE any
  ``get_filters()`` runs across the whole registry).
- Strict multi-owner reuse per H2 of rev8: divergent
  ``graphql_type_name`` rejected; identical target accepted; idempotent
  re-bind of the same ``(filterset, definition)`` pair accepted.
- Materialization idempotency under the ``(name, cls)`` contract.
- Orphan ``filter_input_type`` references rejected with the spec-pinned
  actionable message.
- ``registry.clear()`` co-clears the input-class namespace, the
  ``_helper_referenced_filtersets`` set, and the ``_field_specs`` map.
- ``registry.clear()`` runs without ``ImportError`` when the filters
  package was never imported (subprocess test pins the cycle-safe
  contract per spec-021 line 822).
- Unresolved ``RelatedFilter`` propagates as ``ConfigurationError``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Shelf
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterSet,
    RelatedFilter,
    _helper_referenced_filtersets,
    filter_input_type,
)
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.filters.inputs import (
    INPUTS_MODULE_PATH,
    _field_specs,
    _materialized_names,
    clear_filter_input_namespace,
    materialize_input_class,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.finalizer import _bind_filterset_owner
from django_strawberry_framework.types.relay import apply_interfaces


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()
    _materialized_names.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    yield
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()
    _materialized_names.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()


# ---------------------------------------------------------------------------
# Subpass ordering - H1 of rev8.
# ---------------------------------------------------------------------------


def test_phase_2_5_binds_all_owners_before_expansion():
    """Subpass 1 must complete across both owners before any ``get_filters`` runs.

    Pre-declares ``GenreFilter`` so ``BookFilter`` can reference it as a
    class object (not a forward-string - that would force resolution
    against the test function's local scope which Slice 1's resolver
    cannot reach). Instruments ``GenreFilter.get_filters`` so each
    invocation records whether ``_owner_definition`` was already set.
    Without the four-subpass discipline an observation would land
    ``False`` when ``BookFilter.get_filters`` expanded
    ``RelatedFilter(GenreFilter)`` before ``GenreType`` was iterated.
    """

    class GenreFilter(FilterSet):
        class Meta:
            model = Genre
            fields = {"name": ["exact"]}

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    observations: list[bool] = []
    original_get_filters = GenreFilter.get_filters.__func__

    @classmethod
    def instrumented_get_filters(cls):  # type: ignore[no-redef]
        observations.append(cls._owner_definition is not None)
        return original_get_filters(cls)

    GenreFilter.get_filters = instrumented_get_filters  # type: ignore[method-assign]
    try:

        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = (
                    "id",
                    "title",
                    "shelf",
                    "genres",
                )
                filterset_class = BookFilter

        class GenreType(DjangoType):
            class Meta:
                model = Genre
                fields = ("id", "name")
                filterset_class = GenreFilter

        class ShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "code")
                filterset_class = ShelfFilter

        finalize_django_types()

        assert observations, "GenreFilter.get_filters was never called"
        assert all(observations), (
            "GenreFilter._owner_definition was unset during get_filters; "
            "subpass 1 did not complete across all owners before subpass 2 ran."
        )
    finally:
        del GenreFilter.get_filters


# ---------------------------------------------------------------------------
# Strict multi-owner reuse - H2 of rev8.
# ---------------------------------------------------------------------------


def test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity():
    """Two REAL owners diverging on own-PK Relay identity are rejected end-to-end.

    Exercises the genuinely owner-dependent axis of the H2-rev8 strict
    multi-owner check: one Relay-shaped owner and one plain owner share a
    single ``FilterSet``, so the shared filterset's own ``id`` filter
    would resolve to a GlobalID under one owner but a scalar under the
    other. ``finalize_django_types()`` must reject the second binding via
    ``_check_filterset_owner_pk_identity`` rather than silently pinning
    the first owner.

    Historical note: this test previously simulated divergence on the
    relation-TARGET axis by hand-planting a ``FakeOwnerDefinition`` on the
    filterset before finalize. That shape is structurally impossible now:
    the finalizer's pre-bind reset (``clear_filter_input_namespace`` in
    the before-bind loop) delattrs every FilterSet's ``_owner_definition``
    back to the default ``None``, wiping any pre-seed; and relation
    targets resolve via the process-global ``registry.primary_for(model)``
    keyed on the TARGET model - not the owner - so two legitimate owners
    (which share the filterset's ``Meta.model``) can never diverge there.
    Own-PK Relay identity is the axis that CAN diverge for real owners.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class RelayBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            primary = True
            filterset_class = BookFilter

    class PlainBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "own-primary-key Relay identity" in msg
    assert "BookFilter" in msg
    assert "RelayBookType" in msg
    assert "PlainBookType" in msg


def test_phase_2_5_accepts_multi_owner_with_identical_target():
    """Two distinct owner definitions sharing one ``FilterSet`` succeed when targets match.

    Pins the H2-rev8 strict-equality walk through ``related_filters``
    (per spec-021 line 1030's companion to
    ``test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity``). The
    pre-existing
    ``test_phase_2_5_accepts_idempotent_rebind_of_same_filterset_owner_pair``
    only exercises the ``previous is definition`` identity short-circuit
    in ``_bind_filterset_owner``; this test forces two distinct
    ``DjangoTypeDefinition`` instances to walk the strict-equality compare
    and confirms the legitimate same-target case is accepted.

    Setup: two ``DjangoType``s registered against ``Book`` (one primary,
    one secondary per ``Meta.primary``); both share one ``BookFilter``
    whose ``shelf = RelatedFilter(ShelfFilter, field_name="shelf")``
    declaration is a single ``RelatedFilter`` entry. Both owner
    definitions consult ``Book._meta.get_field("shelf").related_model``,
    which is the same ``Shelf``; ``registry.primary_for(Shelf)`` returns
    ``ShelfType`` for both - so ``related_target_for("shelf")`` returns
    ``(ShelfDefinition, <ForeignKey>)`` from both owner contexts, the
    target ``DjangoTypeDefinition`` identity matches, and the
    ``_graphql_type_name`` strings match. Assert: no raise, and the
    ``_owner_definition`` slot stores the FIRST binding per spec-021
    line 665.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class PrimaryBookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            primary = True
            filterset_class = BookFilter

    class SecondaryBookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    # Two distinct definitions both bind the same BookFilter; the
    # strict-equality walk through ``related_filters`` evaluates
    # ``related_target_for("shelf")`` from each owner's context and
    # accepts the match because both resolve to the same
    # ``ShelfDefinition`` with the same ``graphql_type_name``.
    finalize_django_types()

    primary_definition = PrimaryBookType.__django_strawberry_definition__
    secondary_definition = SecondaryBookType.__django_strawberry_definition__
    # The two owner definitions are distinct (NOT the same identity);
    # the strict-equality walk - not the ``previous is definition``
    # short-circuit - is what accepted the second binding.
    assert primary_definition is not secondary_definition
    # The ``_owner_definition`` slot stores the FIRST binding per spec-021
    # line 665. Iteration order from ``registry.iter_definitions()`` is
    # registration order, so ``PrimaryBookType`` (declared first) wins.
    assert BookFilter._owner_definition is primary_definition


def test_phase_2_5_accepts_idempotent_rebind_of_same_filterset_owner_pair():
    """Re-binding the same ``(filterset, definition)`` pair is a no-op."""

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    finalize_django_types()
    bound = BookFilter._owner_definition
    assert bound is BookType.__django_strawberry_definition__

    # A second finalize is a no-op (registry.is_finalized() guard).
    finalize_django_types()
    assert BookFilter._owner_definition is bound


# ---------------------------------------------------------------------------
# Orphan ``filter_input_type`` references - H5 of rev5.
# ---------------------------------------------------------------------------


def test_orphan_filter_input_type_reference_raises_at_finalize():
    """A ``filter_input_type(StandaloneFilter)`` without ``Meta.filterset_class`` raises."""

    class StandaloneFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    # Helper-reference the filterset without wiring it to any DjangoType.
    filter_input_type(StandaloneFilter)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "StandaloneFilter" in msg
    assert "filterset_class = StandaloneFilter" in msg


def test_phase_2_5_orphan_check_runs_before_materialization():
    """Orphan failure leaves no partial state in the materialization ledgers.

    Subpass 3 (orphan validation) now runs BEFORE subpass 4
    (materialization), so a failed finalize does not leave wired
    filtersets' input classes registered in ``_materialized_names`` /
    ``FilterArgumentsFactory.input_object_types``. The previous
    ordering meant a re-run of ``finalize_django_types()`` after
    fixing the orphan would see stale ledger entries from the prior
    failed attempt.
    """

    class WiredFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class StandaloneFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    # The wired filterset would normally be materialized; the
    # standalone filterset is an orphan that must trigger the failure.
    filter_input_type(StandaloneFilter)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = WiredFilter

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    # No input class registered for either filterset; the wired one's
    # would-be input type stayed un-materialized because the orphan
    # check halted the pass before subpass 4 ran.
    wired_input_name = f"{WiredFilter.__name__}InputType"
    assert wired_input_name not in FilterArgumentsFactory.input_object_types
    assert wired_input_name not in _materialized_names


def test_phase_2_5_orphan_validation_lists_every_orphan_filterset():
    """Two orphan FilterSets surface in one ``ConfigurationError`` with the multi-orphan lead-in.

    The single-orphan branch is exercised by
    ``test_orphan_filter_input_type_reference_raises_at_finalize``; this
    test pins the multi-orphan arm of
    ``_format_orphan_filtersets_error``: lead-in
    ``"FilterSets referenced via filter_input_type(...) but not wired to
    any DjangoType:"`` followed by ``__module__.__qualname__``-sorted
    offenders. Without this test the multi-orphan branch could silently
    drift (e.g., inverting the sort key, dropping the lead-in) without
    a regression signal.
    """

    class StandaloneFilterA(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class StandaloneFilterB(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    filter_input_type(StandaloneFilterA)
    filter_input_type(StandaloneFilterB)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    # Multi-orphan lead-in (mirrors ``_format_unresolved_targets_error``'s shape).
    assert (
        "FilterSets referenced via filter_input_type(...) but not wired to any DjangoType:" in msg
    )
    # Both offenders surface.
    assert "StandaloneFilterA" in msg
    assert "StandaloneFilterB" in msg
    # Actionable suggestion for the multi-orphan arm.
    assert "Add 'filterset_class = <Name>' to the relevant DjangoType's Meta" in msg
    # Sort key contract: offenders ordered by ``__module__.__qualname__``.
    # ``StandaloneFilterA`` < ``StandaloneFilterB`` lexicographically; same module.
    idx_a = msg.index("StandaloneFilterA")
    idx_b = msg.index("StandaloneFilterB")
    assert idx_a < idx_b, (
        "Multi-orphan offenders must be sorted by '__module__.__qualname__'; "
        f"StandaloneFilterA appeared at index {idx_a}, "
        f"StandaloneFilterB at index {idx_b}."
    )


# ---------------------------------------------------------------------------
# Materialization & idempotency - Decision 9.
# ---------------------------------------------------------------------------


def test_phase_2_5_subpass_3_materializes_input_classes_as_module_globals():
    """The materialize pass writes ``BookFilterInputType`` to the inputs module globals."""

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    finalize_django_types()

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookFilterInputType")
    assert "BookFilterInputType" in _materialized_names


def test_materialize_input_class_is_idempotent_on_same_pair():
    """Re-materializing the same ``(name, cls)`` pair is a no-op."""

    class _Stub:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_Stub"

    materialize_input_class("StubInputType", _Stub)
    materialize_input_class("StubInputType", _Stub)

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert inputs_module.StubInputType is _Stub
    assert _materialized_names["StubInputType"] is _Stub

    delattr(inputs_module, "StubInputType")


def test_materialize_input_class_rejects_collision_on_distinct_classes():
    """Re-materializing a name against a different class raises."""

    class _StubA:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_StubA"

    class _StubB:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_StubB"

    materialize_input_class("CollisionInputType", _StubA)
    with pytest.raises(ConfigurationError, match="two distinct FilterSet input classes"):
        materialize_input_class("CollisionInputType", _StubB)

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    delattr(inputs_module, "CollisionInputType")


# ---------------------------------------------------------------------------
# Registry clear - Decision 9 lifecycle.
# ---------------------------------------------------------------------------


def test_registry_clear_clears_filter_input_namespace_and_helper_set():
    """``registry.clear()`` resets the ledger and the helper set.

    Materialized class objects are intentionally left parked in
    ``filters.inputs.__dict__`` so a consumer-held ``strawberry.lazy``
    LazyType still resolves between ``registry.clear()`` and the next
    ``finalize_django_types()`` call; ``materialize_input_class``
    overwrites the parked global in place on the next finalize.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    filter_input_type(BookFilter)
    assert BookFilter in _helper_referenced_filtersets

    # Materialize one input class directly.
    class _Stub:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_Stub"

    materialize_input_class("LedgerStubInputType", _Stub)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "LedgerStubInputType")

    registry.clear()

    # Ledger cleared so the next finalize re-emits, but the parked
    # class object stays in `module.__dict__` for any held LazyType.
    assert _materialized_names == {}
    assert _field_specs == {}
    assert _helper_referenced_filtersets == set()
    assert hasattr(inputs_module, "LedgerStubInputType")
    assert inputs_module.LedgerStubInputType is _Stub

    # Teardown the parked global so the autouse fixture starts clean.
    delattr(inputs_module, "LedgerStubInputType")


def test_clear_filter_input_namespace_can_be_called_directly():
    """The public helper resets the ledger; parked module globals survive."""

    class _Stub:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_Stub"

    materialize_input_class("DirectClearInputType", _Stub)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "DirectClearInputType")

    clear_filter_input_namespace()

    # Ledger cleared so the next finalize re-emits, but the parked
    # class object stays in place so any consumer-held LazyType
    # resolves until the next `materialize_input_class` overwrites it.
    assert _materialized_names == {}
    assert hasattr(inputs_module, "DirectClearInputType")
    assert inputs_module.DirectClearInputType is _Stub

    # Teardown the parked global so the autouse fixture starts clean.
    delattr(inputs_module, "DirectClearInputType")


def test_registry_clear_works_without_filters_imported():
    """``registry.clear()`` must not raise when filters package was never imported."""
    # Absolute, ``__file__``-derived path so the subprocess resolves the
    # example app regardless of pytest's working directory.
    fakeshop = Path(__file__).resolve().parents[2] / "examples" / "fakeshop"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import django; "
                "import os; "
                f"import sys; sys.path.insert(0, {str(fakeshop)!r}); "
                "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
                "django.setup(); "
                "import django_strawberry_framework.registry as r; "
                "assert 'django_strawberry_framework.filters' not in sys.modules; "
                "r.registry.clear()"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Unresolved RelatedFilter propagation.
# ---------------------------------------------------------------------------


def test_phase_2_5_unresolved_related_filter_raises_at_finalize():
    """A ``RelatedFilter("UnknownFilter")`` propagates as ``ConfigurationError``.

    Slice 1's ``LazyRelatedClassMixin.resolve_lazy_class`` raises
    ``ImportError`` at Layer-2 resolution time. The phase-2.5 binding
    pass re-wraps the ``ImportError`` as ``ConfigurationError`` per
    spec-021 lines 416 + 1030 and the package's "finalize-time errors
    are ``ConfigurationError``" convention; the original
    ``ImportError`` is preserved on ``__cause__`` so the failure mode
    is loud AND grep-stable against the sibling formatter convention.
    """

    class BookFilter(FilterSet):
        unknown = RelatedFilter("UnknownFilter", field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookFilter" in msg
    assert "unresolved" in msg
    assert "UnknownFilter" in msg
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_phase_2_5_unregistered_related_filter_target_raises_at_finalize():
    """A wired filterset whose ``RelatedFilter`` target model has no registered type raises.

    Subpass 2.5: a related branch's visibility scoping runs the target
    type's ``get_queryset`` (spec-027 Decision 8 step 3), so a
    ``RelatedFilter`` whose target model has no registered ``DjangoType``
    is unfulfillable even though its input field would be materialized
    into the schema. The misconfiguration surfaces at finalize, naming
    the filterset, instead of on the first request that activates the
    branch (where ``FilterSet._iter_visibility_steps`` raises the runtime
    sibling of this error).
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    # No ShelfType registered - only the parent owner is wired.
    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookFilter" in msg
    assert "'shelf'" in msg
    assert "Shelf" in msg
    assert "no DjangoType is registered" in msg


def test_phase_2_5_unregistered_target_check_walks_transitive_filtersets():
    """Subpass 2.5 reaches ``RelatedFilter``s on UNWIRED child filtersets.

    The misconfigured ``RelatedFilter`` here lives on ``ShelfFilter``,
    which is never wired via ``Meta.filterset_class`` - it is only
    reachable as the target of the wired ``BookFilter.shelf`` branch.
    The sweep must walk wired filtersets transitively (with a visited
    set, since ``RelatedFilter`` cross-references may be cyclic) so a
    nested branch cannot smuggle an unregistered target past finalize.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = Branch
            fields = {"name": ["exact"]}

    class ShelfFilter(FilterSet):
        # Branch has no registered DjangoType below; this nested branch
        # is the misconfiguration the transitive walk must surface.
        branch = RelatedFilter(BranchFilter, field_name="branch")

        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            filterset_class = BookFilter

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "ShelfFilter" in msg
    assert "'branch'" in msg
    assert "no DjangoType is registered" in msg


def test_phase_2_5_non_import_get_filters_failure_rewraps_as_configuration_error():
    """Non-ImportError raised during ``get_filters()`` surfaces as ``ConfigurationError``.

    Subpass 2 only special-cased ``ImportError`` previously; any other
    exception (e.g. a ``RelatedFilter`` callable factory that raises
    ``ValueError`` when evaluated) used to bubble unwrapped, breaking
    the package's "finalize-time errors are ``ConfigurationError``"
    convention. The non-import branch now rewraps with the original on
    ``__cause__`` so consumer error-matching stays uniform.
    """

    def _broken_factory():
        raise ValueError("intentional factory failure")

    class BookFilter(FilterSet):
        # `LazyRelatedClassMixin.resolve_lazy_class` invokes the callable
        # when `.filterset` is read; this only happens at expansion time
        # (subpass 2), not at class creation, so the class itself builds
        # cleanly.
        broken = RelatedFilter(_broken_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookFilter" in msg
    assert "ValueError" in msg
    assert "intentional factory failure" in msg
    assert isinstance(exc_info.value.__cause__, ValueError)


# ---------------------------------------------------------------------------
# Relay-shaped owner accepted under phase 2.5.
# ---------------------------------------------------------------------------


def test_phase_2_5_runs_under_relay_node_interface():
    """Phase 2.5 filter binding cooperates with Relay-Node interface injection."""

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            interfaces = (relay.Node,)
            filterset_class = BookFilter

    finalize_django_types()

    # Owner binding ran and the Relay-Node hooks survived.
    assert BookFilter._owner_definition is BookType.__django_strawberry_definition__
    assert issubclass(BookType, relay.Node)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookFilterInputType")
    # Silence ``strawberry`` import unused at module scope.
    assert strawberry is not None


# ---------------------------------------------------------------------------
# _bind_filterset_owner - direct unit coverage of the binding branches.
# ---------------------------------------------------------------------------


def _owner_definition_stub(name):
    """Return a minimal owner-definition-shaped object for binding tests."""

    class _Stub:
        origin = type(name, (), {})
        model = None  # real owner definitions always carry a Django model

        def __init__(self, resolver=None):
            self._resolver = resolver

        def related_target_for(self, field_name):
            return self._resolver(field_name) if self._resolver is not None else None

    return _Stub


def test_bind_filterset_owner_idempotent_for_same_definition():
    """Re-binding the SAME definition object short-circuits via identity."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    Stub = _owner_definition_stub("OwnerType")
    definition = Stub()
    _bind_filterset_owner(ShelfFilter, definition)  # previous None -> bind
    _bind_filterset_owner(ShelfFilter, definition)  # previous IS definition -> return
    assert ShelfFilter._owner_definition is definition


def test_bind_filterset_owner_continues_when_both_targets_unresolved():
    """A field neither owner can resolve is skipped (both-None continue)."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    Stub = _owner_definition_stub("OwnerType")
    first = Stub(resolver=lambda _f: None)
    second = Stub(resolver=lambda _f: None)
    _bind_filterset_owner(BookFilter, first)
    # Second distinct owner: ``shelf`` resolves to None from both -> continue,
    # no raise, and the first binding is preserved.
    _bind_filterset_owner(BookFilter, second)
    assert BookFilter._owner_definition is first


def test_bind_filterset_owner_rejects_filterset_model_unrelated_to_owner():
    """A first bind whose filterset ``Meta.model`` is unrelated to the owner raises (H-core-3).

    The single most common Phase-2.5 user error is wiring
    ``Meta.filterset_class`` to a FilterSet keyed on an entirely different
    model. Without this guard the FIRST binding stores silently and the
    mismatch only surfaces at query time as an opaque ``FieldError``; the
    guard fails loud at finalize, naming both models.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookOwnerType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    book_def = BookOwnerType.__django_strawberry_definition__
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_filterset_owner(ShelfFilter, book_def)
    msg = str(exc_info.value)
    assert "ShelfFilter" in msg
    assert "Shelf" in msg  # the filterset's own Meta.model
    assert "Book" in msg  # the owner's model
    # The rejected owner must NOT have been stored.
    assert getattr(ShelfFilter, "_owner_definition", None) is None


def test_bind_filterset_owner_rejects_diverging_own_pk_relay_node_ness():
    """A Relay-node owner and a plain owner cannot share one FilterSet (H4b).

    The filterset's own ``id`` resolves to a GlobalID under the Relay owner
    but a scalar under the plain owner - an own-PK ambiguity the binding
    must reject loudly rather than silently pinning to whichever bound
    first. This is the genuine owner-dependent axis (relation targets
    resolve globally by target model and cannot diverge).
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class RelayShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    class PlainShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    # ``apply_interfaces`` injects ``relay.Node`` so ``implements_relay_node``
    # sees the Relay owner as a node (the finalizer's phase-2.5 step, run
    # here in isolation).
    apply_interfaces(RelayShelfType, RelayShelfType.__django_strawberry_definition__)

    relay_def = RelayShelfType.__django_strawberry_definition__
    plain_def = PlainShelfType.__django_strawberry_definition__

    _bind_filterset_owner(ShelfFilter, relay_def)  # first binds
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_filterset_owner(ShelfFilter, plain_def)
    msg = str(exc_info.value)
    assert "own-primary-key Relay identity" in msg
    assert "RelayShelfType" in msg
    assert "PlainShelfType" in msg


def test_bind_filterset_owner_rejects_diverging_own_pk_type_name():
    """Two Relay-node owners with different GraphQL type names can't share a FilterSet (H4b).

    Each owner types the own-PK GlobalID to its own ``graphql_type_name``,
    so the shared ``id`` filter would validate GlobalIDs against whichever
    owner finalized first.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class FirstShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    class SecondShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    apply_interfaces(FirstShelfType, FirstShelfType.__django_strawberry_definition__)
    apply_interfaces(SecondShelfType, SecondShelfType.__django_strawberry_definition__)

    _bind_filterset_owner(ShelfFilter, FirstShelfType.__django_strawberry_definition__)
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_filterset_owner(ShelfFilter, SecondShelfType.__django_strawberry_definition__)
    assert "own-primary-key Relay identity" in str(exc_info.value)


def test_bind_filterset_owner_raises_when_one_owner_resolves_and_other_does_not():
    """A field resolved by one owner but not the other is a hard mismatch."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    Stub = _owner_definition_stub("OwnerType")
    target_def = type("ResolvedShelfDefinition", (), {"origin": type("ResolvedShelfType", (), {})})
    first = Stub(resolver=lambda _f: None)
    second = Stub(resolver=lambda _f: (target_def, object()))
    _bind_filterset_owner(BookFilter, first)
    with pytest.raises(ConfigurationError) as excinfo:
        _bind_filterset_owner(BookFilter, second)
    assert "shelf" in str(excinfo.value)


def test_phase_2_5_configuration_error_from_get_filters_propagates_unwrapped():
    """A ``ConfigurationError`` raised inside ``get_filters()`` is re-raised as-is.

    The finalize loop special-cases ``ImportError`` (rewrap) and generic
    ``Exception`` (rewrap), but a ``ConfigurationError`` is already the
    canonical finalize-time error class, so it propagates unchanged rather
    than being double-wrapped.
    """

    def _config_error_factory():
        raise ConfigurationError("intentional configuration failure inside get_filters")

    class BookFilter(FilterSet):
        broken = RelatedFilter(_config_error_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    # Re-raised unchanged: the original message survives, not the
    # "Cannot finalize ..." rewrap used for ImportError / generic failures.
    assert "intentional configuration failure inside get_filters" in str(excinfo.value)
