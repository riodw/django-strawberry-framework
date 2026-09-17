"""Live GraphQL HTTP tests for what one operation's extensions may be answered from.

Two claims a package-only schema cannot make, both reached from a resolver
holding ``info.schema`` in a real request and read back off the wire:

- the accepted extension configuration is the one the NEXT request is enforced
  by, whatever a resolver writes at the objects the schema holds it in - so the
  bound a slotted factory declared still bounds, and the masking an accepted
  error policy declared still masks;
- the optimizer entry every deployment is documented to write - one module-level
  singleton behind a factory - keeps its published plan on the request it
  belongs to when a consumer extension runs an operation of its own.

The mechanics of the carrier and of the runner's bindings are pinned in
``tests/test_schema.py`` and ``tests/extensions/test_operation_state.py``. What
this module owns is the consumer-visible outcome, because a resolver reaching
``info.schema`` and a response reaching a client are both things only a request
has.
"""

import asyncio
import json
from types import SimpleNamespace

import pytest
import strawberry
from apps.products.services import seed_data
from asgiref.sync import sync_to_async
from django.test import AsyncClient
from django.urls import include, path
from strawberry.extensions.base_extension import SchemaExtension

from django_strawberry_framework import (
    RESOURCE_LIMIT_ERROR_CODE,
    DjangoOptimizerExtension,
    DjangoSchema,
    ResourcePolicy,
    strawberry_config,
)
from django_strawberry_framework.extensions import (
    DjangoErrorPolicyExtension,
    DjangoResourcePolicyExtension,
)
from django_strawberry_framework.optimizer._context import (
    DST_OPTIMIZER_KEYS,
    DST_OPTIMIZER_PLAN,
    get_context_value,
)
from django_strawberry_framework.resource_policy import (
    DEFAULT_RESOURCE_POLICY,
    policy_from_info,
)
from django_strawberry_framework.schema import SCHEMA_CONFIGURATION_ERROR_CODE
from django_strawberry_framework.testing import TestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView


async def _post_async(client, document):
    """Post one document to the async mount and return the decoded payload."""
    response = await client.post(
        "/iso-survivor/",
        data=json.dumps({"query": document}),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    return json.loads(response.content)


pytestmark = pytest.mark.urls(__name__)

#: The exception message an unmasked error policy would put on the wire.
SENTINEL = "the-resolver-said-this-out-loud"


class _NarrowResourceFactory:
    """The accepted entry: a factory whose layout admits no weak reference.

    ``__slots__`` without ``__weakref__`` is an ordinary way to write a callable
    and Strawberry runs it like any other factory, so the schema holds it in a
    box and answers for it from that box alone.
    """

    __slots__ = ()

    def __call__(self):
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=1))


class _WideResourceFactory:
    """The entry a resolver would rather the next request were bounded by."""

    __slots__ = ()

    def __call__(self):
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=999))


class _SilentErrorPolicy(DjangoErrorPolicyExtension):
    """An error-policy extension that masks nothing, which is the point of it.

    An accepted error entry suppresses the automatic one, so what a replacement
    has to do to unmask a later response is simply be an error policy extension
    that does not mask.
    """

    def on_operation(self):
        """Leave the completed result exactly as the resolvers produced it."""
        yield


class _MaskingErrorFactory:
    """The accepted entry: the masking every later response is owed."""

    __slots__ = ()

    def __call__(self):
        return DjangoErrorPolicyExtension()


class _DisabledErrorFactory:
    """The entry a resolver would rather masked nothing."""

    __slots__ = ()

    def __call__(self):
        return _SilentErrorPolicy()


#: Every way there is to aim at the binding inside the box the schema holds. A
#: Python object's own ``__setattr__`` cannot refuse the last two - the
#: primitive its constructor writes its slot with is one a resolver can call -
#: which is why the box is the interpreter's own binding instead.
TAMPERS = {
    "assign-the-binding": lambda box, replacement: setattr(box, "__self__", replacement),
    "assign-past-the-descriptor": lambda box, replacement: object.__setattr__(
        box,
        "__self__",
        replacement,
    ),
    "write-the-instance-dict": lambda box, replacement: box.__dict__.__setitem__(
        "__self__",
        replacement,
    ),
    "delete-the-binding": lambda box, replacement: delattr(box, "__self__"),
    "rebuild-the-box": lambda box, replacement: box.__init__(replacement),
}


