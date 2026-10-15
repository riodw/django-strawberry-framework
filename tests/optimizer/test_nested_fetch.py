"""Tests for the nested-connection fetch-strategy seam (``optimizer/nested_fetch.py``).

Strategy registry identity, ``ConfigurationError`` at construction, and the
``ContextVar`` active-strategy seam have no HTTP envelope. Routed strategy SQL
is ``examples/fakeshop/test_query/test_optimizer_auto_api.py``.
"""

from collections.abc import Callable
from types import SimpleNamespace
from typing import NoReturn

import pytest
import pytest_django
from apps.library.models import Book, Genre
from django.db.models import Prefetch
from django.db.models.query import ModelIterable
from django.utils.functional import SimpleLazyObject
from typing_extensions import override

from django_strawberry_framework import DjangoOptimizerExtension
from django_strawberry_framework.exceptions import ConfigurationError, OptimizerError
from django_strawberry_framework.optimizer._context import (
    begin_execution_frame,
    end_execution_frame,
)
from django_strawberry_framework.optimizer.hints import OptimizerHint
from django_strawberry_framework.optimizer.lateral_fetch import LATERAL_STRATEGY
from django_strawberry_framework.optimizer.nested_fetch import (
    AUTO_STRATEGY,
    WINDOWED_STRATEGY,
    NestedConnectionRequest,
    WindowedPrefetchStrategy,
    _builtin_strategies,
    active_strategy,
    resolve_strategy,
    unwindowable_child_queryset_reason,
)
from django_strawberry_framework.optimizer.nested_planner import NestedConnectionPlanResult
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
)
from tests.optimizer._builders import nested_connection_request


def _books_request(**overrides: object) -> NestedConnectionRequest:
    """A minimal valid request for the reverse-M2M ``Genre.books`` relation."""
    return nested_connection_request(Genre, "books", **overrides)


def test_nested_plan_result_reports_strategy_acceptance() -> None:
    plan = OptimizationPlan()

    assert NestedConnectionPlanResult(plan=plan).accepted is False
    assert (
        NestedConnectionPlanResult(plan=plan, accepted_response_keys=("books",)).accepted is True
    )


def test_windowed_strategy_attaches_windowed_prefetch() -> None:
    """The default strategy lands the spec-033 shape: windowed qs on the ``to_attr``."""
    plan = OptimizationPlan()
    assert WindowedPrefetchStrategy().plan(_books_request(), plan) is True
    (entry,) = plan.prefetch_related
    assert isinstance(entry, Prefetch)
    assert entry.prefetch_through == "books"
    assert entry.to_attr == "_dst_books_connection"
    assert entry.queryset is not None
    annotations = entry.queryset.query.annotations
    assert WINDOW_ROW_NUMBER in annotations
    assert WINDOW_TOTAL_COUNT in annotations


def test_request_rejects_engaged_probe_with_count() -> None:
    """The strategy seam rejects an engaged-probe request that also wants the count.

    ``NestedConnectionRequest`` is the boundary every strategy consumes, so its
    construction enforces the probe/count mutual-exclusion (the shared
    ``assert_window_fetch_mode_for``): a plain-first-page request (offset 0,
    ``limit`` > 0) with ``next_page_probe=True`` cannot also carry
    ``with_total_count=True``. The walker never emits this pair; a future
    strategy or direct caller that does fails loudly here.
    """
    with pytest.raises(OptimizerError, match="mutually exclusive"):
        _books_request(with_total_count=True, next_page_probe=True)


def test_windowed_strategy_honors_conditional_count() -> None:
    """``with_total_count=False`` flows through the request to the window."""
    plan = OptimizationPlan()
    WindowedPrefetchStrategy().plan(_books_request(with_total_count=False), plan)
    (entry,) = plan.prefetch_related
    assert isinstance(entry, Prefetch)
    assert entry.queryset is not None
    assert WINDOW_TOTAL_COUNT not in entry.queryset.query.annotations


