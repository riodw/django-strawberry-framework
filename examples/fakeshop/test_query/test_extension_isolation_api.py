"""Live GraphQL HTTP tests for what one operation's extensions may be answered from.

Two claims a package-only schema cannot make, both reached from a resolver
holding ``info.schema`` in a real request and read back off the wire:

- what enforces the NEXT request is the schema's own configuration, and nothing
  a resolver can reach through ``info.schema`` - not the accepted entries, not
  the objects the schema holds them in, and not the state a stateful factory
  answers from - so the bound still bounds and the masking still masks;
- a schema whose entries resolve into a second enforcement authority refuses
  every request on the wire, including the ones that would not have parsed and
  the ones asking for an operation name no document can carry, and still bounds
  the document it is refusing;
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
from django.test import AsyncClient, Client
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


async def _post_async(client, document, mount="/iso-survivor/", **body):
    """Post one document to an async mount and return the decoded payload."""
    response = await client.post(
        mount,
        data=json.dumps({"query": document, **body}),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    return json.loads(response.content)


def _post_sync(client, document, mount, **body):
    """Post one document to a sync mount and return ``(response, decoded payload)``."""
    response = client.post(
        mount,
        data=json.dumps({"query": document, **body}),
        content_type="application/json",
    )
    return response, response.content


pytestmark = pytest.mark.urls(__name__)

#: The exception message an unmasked error policy would put on the wire.
SENTINEL = "the-resolver-said-this-out-loud"


class _ConsumerExtension(SchemaExtension):
    """An ordinary consumer extension: the thing an entry is still allowed to be."""


class _MutableConsumerFactory:
    """A stateful accepted factory, whose returned object is chosen after acceptance.

    The shape the attack needs: a resolver reaches this through
    ``info.schema.extensions`` and writes it, so if an entry decided enforcement
    the ceiling for every later request would be a resolver's to choose.
    """

    def __init__(self):
        self.widened = False

    def __call__(self):
        return _ConsumerExtension()


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


class _AcceptedConsumerFactory:
    """The accepted entry, in the layout that takes no weak reference."""

    __slots__ = ()

    def __call__(self):
        return _ConsumerExtension()


class _ReplacementConsumerFactory:
    """The entry a resolver would rather the schema resolved, in the same layout."""

    __slots__ = ()

    def __call__(self):
        return _ConsumerExtension()


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
class _Nested:
    """One level of nesting, so a depth bound has something to charge."""

    @strawberry.field
    def hello(self) -> str:
        return "hi"


@strawberry.type
class _ResourceQuery:
    """One scalar to charge aliases against, and every write that would widen them."""

    @strawberry.field
    def hello(self) -> str:
        return "hi"

    @strawberry.field
    def nested(self) -> _Nested:
        return _Nested()

    @strawberry.field
    def widen(self, info: strawberry.Info, tamper: str) -> str:
        """Try to make the next request resolve a wider configuration."""
        for entry in info.schema.extensions:
            if isinstance(entry, _MutableConsumerFactory):
                entry.widened = True
        return _swap(info.schema, tamper, _AcceptedConsumerFactory, _ReplacementConsumerFactory())


@strawberry.type
class _ErrorQuery:
    """One raising field, and every write that would stop its message being masked."""

    @strawberry.field
    def boom(self) -> str:
        raise RuntimeError(SENTINEL)

    @strawberry.field
    def unmask(self, info: strawberry.Info, tamper: str) -> str:
        """Try to make the next request resolve a configuration that masks nothing."""
        for entry in info.schema.extensions:
            if isinstance(entry, _MutableConsumerFactory):
                entry.widened = True
        return _swap(info.schema, tamper, _AcceptedConsumerFactory, _ReplacementConsumerFactory())


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
    """The schema mounted behind the resource mounts, built once per process."""
    return DjangoSchema(
        query=_ResourceQuery,
        resource_policy=ResourcePolicy(max_aliases=1),
        extensions=[_AcceptedConsumerFactory(), _MutableConsumerFactory()],
    )


def _error_schema():
    """The schema mounted behind the error mounts, built once per process."""
    return DjangoSchema(
        query=_ErrorQuery,
        extensions=[_AcceptedConsumerFactory(), _MutableConsumerFactory()],
    )


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
    """An opaque factory resolving to an enforcement authority the schema owns.

    Bounded narrowly on purpose: the refusal chain keeps the package's own
    resource extension, so what a refused schema does to an oversized or deeply
    nested document is part of what this mount answers.
    """
    return DjangoSchema(
        query=_ResourceQuery,
        resource_policy=ResourcePolicy(max_document_tokens=10, max_depth=1),
        extensions=[_NarrowResourceFactory()],
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


def _held_async_view(name, build):
    """Mount the asynchronous view over one held schema."""

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_held(name, build))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


urlpatterns = [
    path("", include("config.urls")),
    path("iso-resource/", _view("resource", _resource_schema)),
    path("iso-resource-async/", _held_async_view("resource", _resource_schema)),
    path("iso-error/", _view("error", _error_schema)),
    path("iso-error-async/", _held_async_view("error", _error_schema)),
    path("iso-nesting/", _fresh_view(_nesting_schema)),
    path("iso-chain/", _view("chain", _ambiguous_schema)),
    path("iso-chain-async/", _held_async_view("chain", _ambiguous_schema)),
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
    """The bound the SCHEMA was configured with is the bound the next request is held to.

    The resolver does everything a resolver can do to the configuration it can
    reach: it writes the accepted stateful factory's own state and it aims one
    write at the box holding the accepted slotted entry. The next request is
    bounded exactly as the deployment configured it, because what enforces it is
    the schema's record and not an object in that graph.

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