def _swap(
    schema,
    tamper,
    accepted_type,
    replacement,
) -> str:
    """Aim one write at the box holding this schema's accepted entry, and say what happened."""
    box = next(
        (
            held
            for held in schema.__dict__["_django_extensions"]
            if isinstance(getattr(held, "__self__", None), accepted_type)
        ),
        None,
    )
    if box is None:
        return "no box"
    try:
        TAMPERS[tamper](box, replacement)
    except AttributeError:
        return "refused"
    return "ignored"


@strawberry.type
class _ResourceQuery:
    """One scalar to charge aliases against, and the write that would widen them."""

    @strawberry.field
    def hello(self) -> str:
        return "hi"

    @strawberry.field
    def widen(self, info: strawberry.Info, tamper: str) -> str:
        """Try to make the next request resolve a wider resource entry."""
        return _swap(info.schema, tamper, _NarrowResourceFactory, _WideResourceFactory())


@strawberry.type
class _ErrorQuery:
    """One raising field, and the write that would stop its message being masked."""

    @strawberry.field
    def boom(self) -> str:
        raise RuntimeError(SENTINEL)

    @strawberry.field
    def unmask(self, info: strawberry.Info, tamper: str) -> str:
        """Try to make the next request resolve a disabled error entry."""
        return _swap(info.schema, tamper, _MaskingErrorFactory, _DisabledErrorFactory())


class _Nester(SchemaExtension):
    """A consumer extension that runs one operation of its own at teardown.

    Its own operation begins after every optimizer hook of the request's
    operation has returned, and reports what the request's context object
    carried either side of it.
    """

    def __init__(self) -> None:
        self.ran = False
        self.published: list[dict] = []

    def on_operation(self):
        """Run the inner operation once the outer operation's hooks are done."""
        yield
        if self.ran:
            return
        self.ran = True
        context = self.execution_context.context
        self.published.append(_published(context))
        self.execution_context.schema.execute_sync(
            "{ allItems(first: 2) { edges { node { name category { id } } } } }",
            context_value=context,
        )
        self.published.append(_published(context))

    def get_results(self) -> dict:
        """Report the comparison where a client can read it."""
        if len(self.published) != 2:
            return {}
        before, after = self.published
        return {
            "nesting": {
                "changed": sorted(key for key in before if before[key] is not after[key]),
                "planPublished": before["dst_optimizer_plan"] is not None,
            },
        }


def _published(context) -> dict:
    """Every optimizer stash currently readable off a request context object."""
    return {key: get_context_value(context, key) for key in DST_OPTIMIZER_KEYS}


def _resource_schema():
    """The schema mounted behind ``/iso-resource/``, built once per process."""
    return DjangoSchema(
        query=_ResourceQuery,
        resource_policy=ResourcePolicy(max_aliases=99),
        extensions=[_NarrowResourceFactory()],
    )


def _error_schema():
    """The schema mounted behind ``/iso-error/``, built once per process."""
    return DjangoSchema(query=_ErrorQuery, extensions=[_MaskingErrorFactory()])


_HELD: dict[str, object] = {}


def _held(name, build):
    """One schema per mount, held for the life of the process.

    A schema rebuilt per request would answer every tamper with a fresh
    configuration, which is the opposite of what these rows ask: whether a write
    made in one request reaches the NEXT one.
    """
    if name not in _HELD:
        _HELD[name] = build()
    return _HELD[name]


def _view(name, build):
    """Mount the package's synchronous view over one held schema."""

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_held(name, build))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _fresh_view(build):
    """Mount the package's synchronous view over a schema built per request.

    The optimizer row needs the project's own generated types, which the
    acceptance fixtures rebuild per test; what it deliberately keeps across
    requests is the module-level optimizer, which is the shipped spelling.
    """

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=build())
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _nesting_schema():
    """The shipped optimizer spelling, with a consumer extension beside it."""
    from apps.products.schema import Query as ProductsQuery

    from django_strawberry_framework import finalize_django_types

    finalize_django_types()
    return DjangoSchema(
        query=ProductsQuery,
        config=strawberry_config(),
        extensions=[lambda: _OPTIMIZER, lambda: _NESTER],
    )