class _ConsumerStrategy:
    """A consumer-authored strategy whose ``plan`` answers one fixed verdict."""

    def __init__(self, name: str, *, verdict: bool) -> None:
        self.name = name
        self._verdict = verdict

    def plan(self, _request: NestedConnectionRequest, _plan: OptimizationPlan) -> bool:
        return self._verdict


def _never_plans(_request: object, _plan: object) -> bool:
    return False


def test_builtin_strategy_registry_is_cached_and_immutable() -> None:
    """The cycle-breaking registry is built once and cannot be mutated."""
    registry = _builtin_strategies()
    assert registry is _builtin_strategies()
    assert sorted(registry) == ["lateral", "windowed"]
    with pytest.raises(TypeError):
        # basedpyright: the registry is a read-only Mapping; the test proves item assignment raises
        # TypeError
        registry["correlated"] = SimpleNamespace(plan=_never_plans)  # pyright: ignore[reportIndexIssue]


def test_resolve_strategy_by_name_auto_and_instance() -> None:
    """Names resolve from the registry; ``"auto"`` stays stable; instances pass through."""
    assert resolve_strategy("windowed") is WINDOWED_STRATEGY
    assert resolve_strategy("auto") is AUTO_STRATEGY
    custom = _ConsumerStrategy(name="custom", verdict=False)
    assert resolve_strategy(custom) is custom


def test_resolve_strategy_rejects_unknown_name_and_bad_type() -> None:
    """Typos fail loud at construction, never at query time."""
    with pytest.raises(
        ConfigurationError,
        match="Unknown nested_connection_strategy 'correlated'",
    ):
        resolve_strategy("correlated")
    with pytest.raises(ConfigurationError, match="plan\\(request, plan\\) method"):
        resolve_strategy(42)


def test_resolve_strategy_rejects_hostile_type_and_class_name() -> None:
    """Hostile types fail safely with ConfigurationError and classes report their name."""

    class HostileType(type):
        @property
        @override
        # basedpyright: the hostile shape under test, a ``__name__`` property whose read raises;
        # the checker rejects any property overriding a base class attribute
        def __name__(cls) -> NoReturn:  # pyright: ignore[reportIncompatibleVariableOverride]
            raise RuntimeError("type name should never run")

    class NotStrategy(metaclass=HostileType):
        pass

    with pytest.raises(ConfigurationError, match="nested_connection_strategy"):
        resolve_strategy(NotStrategy())

    with pytest.raises(ConfigurationError, match="WindowedPrefetchStrategy"):
        resolve_strategy(WindowedPrefetchStrategy)


def test_resolve_strategy_hostile_str_dunders_stay_typed() -> None:
    """A consumer-supplied str subclass cannot replace the typed rejection.

    Deciding never dispatches into the selection's dunders: the ``"auto"`` check
    and the registry match compare content through the base ``str`` slot, so no
    ``__eq__`` or ``__hash__`` runs. Rendering the unknown-name message reads
    ``__repr__`` through a guard. A hostile override therefore degrades to the
    typed ``ConfigurationError`` instead of an arbitrary exception.
    """

    class HostileEq(str):
        @override
        def __eq__(self, other: object) -> NoReturn:
            raise RuntimeError("hostile eq")

        @override
        def __hash__(self) -> int:
            return str.__hash__(self)

    # A hostile ``__eq__`` cannot force a false AUTO_STRATEGY match either:
    # the comparison reads through the base ``str`` slot, so content decides.
    assert resolve_strategy(HostileEq("auto")) is AUTO_STRATEGY
    with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
        resolve_strategy(HostileEq("correlated"))

    class HostileHash(str):
        @override
        def __hash__(self) -> NoReturn:
            raise RuntimeError("hostile hash")

    with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
        resolve_strategy(HostileHash("correlated"))

    class HostileRepr(str):
        @override
        def __repr__(self) -> str:
            raise RuntimeError("hostile repr")

    with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
        resolve_strategy(HostileRepr("correlated"))