@pytest.mark.django_db(transaction=True)
async def test_a_resolver_cannot_widen_the_next_requests_bound_on_the_async_view():
    """The same claim over the asynchronous view, which is a different request path."""
    client = AsyncClient()

    wrote = await _post_async(
        client,
        '{ widen(tamper: "assign-the-binding") }',
        mount="/iso-resource-async/",
    )
    assert wrote["data"] == {"widen": "refused"}

    refused = await _post_async(client, "{ a: hello b: hello }", mount="/iso-resource-async/")
    assert refused["data"] is None
    assert refused["errors"][0]["extensions"]["code"] == RESOURCE_LIMIT_ERROR_CODE


@pytest.mark.parametrize("tamper", sorted(TAMPER_OUTCOMES), ids=sorted(TAMPER_OUTCOMES))
def test_a_resolver_cannot_unmask_the_next_requests_errors_through_the_accepted_entry(tamper):
    """Masking is the amplifier: an unmasked response carries whatever was raised.

    The masking extension is built per operation from the schema's own error
    policy, so no entry a resolver can reach decides whether the next unexpected
    exception reaches the client with its own message on it.
    """
    client = TestClient(path="/iso-error/")

    wrote = client.query("query($t: String!) { unmask(tamper: $t) }", {"t": tamper})
    assert wrote.data["unmask"] == TAMPER_OUTCOMES[tamper]

    masked = client.query("{ boom }", assert_no_errors=False)
    assert masked.errors is not None
    assert SENTINEL not in masked.errors[0]["message"]
    assert "correlationId" in masked.errors[0]["extensions"]


@pytest.mark.django_db(transaction=True)
async def test_a_resolver_cannot_unmask_the_next_requests_errors_on_the_async_view():
    """The same claim over the asynchronous view."""
    client = AsyncClient()

    wrote = await _post_async(
        client,
        '{ unmask(tamper: "assign-the-binding") }',
        mount="/iso-error-async/",
    )
    assert wrote["data"] == {"unmask": "refused"}

    masked = await _post_async(client, "{ boom }", mount="/iso-error-async/")
    assert SENTINEL not in masked["errors"][0]["message"]
    assert "correlationId" in masked["errors"][0]["extensions"]


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
    ["{ hello }", "{ a: hello }", "{"],
    ids=["valid", "aliased", "malformed"],
)
def test_a_schema_whose_factory_claims_an_authority_refuses_every_request(document):
    """A factory cannot be an enforcement authority, and the wire says so identically.

    The factory is opaque until it runs, so what it produces is typed at
    resolution - and an extension of an enforcement kind is a second authority
    whichever object made it. The malformed row is the one that says "every"
    literally: the refusal is published before the parse stage, so a document
    that would not have parsed is answered with the same stable code.
    """
    client = TestClient(path="/iso-chain/")

    refused = client.query(document, assert_no_errors=False)

    assert refused.data is None
    assert refused.errors is not None
    assert refused.errors[0]["extensions"] == {"code": SCHEMA_CONFIGURATION_ERROR_CODE}
    assert "ResourcePolicy" not in refused.errors[0]["message"]
    assert "max_aliases" not in refused.errors[0]["message"]