#: The documented consumer wiring: one module-level optimizer behind a factory,
#: so its plan cache is shared across requests while its state is not.
_OPTIMIZER = DjangoOptimizerExtension()
_NESTER = _Nester()

#: What the worker records between the request that started it and the one that
#: reads it back.
_SURVIVOR: dict = {}

#: The operation the worker runs for itself, on a context of its own.
SURVIVOR_QUERY = "{ allItems(first: 1) { edges { node { name category { name } } } } }"


@strawberry.type
class _SurvivorReport:
    """What a worker that outlived its request saw when it ran work of its own."""

    rows_bound: int
    plan_published: bool


def _ambiguous_schema():
    """Two opaque factories of one kind: a configuration with two answers."""
    return DjangoSchema(
        query=_ResourceQuery,
        extensions=[_NarrowResourceFactory(), _WideResourceFactory()],
    )


def _survivor_schema():
    """The async mount: the project's own types, bounded, with the shipped optimizer."""
    from apps.products.schema import Query as ProductsQuery

    from django_strawberry_framework import finalize_django_types

    @strawberry.type
    class SurvivorQuery(ProductsQuery):
        @strawberry.field
        async def spawn(self, info: strawberry.Info) -> str:
            """Start a worker holding this operation's context, as a resolver may."""
            release = asyncio.Event()
            schema = info.schema
            _SURVIVOR.clear()
            _SURVIVOR["release"] = release

            async def worker() -> None:
                """Read a bound and run a whole operation, after this request ended."""
                await release.wait()
                _SURVIVOR["rows_bound"] = policy_from_info(
                    SimpleNamespace(context={}),
                ).max_list_rows
                context: dict = {}
                result = await schema.execute(SURVIVOR_QUERY, context_value=context)
                _SURVIVOR["errors"] = result.errors
                _SURVIVOR["plan_published"] = (
                    get_context_value(context, DST_OPTIMIZER_PLAN) is not None
                )

            _SURVIVOR["worker"] = asyncio.ensure_future(worker())
            return "spawned"

        @strawberry.field
        async def survivor_report(self) -> _SurvivorReport:
            """Let the worker run now that its request is over, and report what it saw."""
            _SURVIVOR["release"].set()
            await _SURVIVOR["worker"]
            assert _SURVIVOR["errors"] is None, _SURVIVOR["errors"]
            return _SurvivorReport(
                rows_bound=_SURVIVOR["rows_bound"],
                plan_published=_SURVIVOR["plan_published"],
            )

    finalize_django_types()
    return DjangoSchema(
        query=SurvivorQuery,
        config=strawberry_config(),
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[lambda: _OPTIMIZER],
    )


def _async_view(build):
    """Mount the package's asynchronous view over a schema built per request."""

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=build())
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


urlpatterns = [
    path("", include("config.urls")),
    path("iso-resource/", _view("resource", _resource_schema)),
    path("iso-error/", _view("error", _error_schema)),
    path("iso-nesting/", _fresh_view(_nesting_schema)),
    path("iso-chain/", _view("chain", _ambiguous_schema)),
    path("iso-survivor/", _async_view(_survivor_schema)),
]


#: What each write spelling does to the interpreter's own binding. Two of them
#: raise nothing at all - a ``__dict__`` write on a bound method lands on the
#: function it wraps, and a second ``__init__`` is a no-op - which is the point
#: of reading the NEXT request rather than the write's own return value.
TAMPER_OUTCOMES = {
    "assign-the-binding": "refused",
    "assign-past-the-descriptor": "refused",
    "write-the-instance-dict": "ignored",
    "delete-the-binding": "refused",
    "rebuild-the-box": "ignored",
}


@pytest.mark.parametrize("tamper", sorted(TAMPER_OUTCOMES), ids=sorted(TAMPER_OUTCOMES))
def test_a_resolver_cannot_widen_the_next_requests_bound_through_the_accepted_entry(tamper):
    """The bound a slotted factory declared is the bound the NEXT request is held to.

    The schema's own policy would admit both aliases; the accepted entry admits
    one. A resolver that could reach the entry through the object the schema
    holds it in would widen every later request on the process, which is why the
    row reads a SECOND request rather than the one that wrote.

    Parametrized over each write spelling with one node id apiece, because which
    of them the binding survives is the whole claim.
    """
    client = TestClient(path="/iso-resource/")

    wrote = client.query("query($t: String!) { widen(tamper: $t) }", {"t": tamper})
    assert wrote.data["widen"] == TAMPER_OUTCOMES[tamper]

    refused = client.query("{ a: hello b: hello }", assert_no_errors=False)
    assert refused.errors is not None
    assert refused.errors[0]["extensions"]["code"] == RESOURCE_LIMIT_ERROR_CODE
    assert client.query("{ hello }").data == {"hello": "hi"}