def test_resolve_strategy_raising_plan_attribute_is_not_a_strategy() -> None:
    """A raising ``plan`` attribute reads as "not a strategy", never escapes.

    ``getattr(value, "plan", None)`` only absorbs ``AttributeError``; an
    attribute read that raises anything else is guarded to the same typed
    rejection a non-strategy object receives.
    """

    class RaisingPlan:
        @property
        def plan(self) -> NoReturn:
            raise RuntimeError("hostile plan read")

    with pytest.raises(ConfigurationError, match="must be a strategy name"):
        resolve_strategy(RaisingPlan())


_NOT_A_STRATEGY = (
    "nested_connection_strategy must be a strategy name, 'auto', or an object with a "
    "plan(request, plan) method; got {}."
)


def _raising_class_value(raised: type[BaseException]) -> object:
    """A value whose ``__class__`` read raises ``raised`` (so a bare ``isinstance`` raises)."""

    class RaisingClass:
        @property
        @override
        # basedpyright: deliberately a read-only ``__class__`` that raises: the hostile object
        # is the guard's input
        def __class__(self) -> NoReturn:  # pyright: ignore[reportIncompatibleMethodOverride]
            raise raised("hostile __class__")

    return RaisingClass()


class _ClaimsStr:
    """A non-``str`` value whose ``__class__`` claims ``str``."""

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__``: the forged type is the guard's input
    def __class__(self) -> type[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return str


@pytest.mark.parametrize(
    ("make", "type_name"),
    [
        (lambda: _raising_class_value(RuntimeError), "RaisingClass"),
        (lambda: _raising_class_value(TypeError), "RaisingClass"),
        (lambda: _raising_class_value(KeyboardInterrupt), "RaisingClass"),
        (_ClaimsStr, "_ClaimsStr"),
        (lambda: SimpleLazyObject(lambda: "windowed"), "SimpleLazyObject"),
    ],
    ids=[
        "class-read-raises-runtime-error",
        "class-read-raises-type-error",
        "class-read-raises-base-exception",
        "class-claims-str",
        "lazy-str",
    ],
)
def test_resolve_strategy_non_str_lookalikes_stay_typed(
    make: Callable[[], object],
    type_name: str,
) -> None:
    """Whether a selection is a name is asked of its real type, never its ``__class__``.

    A ``__class__`` that raises, or that claims ``str`` for a value the base ``str``
    slot then refuses, and a lazy proxy of a name are all not ``str``; none carries
    a ``plan``, so each takes the typed rejection.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        resolve_strategy(make())
    assert str(exc_info.value) == _NOT_A_STRATEGY.format(type_name)


@pytest.mark.parametrize(
    "claimed_class",
    [type, None],
    ids=["class-claims-type", "class-read-raises"],
)
def test_resolve_strategy_class_test_reads_the_real_type(claimed_class: type | None) -> None:
    """An instance with a callable ``plan`` is a strategy whatever its ``__class__`` claims.

    The class test (a class carries ``plan`` as a plain function, not a bound
    method) asks the real type, so neither a ``__class__`` claiming ``type`` nor
    one that raises decides it.
    """

    class ClassLiarStrategy:
        name = "class-liar"

        @property
        @override
        # basedpyright: deliberately a read-only ``__class__``: the forged type is the guard's input
        def __class__(self) -> type:  # pyright: ignore[reportIncompatibleMethodOverride]
            if claimed_class is None:
                raise RuntimeError("hostile __class__")
            return claimed_class

        def plan(self, _request: NestedConnectionRequest, _plan: OptimizationPlan) -> bool:
            return False

    strategy = ClassLiarStrategy()
    assert resolve_strategy(strategy) is strategy


def test_resolve_strategy_lateral_loads_the_lateral_backend() -> None:
    """``"lateral"`` lazily registers and returns the Postgres backend singleton."""
    assert resolve_strategy("lateral") is LATERAL_STRATEGY
    assert resolve_strategy("lateral") is LATERAL_STRATEGY  # registry, not re-import


def test_resolve_strategy_none_reads_setting(settings: pytest_django.Settings) -> None:
    """``None`` defers to ``DJANGO_STRAWBERRY_FRAMEWORK["NESTED_CONNECTION_STRATEGY"]``."""
    assert resolve_strategy(None) is WINDOWED_STRATEGY  # key absent -> default
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"NESTED_CONNECTION_STRATEGY": "windowed"}
    assert resolve_strategy(None) is WINDOWED_STRATEGY
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"NESTED_CONNECTION_STRATEGY": "auto"}
    assert resolve_strategy(None) is AUTO_STRATEGY
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"NESTED_CONNECTION_STRATEGY": "nope"}
    with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy 'nope'"):
        resolve_strategy(None)


def _construct_optimizer() -> object:
    """Build the optimizer with defaults, so construction reads the settings."""
    return DjangoOptimizerExtension()


@pytest.mark.parametrize(
    "resolve",
    [lambda: resolve_strategy(None), _construct_optimizer],
    ids=["resolve-strategy-none", "extension-construction"],
)
@pytest.mark.parametrize(
    ("make", "type_name"),
    [
        (lambda: _raising_class_value(RuntimeError), "RaisingClass"),
        (_ClaimsStr, "_ClaimsStr"),
        (lambda: SimpleLazyObject(lambda: "windowed"), "SimpleLazyObject"),
    ],
    ids=["class-read-raises", "class-claims-str", "lazy-str"],
)
def test_strategy_setting_non_str_lookalikes_stay_typed(
    settings: pytest_django.Settings,
    resolve: Callable[[], object],
    make: Callable[[], object],
    type_name: str,
) -> None:
    """A configured setting that is not really a ``str`` takes the typed rejection.

    ``NESTED_CONNECTION_STRATEGY`` is read when the selection is ``None`` and
    validated by ``resolve_strategy``, so both the direct call and extension
    construction reject the value with ``ConfigurationError``.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"NESTED_CONNECTION_STRATEGY": make()}
    with pytest.raises(ConfigurationError) as exc_info:
        _ = resolve()
    assert str(exc_info.value) == _NOT_A_STRATEGY.format(type_name)