@pytest.mark.parametrize(
    "document",
    ["{ a: hello b: hello c: hello }", "{ nested { hello } }"],
    ids=["over-token-budget", "over-depth-budget"],
)
def test_a_refused_schema_still_bounds_the_document_it_refuses(document):
    """A broken configuration is not the one shape with no parsing ceiling.

    The refusal chain keeps the package's own resource extension, reading the
    schema's private policy, so the pre-parse token and depth scan still runs.
    Without it one bad factory would turn "every operation fails closed" into an
    endpoint that lexes and nests whatever it is sent before saying no.
    """
    client = TestClient(path="/iso-chain/")

    rejected = client.query(document, assert_no_errors=False)

    assert rejected.data is None
    assert rejected.errors[0]["extensions"]["code"] == RESOURCE_LIMIT_ERROR_CODE


#: Every ``operationName`` a client can put in a request body, including the
#: ones no document can carry. A refused schema discarded the document the name
#: was written against, so the name selects nothing and every one of these has
#: to come back in the same envelope.
_REFUSED_OPERATION_NAMES = {
    "empty": "",
    "invalid-punctuation": "bad-name",
    "unicode": "\N{FIRE}",
    "valid-but-absent": "Absent",
}

_REFUSED_NAME_IDS = sorted(_REFUSED_OPERATION_NAMES)


def _assert_refused_envelope(response, body):
    """One JSON envelope carrying the configuration code, and nothing about the request."""
    assert response.status_code == 200, body
    assert response.headers["Content-Type"].startswith("application/json"), response.headers
    payload = json.loads(body)
    assert payload["data"] is None, payload
    assert [error["extensions"] for error in payload["errors"]] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]
    return payload


@pytest.mark.parametrize("name", _REFUSED_NAME_IDS, ids=_REFUSED_NAME_IDS)
def test_a_refused_schema_answers_every_operation_name_the_same_way(name):
    """A name no document can carry is refused like every other request.

    Upstream selects the operation to run by looking the requested name up in
    whatever document the parse stage left behind, and a refused request's
    document is the package's own - so a name still belonging to the request is
    a lookup that cannot succeed, raised over a refusal already published. What
    a client saw instead was a plain-text 400 quoting its own operation name
    back at it, from the one configuration that is supposed to answer
    everything the same way.
    """
    requested = _REFUSED_OPERATION_NAMES[name]

    response, body = _post_sync(Client(), "{ hello }", "/iso-chain/", operationName=requested)

    payload = _assert_refused_envelope(response, body)
    assert "Unknown operation" not in json.dumps(payload), payload


@pytest.mark.parametrize("name", _REFUSED_NAME_IDS, ids=_REFUSED_NAME_IDS)
def test_a_refused_schema_still_bounds_a_document_sent_under_any_operation_name(name):
    """The ceiling is charged before the name is looked at, and still outranks the refusal.

    Normalizing the selector must not move the pre-parse scan: an oversized
    document is rejected on its size whatever the request called the operation
    it wanted.
    """
    requested = _REFUSED_OPERATION_NAMES[name]

    response, body = _post_sync(
        Client(),
        "{ a: hello b: hello c: hello }",
        "/iso-chain/",
        operationName=requested,
    )

    assert response.status_code == 200, body
    payload = json.loads(body)
    assert payload["errors"][0]["extensions"]["code"] == RESOURCE_LIMIT_ERROR_CODE


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("name", _REFUSED_NAME_IDS, ids=_REFUSED_NAME_IDS)
async def test_a_refused_schema_answers_every_operation_name_asynchronously_too(name):
    """The asynchronous view answers hostile request metadata identically.

    Sync and async are separate code paths through the same schema, and the
    escaped lookup raised out of both - so parity here is the claim, not a
    restatement of the row above.
    """
    requested = _REFUSED_OPERATION_NAMES[name]

    payload = await _post_async(
        AsyncClient(),
        "{ hello }",
        mount="/iso-chain-async/",
        operationName=requested,
    )

    assert payload["data"] is None, payload
    assert [error["extensions"] for error in payload["errors"]] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@pytest.mark.django_db(transaction=True)
async def test_a_refused_schema_answers_the_async_view_the_same_way():
    """The refusal and its ceiling are the same over the asynchronous view."""
    client = AsyncClient()

    refused = await _post_async(client, "{ hello }", mount="/iso-chain-async/")
    assert refused["data"] is None
    assert refused["errors"][0]["extensions"] == {"code": SCHEMA_CONFIGURATION_ERROR_CODE}

    rejected = await _post_async(
        client,
        "{ a: hello b: hello c: hello }",
        mount="/iso-chain-async/",
    )
    assert rejected["errors"][0]["extensions"]["code"] == RESOURCE_LIMIT_ERROR_CODE


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