@pytest.mark.parametrize("tamper", sorted(TAMPER_OUTCOMES), ids=sorted(TAMPER_OUTCOMES))
def test_a_resolver_cannot_unmask_the_next_requests_errors_through_the_accepted_entry(tamper):
    """Masking is the amplifier: an accepted error entry suppresses the automatic one.

    An entry that resolved to a DISABLED policy would therefore leave the
    operation with no masking at all, and the next unexpected exception would
    reach the client carrying whatever the resolver raised.
    """
    client = TestClient(path="/iso-error/")

    wrote = client.query("query($t: String!) { unmask(tamper: $t) }", {"t": tamper})
    assert wrote.data["unmask"] == TAMPER_OUTCOMES[tamper]

    masked = client.query("{ boom }", assert_no_errors=False)
    assert masked.errors is not None
    assert SENTINEL not in masked.errors[0]["message"]
    assert "correlationId" in masked.errors[0]["extensions"]


@pytest.mark.django_db
def test_an_operation_a_consumer_extension_starts_leaves_the_request_its_optimizer_plan():
    """The shipped singleton, through the project's own types, over a real request.

    The optimizer publishes its plan, elisions and lookup paths on the request's
    context object as introspection for whoever holds that request. A consumer
    extension's own operation runs inside the same request and shares that
    object, so what it must not do is clear it or publish its own values there.
    """
    seed_data(2)
    _NESTER.ran = False
    _NESTER.published.clear()
    client = TestClient(path="/iso-nesting/")

    response = client.query(
        "{ allItems(first: 2) { edges { node { name category { name } } } } }",
    )

    edges = response.data["allItems"]["edges"]
    assert edges, response.data
    assert all(edge["node"]["category"]["name"] for edge in edges)
    nesting = response.extensions["nesting"]
    assert nesting["planPublished"] is True
    assert nesting["changed"] == []


@pytest.mark.parametrize(
    "document",
    ["{ hello }", "{ a: hello b: hello }"],
    ids=["one-alias", "two-aliases"],
)
def test_a_schema_with_two_resource_authorities_refuses_every_request(document):
    """Which of two policies bounds the request cannot be decided by list order.

    Both factories are opaque until they run, so both resolve into the
    operation's chain and each arms its own budget over it - and the last one
    armed is what every bound reads. The document here is the difference between
    them: one alias is inside both bounds, two are inside only the wide one. The
    wire says the same thing for both, because the configuration is what is
    refused rather than the request.
    """
    client = TestClient(path="/iso-chain/")

    refused = client.query(document, assert_no_errors=False)

    assert refused.data is None
    assert refused.errors is not None
    assert refused.errors[0]["extensions"] == {"code": SCHEMA_CONFIGURATION_ERROR_CODE}
    assert "ResourcePolicy" not in refused.errors[0]["message"]
    assert "max_aliases" not in refused.errors[0]["message"]


@pytest.mark.django_db(transaction=True)
async def test_a_worker_that_outlived_a_request_is_bounded_and_published_for_itself():
    """The work a background job does is not the request that happened to start it.

    A resolver's task keeps a copy of the context its request ran in, and no
    token reset reaches that copy. Left readable, the completed request's budget
    answers the bound the job reads for work nobody admitted, and the job's own
    operation counts itself as nested - so the plan, elisions and lookup paths
    it publishes go nowhere, and the context it was handed comes back empty to
    whoever passed it.
    """
    await sync_to_async(seed_data)(2)
    client = AsyncClient()

    spawned = await _post_async(client, "{ spawn }")
    assert spawned["data"] == {"spawn": "spawned"}

    reported = await _post_async(
        client,
        "{ survivorReport { rowsBound planPublished } }",
    )

    assert reported["data"]["survivorReport"] == {
        "rowsBound": DEFAULT_RESOURCE_POLICY.max_list_rows,
        "planPublished": True,
    }