def test_extension_pins_strategy_at_construction() -> None:
    """The kwarg resolves eagerly; the instance carries its strategy."""
    extension = DjangoOptimizerExtension()
    assert extension.nested_connection_strategy is WINDOWED_STRATEGY
    assert (
        DjangoOptimizerExtension(nested_connection_strategy="auto").nested_connection_strategy
        is AUTO_STRATEGY
    )
    custom = _ConsumerStrategy(name="custom", verdict=False)
    assert (
        DjangoOptimizerExtension(nested_connection_strategy=custom).nested_connection_strategy
        is custom
    )
    with pytest.raises(ConfigurationError):
        DjangoOptimizerExtension(nested_connection_strategy="correlated")


def test_optimizer_hint_strategy_accepts_and_drives_a_consumer_instance() -> None:
    """``OptimizerHint.strategy(instance)`` takes a consumer-authored backend.

    The per-field seam accepts the same ``str | NestedConnectionStrategy`` the
    extension-wide kwarg does: an instance survives ``__post_init__`` validation
    verbatim (no str coercion), the stored selection dispatches back to the same
    object through ``resolve_strategy``, and driving it plans one request through
    the consumer's own ``plan()``.
    """
    planned: list[object] = []

    class RecordingStrategy:
        name = "recording"

        def plan(self, request: NestedConnectionRequest, _plan: OptimizationPlan) -> bool:
            planned.append(request)
            return True

    backend = RecordingStrategy()
    hint = OptimizerHint.strategy(backend)
    # Validated at construction and carried as the instance itself.
    assert hint.nested_strategy is backend
    # The stored selection resolves back to the same consumer backend...
    assert resolve_strategy(hint.nested_strategy) is backend
    # ...and driving it plans the request through the consumer's plan().
    plan = OptimizationPlan()
    request = _books_request()
    assert resolve_strategy(hint.nested_strategy).plan(request, plan) is True
    assert planned == [request]


