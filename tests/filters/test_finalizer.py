"""Tests for the spec-021 Slice 3 phase-2.5 filter-binding pass.

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

import pytest
import strawberry
from apps.library.models import Book, Genre, Shelf
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
# Subpass ordering — H1 of rev8.
# ---------------------------------------------------------------------------


def test_phase_2_5_binds_all_owners_before_expansion():
    """Subpass 1 must complete across both owners before any ``get_filters`` runs.

    Pre-declares ``GenreFilter`` so ``BookFilter`` can reference it as a
    class object (not a forward-string — that would force resolution
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
                fields = ("id", "title", "shelf", "genres")
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
# Strict multi-owner reuse — H2 of rev8.
# ---------------------------------------------------------------------------


def test_phase_2_5_rejects_multi_owner_with_diverging_target():
    """Two owners that resolve a shared field to different DjangoTypes raise."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    # Both PrimaryShelfType and SecondaryShelfType are registered against
    # Shelf, but only one is primary. ``PrimaryBookType`` resolves
    # ``shelf`` to ``PrimaryShelfType``; ``SecondaryBookType`` will
    # resolve to the same primary unless we force otherwise — to actually
    # test divergence we set the primary differently before each book
    # binds, but H2-rev8's check operates on the FilterSet's stored
    # ``_owner_definition`` vs the candidate. Simulate divergence by
    # manually pre-binding a different owner via direct registry use.
    class PrimaryShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            primary = True

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class PrimaryBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            primary = True
            filterset_class = BookFilter

    # Pre-bind BookFilter to a fake owner-definition whose
    # related_target_for returns a different target than PrimaryBookType's
    # to trigger H2-rev8 strict mismatch.
    fake_definition = PrimaryBookType.__django_strawberry_definition__

    class FakeOwnerDefinition:
        origin = type("OtherBookType", (), {"__qualname__": "OtherBookType"})
        name = None

        @staticmethod
        def related_target_for(field_name):
            if field_name == "shelf":

                class _SyntheticDefinition:
                    origin = type(
                        "DivergedShelfType",
                        (),
                        {"__qualname__": "DivergedShelfType"},
                    )
                    name = "DivergedShelfType"

                return (_SyntheticDefinition, object())
            return None

    BookFilter._owner_definition = FakeOwnerDefinition  # type: ignore[assignment]

    # Now finalize: the binding pass tries to bind ``PrimaryBookType``
    # over BookFilter and the H2-rev8 strict check rejects the diverging
    # target.
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "diverging targets" in msg
    assert "shelf" in msg
    # Ensure the canonical name resolution surfaced in the message.
    assert "DivergedShelfType" in msg or "PrimaryShelfType" in msg
    # Quiet the linter — fake_definition pinned for inspection.
    assert isinstance(fake_definition.origin.__qualname__, str)


def test_phase_2_5_accepts_multi_owner_with_identical_target():
    """Two distinct owner definitions sharing one ``FilterSet`` succeed when targets match.

    Pins the H2-rev8 strict-equality walk through ``related_filters``
    (per spec-021 line 1030's companion to
    ``test_phase_2_5_rejects_multi_owner_with_diverging_target``). The
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
    ``ShelfType`` for both — so ``related_target_for("shelf")`` returns
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
            fields = ("id", "title", "shelf", "genres")
            primary = True
            filterset_class = BookFilter

    class SecondaryBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf", "genres")
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
    # the strict-equality walk — not the ``previous is definition``
    # short-circuit — is what accepted the second binding.
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
            fields = ("id", "title", "shelf", "genres")
            filterset_class = BookFilter

    finalize_django_types()
    bound = BookFilter._owner_definition
    assert bound is BookType.__django_strawberry_definition__

    # A second finalize is a no-op (registry.is_finalized() guard).
    finalize_django_types()
    assert BookFilter._owner_definition is bound


# ---------------------------------------------------------------------------
# Orphan ``filter_input_type`` references — H5 of rev5.
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
            fields = ("id", "title", "shelf", "genres")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "StandaloneFilter" in msg
    assert "filterset_class = StandaloneFilter" in msg


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
            fields = ("id", "title", "shelf", "genres")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    # Multi-orphan lead-in (mirrors ``_format_unresolved_targets_error``'s shape).
    assert "FilterSets referenced via filter_input_type(...) but not wired to any DjangoType:" in msg
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
# Materialization & idempotency — Decision 9.
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
            fields = ("id", "title", "shelf", "genres")
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
# Registry clear — Decision 9 lifecycle.
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
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import django; "
                "import os; "
                "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fakeshop.settings'); "
                "import sys; sys.path.insert(0, 'examples/fakeshop'); "
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
    assert result.returncode == 0, f"subprocess failed: stdout={result.stdout!r}, stderr={result.stderr!r}"


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
            fields = ("id", "title", "shelf", "genres")
            filterset_class = BookFilter

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookFilter" in msg
    assert "unresolved" in msg
    assert "UnknownFilter" in msg
    assert isinstance(exc_info.value.__cause__, ImportError)


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
            fields = ("id", "title", "shelf", "genres")
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