def test_active_strategy_defaults_windowed_and_reads_the_execution_frame() -> None:
    """Direct ``plan_optimizations`` callers get windowed; executions get the published one."""
    assert active_strategy() is WINDOWED_STRATEGY
    custom = _ConsumerStrategy(name="custom", verdict=True)
    frame = begin_execution_frame({}, nested=False, strategy=custom)
    try:
        assert active_strategy() is custom
    finally:
        end_execution_frame(frame)
    assert active_strategy() is WINDOWED_STRATEGY


def test_active_strategy_preserves_falsey_consumer_strategy() -> None:
    """A valid strategy whose truth value is false must remain active."""

    class FalseyStrategy:
        name = "falsey"

        def __bool__(self) -> bool:
            return False

        def plan(self, _request: NestedConnectionRequest, _plan: OptimizationPlan) -> bool:
            return True

    custom = FalseyStrategy()
    frame = begin_execution_frame({}, nested=False, strategy=custom)
    try:
        assert active_strategy() is custom
    finally:
        end_execution_frame(frame)


def test_on_execute_publishes_instance_strategy() -> None:
    """``on_execute`` publishes the instance's strategy for the walker's lifetime."""
    custom = _ConsumerStrategy(name="custom", verdict=True)
    extension = DjangoOptimizerExtension(nested_connection_strategy=custom)
    hook = extension.on_execute()
    next(hook)  # enter the execution window
    try:
        assert active_strategy() is custom
    finally:
        with pytest.raises(StopIteration):
            next(hook)  # exit; the finally block resets the ContextVar
    assert active_strategy() is WINDOWED_STRATEGY


def test_unwindowable_child_queryset_reason_matrix() -> None:
    """The strategy-independent safety classifier.

    Each unsafe consumer-hook shape maps to a stable reason; a plain
    queryset (with or without projection/ordering) maps to ``None``.
    """
    assert unwindowable_child_queryset_reason(Book.objects.all()[:10]) == "sliced"
    assert (
        unwindowable_child_queryset_reason(Book.objects.select_for_update()) == "select_for_update"
    )
    assert (
        unwindowable_child_queryset_reason(
            Book.objects.filter(pk=1).union(Book.objects.filter(pk=2)),
        )
        == "combined"
    )
    assert unwindowable_child_queryset_reason(Book.objects.distinct()) == "distinct"
    assert unwindowable_child_queryset_reason(Book.objects.values_list("id")) == "values"
    assert unwindowable_child_queryset_reason(Book.objects.values("id")) == "values"

    # A custom ModelIterable subclass still yields model instances and is windowable.
    class CustomModelIterable(ModelIterable[Book]):
        pass

    custom_qs = Book.objects.all()
    custom_qs._iterable_class = CustomModelIterable
    assert unwindowable_child_queryset_reason(custom_qs) is None

    # A non-type or invalid iterable class is rejected as values.
    invalid_qs = Book.objects.all()
    # basedpyright: the planted non-type iterable class is the hostile input under test;
    # django-stubs types the slot as one of Django's BaseIterable classes
    invalid_qs._iterable_class = "invalid"  # pyright: ignore[reportAttributeAccessIssue]
    assert unwindowable_child_queryset_reason(invalid_qs) == "values"

    assert unwindowable_child_queryset_reason(Book.objects.only("id", "title")) is None
    assert unwindowable_child_queryset_reason(Book.objects.order_by("title")) is None
