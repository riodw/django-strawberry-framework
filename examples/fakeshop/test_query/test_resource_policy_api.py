"""Live ``/graphql/`` execution-resource-policy acceptance tests (spec-047).

Every bound in ``ResourcePolicy`` is a promise about what a real request over the
wire can spend, so the boundaries are pinned where a real request can reach them:
against mounts of the package's own Django GraphQL view, over
``django.test.Client``, with the rejection read out of the JSON envelope.

The scaffolding is one cached schema factory. Each mount narrows ONE family of
bounds and leaves every other bound at its package default, so a row that
rejects can only have rejected on the bound it is about - a single
tightened-everything schema would let a token bound silently absorb a row
written about node ids. The factory is cached per policy so a worker builds each
probe schema once.

Row groups, in the order a request meets them:

- the document text bounds (tokens, structural depth) - charged before the parse;
- the expanded-document bounds (selections, aliases, collection cost) - charged
  before validation, with fragment / alias / directive evasion rows, and the
  named-operation filter (post-parse bounds charge only the operation
  ``operationName`` selects; the token bound on the same two-operation
  document is the request-level counterpart);
- the value bounds (node ids, membership items, relation ids, nested rows,
  container width, value depth, input nodes, scalar bytes, uploads) - charged
  over a TINY document carrying a LARGE variable payload, which is the shape
  document limits cannot see, including the two shapes only a real request
  builds: one variable spliced into two fields (the same Python object twice)
  and a nested value whose depth no bracket in the document reflects;
- the raw-pk relation id sets - the write inputs whose relation ids render as
  raw pks rather than ``GlobalID``s (``[Int!]`` on the wire), charged against
  the relation bounds through their bind specs rather than the id scalar's
  name, with the GlobalID twins and the aggregate kept honest beside them;
- introspection, charged like any other document shape rather than exempted;
- the collection bounds the fields enforce (raw-list rows, connection page size,
  and the list sibling that used to bypass the connection cap), together with
  what a bounded many-side relation COSTS when its rows arrive already fetched:
  the fakeshop ``Loan`` model's no-op ``LoanQuerySet.as_manager()`` declaration
  is rebuilt at that seam and, under a prefetching plan, must answer its payload
  in the absolute two-query budget (one parent query plus one prefetch);
- the cooperative deadline, one row per seam that hands work to the database;
- the enforcement authority a resolver can reach through ``info.schema``, proven
  across two requests because the write and the request it would widen are
  different requests, together with the two things that authority is identified
  and taken by - the schema's own identity and a private copy of the policy the
  deployment supplied - and the ``max_list_rows`` an extension ENTRY declared,
  which the schema reads once and bounds the request with while the entry itself
  never reaches the chain, alongside the boundary the value budget sits on -
  the raw argument the request carried, charged before a custom scalar converts
  it, whichever of the three places a request can carry one it came from - and
  the largest configurable bound executing as a real ``LIMIT``; and
- the cross-cutting proofs: zero ORM work after a rejection, and one typed error
  code shared by the sync and async transports.

``examples/fakeshop/tests`` and ``tests/test_resource_policy.py`` hold what a
live request cannot reach: policy construction and validation, the
settings/constructor precedence ladder, the narrowing rule, and the walker's
degenerate inputs.
"""

from __future__ import annotations

import json
import threading
import warnings
from contextlib import contextmanager
from functools import cache
from typing import NewType

import pytest
import strawberry
from apps.library import models as library_models
from apps.library import schema as library_schema
from apps.products.services import create_users, seed_data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.models import QuerySet
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import include, path
from graphql_client import graphql_payload
from strawberry.extensions import ValidationCache
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.validation_cache import _get_validate_cache

from django_strawberry_framework import (
    DEFAULT_ERROR_POLICY,
    RESOURCE_LIMIT_ERROR_CODE,
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    ErrorPolicy,
    strawberry_config,
)
from django_strawberry_framework.extensions.resource_policy import (
    DjangoResourcePolicyExtension,
)
from django_strawberry_framework.resource_policy import (
    MAX_RESOURCE_BOUND,
    ResourcePolicy,
    bounded_rows,
)
from django_strawberry_framework.testing import AsyncTestClient, TestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.urls(__name__)


#: Settings that open the spec-048 error policy's pass-through gate for ONE live
#: request. ``settings.DEBUG`` is the gate, and on this tier it is the only
#: reachable instrument - the project schema is constructed by the app, not by the
#: test. Fakeshop's shipped settings also wire django-debug-toolbar behind
#: ``DEBUG``, so the toolbar middleware is dropped for the duration: left in, it
#: would try to inject a panel referencing the ``djdt`` routes that ``config.urls``
#: computed under the ambient ``DEBUG=False`` and fail the request for a reason
#: that has nothing to do with the row. Dropping the middleware is the deterministic
#: form of that - the toolbar's own show-gate is memoized per process, so overriding
#: its callback would not reliably take effect.
_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}


@cache
def _probe_schema(overrides: tuple[tuple[str, int], ...]) -> DjangoSchema:
    """Build (once per worker) a schema over fakeshop's types with a narrowed policy.

    The optimizer is deliberately NOT installed on these probe schemas: the
    subject is the budget, and leaving the optimizer out keeps the query counts a
    rejection row asserts about attributable to the rejection alone.
    """
    from config.schema import Mutation, Query

    return DjangoSchema(
        query=Query,
        mutation=Mutation,
        config=strawberry_config(),
        resource_policy=dict(overrides),
    )


def _probe_view(**overrides: float):
    """Mount the package view over a probe schema narrowing exactly ``overrides``."""
    frozen = tuple(sorted(overrides.items()))

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_probe_schema(frozen))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _probe_upload_view(**overrides: int):
    """The upload twin: same probe schema, with upstream's multipart handling on."""
    frozen = tuple(sorted(overrides.items()))

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(
            schema=_probe_schema(frozen),
            multipart_uploads_enabled=True,
        )
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _probe_async_view(**overrides: int):
    """The async twin of ``_probe_view``, so parity is proven on a real event loop."""
    frozen = tuple(sorted(overrides.items()))

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_probe_schema(frozen))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


#: The bound the hostile-relation mounts narrow to. One row makes the ceiling and
#: the seeded relation impossible to confuse: every assertion below is "one, not
#: four", never "fewer than seeded".
HOSTILE_RELATION_ROWS = 1


class _EscapingQuerySet(QuerySet):
    """A ``QuerySet`` subclass whose slice answers with every row it was asked to drop.

    The raw-list ceiling is ``result[:limit]``, and on a subclass that expression
    is consumer code. A project's manager is free to return one of these - Django
    itself builds relation managers over whatever queryset class the model
    declares - so this is a shape the bound meets in ordinary code, not only in
    an attack.
    """

    def __getitem__(self, key):
        return list(library_models.Loan.objects.all())


@contextmanager
def _hostile_relation_manager():
    """Make the reverse ``loans`` manager hand back the escaping subclass.

    The relation resolver builds its source with ``getattr(root, accessor).all()``
    on Django's own related manager, so replacing that one method is how a real
    project's custom queryset class reaches the raw-list bound - no framework
    seam is bypassed and no test double stands in for the resolver.
    """
    manager_cls = library_models.Patron.loans.related_manager_cls
    original = manager_cls.all

    def escaping_all(self):
        source = original(self)
        hostile = _EscapingQuerySet(model=library_models.Loan, query=source.query)
        hostile._db = source._db
        return hostile

    manager_cls.all = escaping_all
    try:
        yield
    finally:
        manager_cls.all = original


@cache
def _hostile_relation_schema(patron_type: type) -> DjangoSchema:
    """A ``DjangoListField`` schema over a type whose many-side target seals nothing.

    ``PatronType`` and ``LoanType`` both leave ``get_queryset`` at the default, so
    the generated ``loans`` resolver takes the no-custom-visibility branch - the
    one path to the raw-list bound that no visibility rebuild stands in front of.
    No shipped root pairs a ``DjangoListField`` with such a target, so the root
    is declared here rather than borrowed.

    The type is an ARGUMENT, and the cache is keyed on it, because these suites
    reload every app schema module per module: a root captured at import time
    would hold the generation before that reload and mix two type graphs into
    one schema.
    """

    # Built with ``type(...)`` and a REAL annotation object: this module runs
    # under ``from __future__ import annotations``, so a written annotation would
    # be the string ``"list[patron_type]"`` and would resolve against the module
    # globals, where the local type argument does not exist.
    query_cls = strawberry.type(
        type(
            "_HostileRelationQuery",
            (),
            {
                "__annotations__": {"patrons": list[patron_type]},
                "__doc__": "A raw-list root over a type whose many-side target seals nothing.",
                "patrons": DjangoListField(patron_type),
            },
        ),
    )
    return DjangoSchema(
        query=query_cls,
        config=strawberry_config(),
        resource_policy=ResourcePolicy(max_list_rows=HOSTILE_RELATION_ROWS),
    )


def _hostile_relation_view(request, *args, **kwargs):
    """Mount the package view over the hostile-relation probe schema."""
    schema = _hostile_relation_schema(library_schema.PatronType)
    return DjangoGraphQLView.as_view(schema=schema)(request, *args, **kwargs)


_hostile_relation_view.csrf_exempt = True


async def _hostile_relation_async_view(request, *args, **kwargs):
    """The async twin, so the bound is proven on a real event loop too."""
    schema = _hostile_relation_schema(library_schema.PatronType)
    built = AsyncDjangoGraphQLView.as_view(schema=schema)
    return await built(request, *args, **kwargs)


_hostile_relation_async_view.csrf_exempt = True


#: The bound the carry mounts narrow to. Wide enough that no row in this group is
#: truncated: the subject is what the relation COSTS, so a ceiling clipping it
#: would make every payload comparison agree for the wrong reason.
CARRY_RELATION_ROWS = 10

#: The absolute query count one prefetched ``patrons { loans }`` request costs -
#: the parent query plus one prefetch. The fakeshop ``Loan`` model declares its
#: no-op project queryset through ``as_manager()``, so this is measured directly
#: against the public project shape rather than a test-only manager mount.
CARRY_RELATION_QUERIES = 2


@cache
def _carry_relation_schema(patron_type: type) -> DjangoSchema:
    """A real ``LoanQuerySet.as_manager()`` relation under a prefetching plan.

    ``_hostile_relation_schema`` installs no optimizer, so it plans no prefetch
    and its relation branch never reaches the warm-cache path this group is
    about.

    The optimizer is a singleton behind a factory, the one spelling the repo
    permits. The type is an ARGUMENT and the cache is keyed on it, for the reason
    ``_hostile_relation_schema`` gives.
    """
    optimizer = DjangoOptimizerExtension()
    query_cls = strawberry.type(
        type(
            "_CarryRelationQuery",
            (),
            {
                "__annotations__": {"patrons": list[patron_type]},
                "__doc__": "A raw-list root whose many-side target is planned as a prefetch.",
                "patrons": DjangoListField(patron_type),
            },
        ),
    )
    return DjangoSchema(
        query=query_cls,
        config=strawberry_config(),
        resource_policy=ResourcePolicy(max_list_rows=CARRY_RELATION_ROWS),
        extensions=[lambda: optimizer],
    )


def _carry_relation_view(request, *args, **kwargs):
    """Mount the public project-manager relation over the synchronous view."""
    schema = _carry_relation_schema(library_schema.PatronType)
    return DjangoGraphQLView.as_view(schema=schema)(request, *args, **kwargs)


_carry_relation_view.csrf_exempt = True


async def _carry_relation_async_view(request, *args, **kwargs):
    """The async twin, so the rebuilt relation is proven on a real event loop too."""
    schema = _carry_relation_schema(library_schema.PatronType)
    built = AsyncDjangoGraphQLView.as_view(schema=schema)
    return await built(request, *args, **kwargs)


_carry_relation_async_view.csrf_exempt = True


MAX_TOKENS = 40
MAX_DEPTH = 6
MAX_SELECTIONS = 12
MAX_ALIASES = 3
MAX_COST = 5_000
MAX_LIST_ROWS = 3
MAX_PAGE_SIZE = 5
MAX_NESTED_ROWS = 2
MAX_NODE_IDS = 3
MAX_MEMBERSHIP = 4
MAX_RELATION_IDS = 2
MAX_RELATION_IDS_TOTAL = 3
MAX_CONTAINER_WIDTH = 6
MAX_VALUE_DEPTH = 4
MAX_INPUT_NODES = 20
MAX_SCALAR_BYTES = 32
MAX_UPLOAD_COUNT = 1
MAX_UPLOAD_FILE_BYTES = 64
MAX_UPLOAD_TOTAL_BYTES = 96

#: A deadline small enough that it has always passed by the time a resolver
#: runs, which is what makes the cooperative seams assertable without a sleep.
DEADLINE_SECONDS = 0.000_001

_VALUE_BOUNDS = {
    "max_node_ids": MAX_NODE_IDS,
    "max_membership_items": MAX_MEMBERSHIP,
    "max_relation_ids_per_mutation": MAX_RELATION_IDS,
    "max_relation_ids_total": MAX_RELATION_IDS_TOTAL,
    "max_container_width": MAX_CONTAINER_WIDTH,
    "max_input_nodes": MAX_INPUT_NODES,
    "max_scalar_bytes": MAX_SCALAR_BYTES,
}


# Every argument value the custom scalar below was asked to parse, in order. The
# value budget charges the RAW argument the request carried, which is before any
# custom scalar converts it, so this is what says whether a given request was
# admitted as far as conversion at all.
_scalar_parses: list[object] = []


def _record_parse(value):
    """Parse a scalar argument by recording it and handing it back unchanged."""
    _scalar_parses.append(value)
    return value


#: A custom scalar that accepts whatever shape the request carried.
#:
#: An argument typed by one of these is how a raw JSON container reaches the
#: value budget without a declared input object shaping it first, and its parser
#: is the observable marker for the boundary the budget sits on.
OpaqueValue = NewType("OpaqueValue", object)

_OPAQUE_SCALAR = strawberry.scalar(
    name="OpaqueValue",
    serialize=lambda value: value,
    parse_value=_record_parse,
)


@strawberry.type
class _AuthorityQuery:
    """The seams a resolver can reach through ``info.schema``, plus a bounded list."""

    @strawberry.field
    def widen(self, info: strawberry.Info) -> int:
        """Write past the properties holding the policy and the extension list."""
        info.schema.__dict__["resource_policy"] = ResourcePolicy(max_list_rows=999)
        info.schema.__dict__["extensions"] = ()
        return 1

    @strawberry.field
    def reachable_authorities(self, info: strawberry.Info) -> list[str]:
        """Every name on the schema answering with a policy, directly or at one remove.

        Asked by CONTENT rather than by name: a row that spelled out the
        attribute it expects to be absent would pass the moment that attribute
        was renamed, while this one fails for any name at all that puts an
        enforcement policy back in a resolver's reach. Both policies count - one
        record settled them together, and writing the masking one puts raw
        exception text on the wire exactly as writing the other widens a row
        count.
        """
        found = []
        for name, value in vars(info.schema).items():
            for kind, attribute in (
                (ResourcePolicy, "resource_policy"),
                (ErrorPolicy, "error_policy"),
            ):
                if isinstance(value, kind):
                    found.append(name)
                if isinstance(getattr(value, attribute, None), kind):
                    found.append(f"{name}.{attribute}")
        return sorted(found)

    @strawberry.field
    def boom(self) -> str:
        """Raise an exception whose text must never reach a client."""
        raise RuntimeError(UNMASKED_SENTINEL)

    @strawberry.field
    def unmask(self, info: strawberry.Info) -> list[str]:
        """Turn masking off through every name on the schema that could carry it."""
        turned_off = []
        for name, value in list(vars(info.schema).items()):
            policy = (
                value if isinstance(value, ErrorPolicy) else getattr(value, "error_policy", None)
            )
            if isinstance(policy, ErrorPolicy):
                policy.__dict__["enabled"] = False
                turned_off.append(name)
        return turned_off

    @strawberry.field
    def reconfigure(self, info: strawberry.Info) -> str:
        """Run the schema's own constructor again, with a wider policy."""
        try:
            type(info.schema).__init__(
                info.schema,
                query=_AuthorityQuery,
                config=strawberry_config(extra_scalar_map={OpaqueValue: _OPAQUE_SCALAR}),
                resource_policy={"max_list_rows": 999},
            )
        except Exception as exc:
            return type(exc).__name__
        return "reconfigured"

    @strawberry.field
    def nominate(self, info: strawberry.Info) -> int:
        """Replace the extension list with one carrying a wider policy of its own."""
        info.schema.extensions = [
            lambda: DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=999)),
        ]
        return 1

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))

    @strawberry.field
    def take(self, payload: OpaqueValue = None) -> str:
        return "ok"


@cache
def _authority_schema() -> DjangoSchema:
    return DjangoSchema(
        query=_AuthorityQuery,
        config=strawberry_config(extra_scalar_map={OpaqueValue: _OPAQUE_SCALAR}),
        resource_policy={"max_list_rows": 1, "max_container_width": MAX_CONTAINER_WIDTH},
    )


def _authority_view(request, *args, **kwargs):
    built = DjangoGraphQLView.as_view(schema=_authority_schema())
    return built(request, *args, **kwargs)


_authority_view.csrf_exempt = True


@cache
def _entry_rows_schema() -> DjangoSchema:
    """Schema whose narrow bound is declared by an ENTRY rather than by ``resource_policy=``."""
    return DjangoSchema(
        query=_AuthorityQuery,
        config=strawberry_config(extra_scalar_map={OpaqueValue: _OPAQUE_SCALAR}),
        extensions=[DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))],
    )


def _entry_rows_view(request, *args, **kwargs):
    built = DjangoGraphQLView.as_view(schema=_entry_rows_schema())
    return built(request, *args, **kwargs)


_entry_rows_view.csrf_exempt = True


class _EqualSchema(DjangoSchema):
    """A supported subclass that gives its instances VALUE equality.

    Nothing about a schema requires identity semantics from a consumer, so a
    registry that found its entries by hash and equality would let this class
    decide which schema's bounds answer for which schema.
    """

    def __hash__(self):
        return 1

    def __eq__(self, other):
        return isinstance(other, _EqualSchema)


@cache
def _equal_schema(rows: int) -> DjangoSchema:
    return _EqualSchema(
        query=_AuthorityQuery,
        config=strawberry_config(extra_scalar_map={OpaqueValue: _OPAQUE_SCALAR}),
        resource_policy={"max_list_rows": rows, "max_container_width": MAX_CONTAINER_WIDTH},
    )


def _equal_view(rows: int):
    """One mount per equal-but-distinct schema, so two live requests can differ."""

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_equal_schema(rows))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


@strawberry.type
class _AcceptedInstanceQuery:
    """The seams a resolver can reach on an extension INSTANCE the schema accepted."""

    @strawberry.field
    def rebind(self, info: strawberry.Info) -> str:
        """Point the entry that bounds this schema at a wider policy."""
        entry = _accepted_resource_entry(info)
        if entry is None:
            return "unreachable"
        try:
            entry._policy = ResourcePolicy(max_list_rows=999)
        except AttributeError as exc:
            return type(exc).__name__
        return "assigned"

    @strawberry.field
    def overwrite(self, info: strawberry.Info) -> str:
        """Write a wider bound onto the policy object that entry answers with."""
        entry = _accepted_resource_entry(info)
        if entry is None:
            return "unreachable"
        entry._policy.__dict__["max_list_rows"] = 999
        return "written"

    @strawberry.field
    def empty_the_entry(self, info: strawberry.Info) -> list[str]:
        """Delete everything that entry carries, bar the context it is mid-request on."""
        entry = _accepted_resource_entry(info)
        if entry is None:
            return []
        held = entry.__dict__
        dropped = sorted(name for name in held if name != "execution_context")
        for name in dropped:
            del held[name]
        return dropped

    @strawberry.field
    def reachable_authorities(self, info: strawberry.Info) -> list[str]:
        """Every name on a reachable entry answering with a policy, asked by content."""
        entry = _accepted_resource_entry(info)
        if entry is None:
            return []
        return sorted(
            name for name, value in vars(entry).items() if isinstance(value, ResourcePolicy)
        )

    @strawberry.field
    def reconfigure(self, info: strawberry.Info) -> str:
        """Run that entry's own constructor again, with a wider policy."""
        entry = _accepted_resource_entry(info)
        if entry is None:
            return "unreachable"
        try:
            entry.__init__(policy=ResourcePolicy(max_list_rows=999))
        except Exception as exc:
            return type(exc).__name__
        return "reconfigured"

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))


def _accepted_resource_entry(info):
    """The resource extension a resolver reaches through ``info.schema.extensions``.

    ``None`` is the ordinary answer: the extension that bounds an operation is
    built per operation from the schema's own record and is not an entry, so a
    directly supplied one is read as a declaration and does not travel. The
    resolver-facing fields report that as ``unreachable`` rather than raising,
    because "there is nothing here to write" is the outcome these rows are about.
    """
    return next(
        (
            entry
            for entry in info.schema.extensions
            if isinstance(entry, DjangoResourcePolicyExtension)
        ),
        None,
    )


@cache
def _accepted_instance_schema() -> DjangoSchema:
    """A schema configured with an extension INSTANCE carrying its own policy.

    Strawberry deprecates instance entries because one instance shares its
    charge counters across every request; this package still accepts them as
    configuration, which is exactly why what one holds must not be a seam. The
    warning is suppressed HERE rather than at each row, because the mount is
    built inside a request and a warning raised there would be a response, not
    a test outcome.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return DjangoSchema(
            query=_AcceptedInstanceQuery,
            extensions=[
                DjangoResourcePolicyExtension(
                    policy=ResourcePolicy(
                        max_list_rows=1,
                        max_container_width=MAX_CONTAINER_WIDTH,
                    ),
                ),
            ],
        )


def _accepted_instance_view(request, *args, **kwargs):
    built = DjangoGraphQLView.as_view(schema=_accepted_instance_schema())
    return built(request, *args, **kwargs)


_accepted_instance_view.csrf_exempt = True


@cache
def _inherited_instance_schema() -> DjangoSchema:
    """A schema configured with an extension instance that declares NO policy of its own.

    The other supported configuration of the same entry: it enforces the policy
    its schema resolved, per operation, rather than one it was handed. Having no
    override is a configuration, so this instance is as settled as the one that
    carries a policy - and closed to the same second construction.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return DjangoSchema(
            query=_AcceptedInstanceQuery,
            resource_policy=ResourcePolicy(
                max_list_rows=1,
                max_container_width=MAX_CONTAINER_WIDTH,
            ),
            extensions=[DjangoResourcePolicyExtension()],
        )


def _inherited_instance_view(request, *args, **kwargs):
    built = DjangoGraphQLView.as_view(schema=_inherited_instance_schema())
    return built(request, *args, **kwargs)


_inherited_instance_view.csrf_exempt = True


def _widening_factory():
    """The entry a resolver would rather the next operation resolved."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=999))


@strawberry.type
class _MembershipQuery:
    """A bounded list beside the writes that aim at WHICH extensions run it.

    The schema behind this query declared no extensions of its own, so its
    accepted configuration is empty and the two extensions that bound and mask
    its operations are built per operation from its own record. What each row
    here changes is therefore the membership and nothing else, which is the
    question these rows exist to ask: whether a later operation runs the
    extensions that were accepted - and is enforced as the deployment
    configured it - or the ones that were written where the accepted ones are
    held.
    """

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))

    @strawberry.field
    def boom(self) -> str:
        """Raise an exception whose text must never reach a client."""
        raise RuntimeError(UNMASKED_SENTINEL)

    @strawberry.field
    def empty_the_entries(self, info: strawberry.Info) -> list[str]:
        """Leave the schema carrying no extension entries at all."""
        return _write_entries(info, ())

    @strawberry.field
    def widen_the_entries(self, info: strawberry.Info) -> list[str]:
        """Nominate an entry carrying a policy the deployment never accepted."""
        return _write_entries(info, (_widening_factory,))

    @strawberry.field
    def rewrite_behind_the_names(self, info: strawberry.Info) -> list[str]:
        """Write one layer in, through whatever object each private name answers with.

        The write that replaces nothing the package filed: a carrier holding the
        entries keeps its identity while its contents change, so a schema that
        authenticated the holder would hand this membership to the next
        operation. Asked by content, so the row still means something when the
        name or the shape behind it changes.
        """
        written = []
        for name, value in sorted(vars(info.schema).items()):
            held = getattr(value, "__dict__", None)
            if not name.startswith("_django") or held is None:
                continue
            for field in sorted(held):
                held[field] = ()
                written.append(f"{name}.{field}")
        return written


def _write_entries(info, entries):
    """Write ``entries`` over every private name the schema carries."""
    written = []
    for name in sorted(vars(info.schema)):
        if name.startswith("_django"):
            info.schema.__dict__[name] = entries
            written.append(name)
    return written


@cache
def _membership_schema(mount: str) -> DjangoSchema:
    """One schema per row, so a membership one row rewrites is not another's."""
    assert mount
    return DjangoSchema(query=_MembershipQuery, resource_policy=ResourcePolicy(max_list_rows=1))


def _membership_view(mount: str):
    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_membership_schema(mount))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


#: Every extension this mount's factory has built, one per operation it served.
_FACTORY_BUILDS: list[SchemaExtension] = []


class _CountedExtension(SchemaExtension):
    """A consumer extension the mount's factory builds fresh for every operation."""


def _narrow_extension_factory():
    """A fresh extension per operation, the way a consumer's own factory builds one."""
    built = _CountedExtension()
    _FACTORY_BUILDS.append(built)
    return built


@strawberry.type
class _FactoryQuery:
    """The legitimate per-operation construction that closing reconstruction must keep."""

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))

    @strawberry.field
    def builds(self) -> int:
        """How many extensions this mount's factory has built so far."""
        return len(_FACTORY_BUILDS)


@cache
def _factory_schema() -> DjangoSchema:
    return DjangoSchema(
        query=_FactoryQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[_narrow_extension_factory],
    )


def _factory_view(request, *args, **kwargs):
    built = DjangoGraphQLView.as_view(schema=_factory_schema())
    return built(request, *args, **kwargs)


_factory_view.csrf_exempt = True


@strawberry.type
class _DroppableQuery:
    """A bounded list beside the one write that loses a schema's accepted entries."""

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))

    @strawberry.field
    def forge(self, info: strawberry.Info) -> list[str]:
        """Replace every private name the schema carries with something of the same shape."""
        held = info.schema.__dict__
        replaced = sorted(name for name in held if name.startswith("_django"))
        for name in replaced:
            held[name] = ()
        return replaced

    @strawberry.field
    def drop(self, info: strawberry.Info) -> list[str]:
        """Delete every private name the schema carries."""
        held = info.schema.__dict__
        dropped = sorted(name for name in held if name.startswith("_django"))
        for name in dropped:
            del held[name]
        return dropped


@cache
def _droppable_schema(mount: str) -> DjangoSchema:
    """One schema per destructive row, so a refused schema cannot leak into another row."""
    assert mount
    return DjangoSchema(
        query=_DroppableQuery,
        extensions=[
            DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1)),
        ],
    )


def _droppable_view(mount: str):
    def view(request, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            schema = _droppable_schema(mount)
        built = DjangoGraphQLView.as_view(schema=schema)
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


@cache
def _census_schema() -> DjangoSchema:
    """A schema no row writes through, so a census of what it carries means something."""
    return DjangoSchema(
        query=_AuthorityQuery,
        config=strawberry_config(extra_scalar_map={OpaqueValue: _OPAQUE_SCALAR}),
        resource_policy={"max_list_rows": 1},
    )


def _census_view(request, *args, **kwargs):
    built = DjangoGraphQLView.as_view(schema=_census_schema())
    return built(request, *args, **kwargs)


_census_view.csrf_exempt = True


@strawberry.type
class _WitnessQuery:
    """A bounded list on a schema that records whether execution ever began."""

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))


class _ExecutionWitness(SchemaExtension):
    """Record that the executing stage was entered, from outside the guard under test.

    A refusal asserted from inside the extension that issues it cannot tell
    "nothing ran" from "something ran and was stopped on its way out". This
    entry sits ahead of the package's own in the chain, so its hook runs first
    and its record is the operation's own answer to whether execution began.
    """

    entered: list[str] = []

    def on_execute(self):
        """Record the query executing began for, as a generator hook like the package's."""
        _ExecutionWitness.entered.append(self.execution_context.query or "")
        yield


class _CacheNeighbour(SchemaExtension):
    """A consumer entry with no behavior, so the cache has a position to take."""


@cache
def _witness_schema(order: str) -> DjangoSchema:
    """One witnessed schema per position the validation cache takes among the consumer entries.

    The package's own enforcing entry is behind every consumer entry whatever
    the consumer wrote, and the guard is behind that - so what varies here is
    where the cache sits relative to the witness, and the verdict must not.
    """
    if order == "cache-first":
        return DjangoSchema(
            query=_WitnessQuery,
            resource_policy={"max_aliases": CACHE_ALIASES},
            extensions=[ValidationCache, _ExecutionWitness],
        )
    return DjangoSchema(
        query=_WitnessQuery,
        resource_policy={"max_aliases": CACHE_ALIASES},
        extensions=[_ExecutionWitness, ValidationCache],
    )


def _witness_view(order: str):
    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_witness_schema(order))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _witness_async_view(order: str):
    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_witness_schema(order))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


#: The aliases one operation may carry on the validation-cache mounts. Small
#: enough that an ordinary two-alias document is over it, which is what gives the
#: composition matrix a rejecting row that involves no custom scalar at all.
CACHE_ALIASES = 1

#: Exception text a masked response must never carry.
UNMASKED_SENTINEL = "resource-policy-unmasked-sentinel"


@cache
def _cache_schema(order: str) -> DjangoSchema:
    """One schema per position a validation cache can take relative to admission.

    ``ValidationCache`` is an ordinary supported extension that runs the
    validation pass itself and assigns the result over the operation's
    pre-execution errors. Where it sits among the consumer's own entries is the
    consumer's choice, and both choices are configurations this package accepts,
    so both are mounted; the package's enforcing entry is behind all of them
    either way, and the guard is behind that.
    """
    policy = ResourcePolicy(
        max_aliases=CACHE_ALIASES,
        max_container_width=MAX_CONTAINER_WIDTH,
    )
    config = strawberry_config(extra_scalar_map={OpaqueValue: _OPAQUE_SCALAR})
    if order == "none":
        return DjangoSchema(query=_AuthorityQuery, config=config, resource_policy=policy)
    if order == "cache-first":
        return DjangoSchema(
            query=_AuthorityQuery,
            config=config,
            resource_policy=policy,
            extensions=[ValidationCache, _CacheNeighbour],
        )
    return DjangoSchema(
        query=_AuthorityQuery,
        config=config,
        resource_policy=policy,
        extensions=[_CacheNeighbour, ValidationCache],
    )


def _cache_view(order: str):
    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_cache_schema(order))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _cache_async_view(order: str):
    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_cache_schema(order))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


#: The policy object a deployment hands to a schema and then keeps a reference to.
RETAINED_POLICY = ResourcePolicy(max_list_rows=1, max_container_width=MAX_CONTAINER_WIDTH)


@cache
def _retained_schema() -> DjangoSchema:
    return DjangoSchema(
        query=_AuthorityQuery,
        config=strawberry_config(extra_scalar_map={OpaqueValue: _OPAQUE_SCALAR}),
        resource_policy=RETAINED_POLICY,
    )


def _retained_view(request, *args, **kwargs):
    built = DjangoGraphQLView.as_view(schema=_retained_schema())
    return built(request, *args, **kwargs)


_retained_view.csrf_exempt = True


#: Aliases one operation may carry on the shared-entry mounts. An ordinary
#: two-alias document is over it, so the oversized and benign documents differ in
#: nothing but the alias the bound is about.
ENTRY_ALIASES = 1

#: The four spellings Strawberry accepts for a consumer extension entry, and what
#: each one resolves to per operation. Two of them resolve to the SAME object
#: every time - an instance is passed through unchanged and a factory returning a
#: singleton returns it again - which is what makes the shared-entry rows
#: different in kind from their fresh controls rather than a repetition of them.
ENTRY_SPELLINGS = (
    "class",
    "fresh-factory",
    "instance",
    "singleton-factory",
)


class _OverlapCoordinator(SchemaExtension):
    """Hold the oversized operation open until a second operation has run.

    Parks in the PARSING hook's setup half, which is the window the defect lives
    in: every entry's parsing hook sets up before the document is parsed, and the
    enforcing entry charges it in its teardown - so an operation held here is one
    whose charge has not happened yet while another request assigns its own
    context over a shared entry.

    It changes nothing. No policy, no execution context, no extension list and no
    result is touched, and the pause is bounded by an event rather than by a
    sleep, so the row measures the boundary rather than a scheduling guess.
    """

    parked = threading.Event()
    released = threading.Event()
    armed = False

    def on_parse(self):
        """Park the oversized document, once, while the overlap row is armed."""
        if _OverlapCoordinator.armed and "a: rows" in (self.execution_context.query or ""):
            _OverlapCoordinator.parked.set()
            _OverlapCoordinator.released.wait(timeout=10)
        yield


class _SharedEntryExtension(SchemaExtension):
    """A consumer extension, so two of the four spellings share ONE object per mount."""


@cache
def _entry_extension(spelling: str) -> _SharedEntryExtension:
    """The ONE extension object a shared-entry mount hands every operation."""
    return _SharedEntryExtension()


def _entry_entry(spelling: str):
    """The ``extensions=[...]`` entry that spells ``spelling``."""
    if spelling == "class":
        return _SharedEntryExtension
    if spelling == "fresh-factory":
        return lambda: _SharedEntryExtension()
    if spelling == "instance":
        return _entry_extension(spelling)
    return lambda: _entry_extension(spelling)


@cache
def _entry_schema(spelling: str) -> DjangoSchema:
    """One schema per entry spelling, built once so the mount is the same object.

    Every mount is bounded by the same ``resource_policy=``, because the
    extension that spends it is the schema's own either way; what the spelling
    decides is whether the CONSUMER entry beside it is a new object per
    operation or one object every operation shares. Every mount therefore
    refuses the same document for the same reason, which is what makes the four
    rows comparable.

    Strawberry's deprecation warning for the instance spelling is suppressed here
    rather than at each row: the mount is built inside a request, where a raised
    warning would be a response rather than a test outcome.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return DjangoSchema(
            query=_WitnessQuery,
            resource_policy={"max_aliases": ENTRY_ALIASES},
            extensions=[_ExecutionWitness, _OverlapCoordinator, _entry_entry(spelling)],
        )


def _entry_view(spelling: str):
    """Mount the synchronous package view over one entry spelling."""

    def view(request, *args, **kwargs):
        built = DjangoGraphQLView.as_view(schema=_entry_schema(spelling))
        return built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


def _entry_async_view(spelling: str):
    """Mount the asynchronous package view over one entry spelling."""

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_entry_schema(spelling))
        return await built(request, *args, **kwargs)

    view.csrf_exempt = True
    return view


#: Where each entry spelling is mounted, per view color.
ENTRY_MOUNTS = {
    (spelling, color): f"/rp-entry-{spelling}-{color}/"
    for spelling in ENTRY_SPELLINGS
    for color in ("sync", "async")
}


#: Every shared-entry row, with the node id its spelling and color read as.
ENTRY_ROWS = list(ENTRY_MOUNTS)
ENTRY_IDS = [f"{spelling}-{color}" for spelling, color in ENTRY_ROWS]


urlpatterns = [
    path("", include("config.urls")),
    path("rp-authority/", _authority_view),
    # Mounted from ``ENTRY_MOUNTS`` rather than spelled out, so the mounts and the
    # parametrized rows cannot disagree about which spellings exist.
    *(
        path(mount.lstrip("/"), (_entry_view if color == "sync" else _entry_async_view)(spelling))
        for (spelling, color), mount in ENTRY_MOUNTS.items()
    ),
    path("rp-entry-rows/", _entry_rows_view),
    path("rp-equal-narrow/", _equal_view(1)),
    path("rp-equal-wide/", _equal_view(3)),
    path("rp-retained/", _retained_view),
    path("rp-accepted-instance/", _accepted_instance_view),
    path("rp-inherited-instance/", _inherited_instance_view),
    path("rp-factory-entry/", _factory_view),
    path("rp-emptied-entries/", _membership_view("emptied")),
    path("rp-widened-entries/", _membership_view("widened")),
    path("rp-rewritten-entries/", _membership_view("rewritten")),
    path("rp-forged-entries/", _droppable_view("forged")),
    path("rp-dropped-entries/", _droppable_view("dropped")),
    path("rp-census/", _census_view),
    path("rp-witness-cache-first/", _witness_view("cache-first")),
    path("rp-witness-cache-last/", _witness_view("cache-last")),
    path("rp-witness-cache-last-async/", _witness_async_view("cache-last")),
    path("rp-cache-none/", _cache_view("none")),
    path("rp-cache-first/", _cache_view("cache-first")),
    path("rp-cache-last/", _cache_view("cache-last")),
    path("rp-cache-first-async/", _cache_async_view("cache-first")),
    path("rp-cache-last-async/", _cache_async_view("cache-last")),
    path(
        "rp-max-bound/",
        _probe_view(
            max_list_rows=MAX_RESOURCE_BOUND,
            max_collection_cost=MAX_RESOURCE_BOUND,
        ),
    ),
    path("rp-tokens/", _probe_view(max_document_tokens=MAX_TOKENS)),
    path("rp-depth/", _probe_view(max_depth=MAX_DEPTH)),
    path(
        "rp-shape/",
        _probe_view(max_selections=MAX_SELECTIONS, max_aliases=MAX_ALIASES),
    ),
    path("rp-cost/", _probe_view(max_collection_cost=MAX_COST)),
    path("rp-nested-rows/", _probe_view(max_nested_rows=MAX_NESTED_ROWS)),
    path("rp-values/", _probe_view(**_VALUE_BOUNDS)),
    path("rp-value-depth/", _probe_view(max_value_depth=MAX_VALUE_DEPTH)),
    path("rp-deadline/", _probe_view(execution_deadline_seconds=DEADLINE_SECONDS)),
    path("rp-values-async/", _probe_async_view(**_VALUE_BOUNDS)),
    path("rp-hostile-relation/", _hostile_relation_view),
    path("rp-hostile-relation-async/", _hostile_relation_async_view),
    path("rp-carry-relation/", _carry_relation_view),
    path("rp-carry-relation-async/", _carry_relation_async_view),
    path(
        "rp-rows/",
        _probe_view(max_list_rows=MAX_LIST_ROWS, max_page_size=MAX_PAGE_SIZE),
    ),
    path(
        "rp-list-cost/",
        _probe_view(
            max_list_rows=MAX_LIST_ROWS,
            max_collection_cost=MAX_LIST_ROWS - 1,
        ),
    ),
    path(
        "rp-uploads/",
        _probe_upload_view(
            max_upload_count=MAX_UPLOAD_COUNT,
            max_upload_file_bytes=MAX_UPLOAD_FILE_BYTES,
            max_upload_total_bytes=MAX_UPLOAD_TOTAL_BYTES,
        ),
    ),
]


def _post(
    mount,
    query,
    variables=None,
    *,
    client=None,
):
    """POST one GraphQL document to a probe mount and return the parsed envelope."""
    return graphql_payload(
        query,
        client=client,
        variables=variables,
        url=mount,
    )


def _rejection(payload):
    """Return the single resource rejection in ``payload``, asserting its shape.

    Every row funnels through here, so "the request was rejected" always means
    the SAME thing: no data, exactly one error, and the one typed code. A row
    that merely asserted "errors is non-empty" would pass on a validation error
    or a resolver crash.
    """
    assert payload["data"] is None, payload
    errors = payload["errors"]
    assert len(errors) == 1, errors
    extensions = errors[0]["extensions"]
    assert extensions["code"] == RESOURCE_LIMIT_ERROR_CODE, extensions
    return extensions


def _no_rejection(payload):
    """Assert ``payload`` carries no resource rejection (it may carry other errors).

    The under/at-boundary half of each pair. It deliberately does NOT demand a
    fully successful response: several at-boundary rows drive write surfaces that
    answer with a permission or validation error, and a row about a resource
    bound must not silently start asserting the auth contract instead.
    """
    for error in payload.get("errors") or []:
        assert (error.get("extensions") or {}).get("code") != RESOURCE_LIMIT_ERROR_CODE, payload


# ---------------------------------------------------------------------------
# Document text bounds: charged before the parse
# ---------------------------------------------------------------------------


def test_document_under_the_token_bound_executes():
    payload = _post("/rp-tokens/", "{ __typename }")
    _no_rejection(payload)
    assert payload["data"]["__typename"] == "Query"


def test_document_over_the_token_bound_is_rejected():
    """Tokens are charged on the raw text, so the document never reaches the parser."""
    fields = " ".join(f"a{index}: __typename" for index in range(MAX_TOKENS))
    extensions = _rejection(_post("/rp-tokens/", "{ %s }" % fields))
    assert extensions["bound"] == "max_document_tokens"
    assert extensions["limit"] == MAX_TOKENS
    assert extensions["charged"] == MAX_TOKENS + 1


def _post_named(mount, query, operation_name):
    """POST a document with an ``operationName``, which the shared client cannot express.

    The raw-envelope exemption (spec-043): the subject IS the wire field, so the
    body is hand-built rather than replaced by the client's body-builder.
    """
    response = Client().post(
        mount,
        data=json.dumps({"query": query, "operationName": operation_name}),
        content_type="application/json",
    )
    assert response.status_code == 200
    return response.json()


#: One persisted document carrying a small operation and an oversized one. The
#: small operation alone is comfortably under ``MAX_TOKENS``.
_TWO_OPERATIONS = "query Small { __typename }\nquery Big { %s }" % " ".join(
    f"a{index}: __typename" for index in range(MAX_TOKENS)
)


def test_the_token_bound_is_charged_over_the_whole_request_document():
    """``max_document_tokens`` bounds the parse, and the parse reads every operation.

    Naming one operation does not make the rest of the document free: it is
    lexed, it is parsed, and nothing has identified the selected operation until
    that parse has finished. The bound a deployment configures here is a ceiling
    on a request, not on an operation.
    """
    extensions = _rejection(_post_named("/rp-tokens/", _TWO_OPERATIONS, "Small"))
    assert extensions["bound"] == "max_document_tokens"


def test_the_named_operation_alone_is_under_the_same_token_bound():
    """The control: the document, minus the operation it did not name, executes."""
    payload = _post_named("/rp-tokens/", "query Small { __typename }", "Small")
    assert payload["data"] == {"__typename": "Query"}


def test_a_malformed_document_keeps_the_parsers_own_syntax_diagnostic():
    """A document the lexer cannot finish comes back as a syntax error, not a resource rejection.

    The scan tokenizes the raw text to charge it, so it meets a malformed
    document before graphql-core does. Swallowing its own lexer error is what
    lets the accurate diagnostic survive; reporting it would answer a syntax
    mistake with a bound nothing exceeded. The must-not is the row below: the
    swallow is scoped to the lexer's complaint and does not also discard the
    tokens already charged.
    """
    payload = _post("/rp-tokens/", "{ foo(bar: 'single quotes') }")

    _no_rejection(payload)
    assert payload["data"] is None, payload
    assert len(payload["errors"]) == 1, payload
    assert "Syntax Error" in payload["errors"][0]["message"], payload


def test_a_malformed_document_over_the_token_bound_is_rejected_on_size():
    """Tokens are charged as they are lexed, so size fires before the lexer reaches the garbage."""
    fields = " ".join(f"a{index}: __typename" for index in range(MAX_TOKENS))

    extensions = _rejection(_post("/rp-tokens/", "{ %s 'garbage' }" % fields))

    assert extensions["bound"] == "max_document_tokens"
    assert extensions["limit"] == MAX_TOKENS


def test_document_over_the_depth_bound_is_rejected():
    """Structural nesting is charged before the parse, so deep documents cannot recurse it."""
    query = "{ " * (MAX_DEPTH + 1) + "__typename" + " }" * (MAX_DEPTH + 1)
    extensions = _rejection(_post("/rp-depth/", query))
    assert extensions["bound"] == "max_depth"
    assert extensions["charged"] == MAX_DEPTH + 1


def test_depth_counts_argument_and_input_object_nesting():
    """Argument and input-object brackets count toward depth, as the bound documents.

    The scan runs before the parse, where nothing distinguishes an argument list
    from a selection set. Pinning it here means the pre-parse bound's shape is a
    contract rather than an implementation detail a later reader might "fix".
    """
    query = (
        "{ allLibraryGenres(filter: { and: [ { and: [ { and: "
        '[ { name: { exact: "x" } } ] } ] } ] }) { name } }'
    )
    extensions = _rejection(_post("/rp-depth/", query))
    assert extensions["bound"] == "max_depth"


# ---------------------------------------------------------------------------
# Expanded-document bounds: fragments, aliases, directives, collection cost
# ---------------------------------------------------------------------------


def test_selections_are_charged_after_fragment_expansion():
    """A fragment is charged at EVERY spread site, so spreading it N times costs N times.

    The evasion this closes: moving a selection set into a fragment and spreading
    it repeatedly leaves the document small while the executed selection set is
    not.
    """
    spreads = " ".join("g%d: allLibraryGenres { ...F }" % index for index in range(4))
    query = "{ %s } fragment F on GenreType { name id }" % spreads
    extensions = _rejection(_post("/rp-shape/", query))
    assert extensions["bound"] in {"max_selections", "max_aliases"}


def test_a_directive_does_not_hide_a_selection_from_accounting():
    """``@skip`` changes what is RETURNED, never what is charged.

    Charging only the fields a directive lets through would make ``@skip(if:
    true)`` a free pass around every document bound.
    """
    fields = " ".join(
        f"s{index}: __typename @skip(if: true)" for index in range(MAX_SELECTIONS + 2)
    )
    extensions = _rejection(_post("/rp-shape/", "{ %s }" % fields))
    assert extensions["bound"] in {"max_selections", "max_aliases"}


def test_the_same_field_under_many_aliases_is_charged_once_per_alias():
    aliased = " ".join(f"a{index}: __typename" for index in range(MAX_ALIASES + 1))
    extensions = _rejection(_post("/rp-shape/", "{ %s }" % aliased))
    assert extensions["bound"] == "max_aliases"
    assert extensions["charged"] == MAX_ALIASES + 1


#: Two operations, one small and one over a post-parse bound. Naming ``Small``
#: is what proves the walk filters by ``operationName``: the pre-parse token
#: pair on ``/rp-tokens/`` is the counterpart that does not filter.
_SHAPE_ALIAS_FIELDS = " ".join(f"a{index}: __typename" for index in range(MAX_ALIASES + 1))
_SHAPE_SPREAD_FIELDS = " ".join("...F" for _ in range(MAX_SELECTIONS + 1))
_SHAPE_NAMED_ALIAS_DOCUMENT = (
    f"query Small {{ __typename }}\nquery Big {{ {_SHAPE_ALIAS_FIELDS} }}"
)
_SHAPE_NAMED_SPREAD_DOCUMENT = (
    f"query Small {{ __typename }}\nquery Big {{ {_SHAPE_SPREAD_FIELDS} }}"
    "\nfragment F on Query { __typename }"
)
#: Anonymous leading operation so Strawberry does not infer ``operationName`` from
#: a first named operation (``query Small`` would execute ``Small`` and skip
#: ``Big``). That is the wire shape that leaves the walk's operation filter unset.
_SHAPE_ANON_ALIAS_DOCUMENT = f"{{ __typename }}\nquery Big {{ {_SHAPE_ALIAS_FIELDS} }}"
_SHAPE_ANON_SPREAD_DOCUMENT = (
    f"{{ __typename }}\nquery Big {{ {_SHAPE_SPREAD_FIELDS} }}"
    "\nfragment F on Query { __typename }"
)
_SHAPE_OVERSIZE_CASES = [
    pytest.param(
        _SHAPE_NAMED_ALIAS_DOCUMENT,
        "max_aliases",
        MAX_ALIASES + 1,
        id="oversized-aliases",
    ),
    pytest.param(
        _SHAPE_NAMED_SPREAD_DOCUMENT,
        "max_selections",
        MAX_SELECTIONS + 1,
        id="oversized-fragment-spreads",
    ),
]
_SHAPE_ANON_OVERSIZE_CASES = [
    pytest.param(
        _SHAPE_ANON_ALIAS_DOCUMENT,
        "max_aliases",
        MAX_ALIASES + 1,
        id="oversized-aliases",
    ),
    pytest.param(
        _SHAPE_ANON_SPREAD_DOCUMENT,
        "max_selections",
        MAX_SELECTIONS + 1,
        id="oversized-fragment-spreads",
    ),
]


@pytest.mark.parametrize(
    "document",
    [_SHAPE_NAMED_ALIAS_DOCUMENT, _SHAPE_NAMED_SPREAD_DOCUMENT],
    ids=["oversized-aliases", "oversized-fragment-spreads"],
)
def test_naming_the_small_operation_does_not_charge_the_oversized_sibling(document):
    """Post-parse bounds charge only the operation ``operationName`` names.

    ``Big`` is over the alias or selection ceiling; ``Small`` is not. Naming
    ``Small`` therefore executes, which is what fails if the walk still charged
    every operation in the document. The token-bound pair on ``/rp-tokens/`` is
    the other half: the parse still reads the whole request.
    """
    payload = _post_named("/rp-shape/", document, "Small")
    _no_rejection(payload)
    assert payload["data"] == {"__typename": "Query"}


@pytest.mark.parametrize(
    ("document", "bound", "charged"),
    _SHAPE_OVERSIZE_CASES,
)
def test_naming_the_oversized_operation_rejects_on_its_own_shape(document, bound, charged):
    """The must-not: naming the oversized sibling still charges it."""
    extensions = _rejection(_post_named("/rp-shape/", document, "Big"))
    assert extensions["bound"] == bound
    assert extensions["charged"] == charged


@pytest.mark.parametrize(
    ("document", "bound", "charged"),
    _SHAPE_ANON_OVERSIZE_CASES,
)
def test_an_unnamed_multi_operation_document_is_charged_in_full(document, bound, charged):
    """With no ``operationName``, every operation in the document is charged.

    The leading operation is anonymous so the engine cannot infer a name from
    the first definition and skip ``Big``. GraphQL would then refuse the
    document for lacking a name, but the budget runs first: ``Big`` is over a
    post-parse ceiling, so the typed resource rejection is what the client sees.
    """
    extensions = _rejection(_post("/rp-shape/", document))
    assert extensions["bound"] == bound
    assert extensions["charged"] == charged


def test_nested_collections_are_charged_multiplicatively():
    """Two nested full pages cost their product, which is what the cost bound sees."""
    query = """
    {
      allCategories {
        edges { node { itemsConnection { edges { node { name } } } } }
      }
    }
    """
    extensions = _rejection(_post("/rp-cost/", query))
    assert extensions["bound"] == "max_collection_cost"
    assert extensions["charged"] > MAX_COST


def test_an_introspection_document_is_charged_like_any_other():
    """Introspection is a document shape, not an exemption.

    ``__schema`` opens a subtree over every type, field and argument in the
    schema. A walk that could not resolve the meta-fields charged the whole of
    it as one selection and then stopped descending, so introspection was the
    one shape no depth, selection, or collection bound could see. Here the
    nested ``types { fields { ... } }`` lists charge multiplicatively like any
    other nested collection.
    """
    extensions = _rejection(_post("/rp-cost/", "{ __schema { types { fields { name } } } }"))
    assert extensions["bound"] == "max_collection_cost"
    assert extensions["charged"] > MAX_COST


def test_an_explicit_small_page_narrows_the_collection_cost():
    """``first:`` narrows the charge, so a client that asks for less is charged less."""
    query = """
    {
      allCategories(first: 2) {
        edges { node { itemsConnection(first: 2) { edges { node { name } } } } }
      }
    }
    """
    _no_rejection(_post("/rp-cost/", query))


# ---------------------------------------------------------------------------
# Value bounds: a tiny document carrying a large variable payload
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_nested_row_list_over_the_bound_is_rejected():
    """A list of input objects is a nested row set, charged on ``max_nested_rows``.

    The ``and`` combinator is a list of filter input objects - the same shape a
    nested serializer / formset payload presents on a write. Three branches
    against a bound of two must reject on ``max_nested_rows`` specifically: a
    row that only widened ``max_container_width`` or ``max_input_nodes`` would
    let the bound silently stop applying to the nested-row shape.
    """
    branches = ", ".join('{ name: { exact: "x" } }' for _ in range(MAX_NESTED_ROWS + 1))
    query = "{ allLibraryGenres(filter: { and: [%s] }) { name } }" % branches
    extensions = _rejection(_post("/rp-nested-rows/", query))
    assert extensions["bound"] == "max_nested_rows"
    assert extensions["charged"] == MAX_NESTED_ROWS + 1


@pytest.mark.django_db
def test_a_nested_row_list_at_the_bound_is_not_rejected():
    branches = ", ".join('{ name: { exact: "x" } }' for _ in range(MAX_NESTED_ROWS))
    query = "{ allLibraryGenres(filter: { and: [%s] }) { name } }" % branches
    _no_rejection(_post("/rp-nested-rows/", query))


@pytest.mark.django_db
def test_a_nested_row_list_rides_in_through_one_variable():
    """The tiny-document / large-variable shape, on the nested-rows bound.

    ``$f`` carries the whole row list in a variable, so no document bracket
    reflects its width - the same tiny-document/large-payload shape the other
    value bounds are charged from, here answered from the declared input type
    of ``and`` rather than from any bracket in the text.
    """
    rows = [{"name": {"exact": "x"}}] * (MAX_NESTED_ROWS + 1)
    extensions = _rejection(
        _post(
            "/rp-nested-rows/",
            "query R($f: [GenreFilterInputType!]) { "
            "allLibraryGenres(filter: { and: $f }) { name } }",
            {"f": rows},
        ),
    )
    assert extensions["bound"] == "max_nested_rows"
    assert extensions["charged"] == MAX_NESTED_ROWS + 1


_NODES = "query N($ids: [ID!]!) { nodes(ids: $ids) { __typename } }"
_GENRE_IN = "query G($ids: [String!]) { allLibraryGenres(filter: { id: { in: $ids } }) { name } }"
_GENRE_FILTER = "query G($f: GenreFilterInputType) { allLibraryGenres(filter: $f) { name } }"


@pytest.mark.django_db
def test_node_refetch_ids_at_the_bound_are_not_rejected():
    _no_rejection(_post("/rp-values/", _NODES, {"ids": ["x"] * MAX_NODE_IDS}))


@pytest.mark.django_db
def test_node_refetch_ids_over_the_bound_are_rejected_before_any_id_is_decoded():
    """A tiny document with a large variable payload - the shape S4 names.

    The rejection is charged from the variable list, so no GlobalID is decoded
    and no queryset is built; the query-count assertion is the evidence, since a
    decoded id would have driven at least one lookup.
    """
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post("/rp-values/", _NODES, {"ids": ["x"] * (MAX_NODE_IDS + 1)})
    extensions = _rejection(payload)
    assert extensions["bound"] == "max_node_ids"
    assert extensions["charged"] == MAX_NODE_IDS + 1
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_duplicate_node_ids_are_charged_positionally():
    """Duplicates cost what they cost: the framework reassembles every position.

    The database may collapse an ``IN`` predicate, but ``DjangoNodesField``
    preserves duplicates positionally, so charging the deduplicated width would
    charge for work the request does not do.
    """
    extensions = _rejection(_post("/rp-values/", _NODES, {"ids": ["same"] * (MAX_NODE_IDS + 1)}))
    assert extensions["charged"] == MAX_NODE_IDS + 1


@pytest.mark.django_db
def test_an_empty_id_list_is_not_rejected():
    _no_rejection(_post("/rp-values/", _NODES, {"ids": []}))


@pytest.mark.django_db
def test_membership_list_over_the_bound_is_rejected():
    extensions = _rejection(_post("/rp-values/", _GENRE_IN, {"ids": ["1"] * (MAX_MEMBERSHIP + 1)}))
    assert extensions["bound"] == "max_membership_items"


@pytest.mark.django_db
def test_membership_list_at_the_bound_is_not_rejected():
    _no_rejection(_post("/rp-values/", _GENRE_IN, {"ids": ["1"] * MAX_MEMBERSHIP}))


_MEMBERSHIP_DEFAULT_OVER = (
    'query MyQuery($ids: [String!] = ["1", "2", "3", "4", "5"]) { '
    "allLibraryGenres(filter: { id: { in: $ids } }) { name } "
    "}"
)
_MEMBERSHIP_DEFAULT_AT = (
    'query MyQuery($ids: [String!] = ["1", "2", "3", "4"]) { '
    "allLibraryGenres(filter: { id: { in: $ids } }) { name } "
    "}"
)


@pytest.mark.django_db
def test_variable_default_value_in_operation_header_is_rejected_when_omitted():
    """An omitted variable is charged as its document default, over and at the bound."""
    extensions = _rejection(_post("/rp-values/", _MEMBERSHIP_DEFAULT_OVER, {}))
    assert extensions["bound"] == "max_membership_items"
    assert extensions["charged"] == MAX_MEMBERSHIP + 1
    _no_rejection(_post("/rp-values/", _MEMBERSHIP_DEFAULT_AT, {}))


@pytest.mark.django_db
def test_variable_default_value_in_operation_header_ignored_when_overridden():
    """An explicit variable is charged as the runtime list, not the document default.

    Under the bound the request runs; over it the charge is the runtime width
    (five), never the default that would have been five either - a walker that
    ignored both would pass the under-bound arm, and a walker that still charged
    the default would fail it.
    """
    _no_rejection(_post("/rp-values/", _MEMBERSHIP_DEFAULT_OVER, {"ids": ["1", "2"]}))
    extensions = _rejection(
        _post("/rp-values/", _MEMBERSHIP_DEFAULT_OVER, {"ids": ["1"] * (MAX_MEMBERSHIP + 1)}),
    )
    assert extensions["bound"] == "max_membership_items"
    assert extensions["charged"] == MAX_MEMBERSHIP + 1


@pytest.mark.django_db
def test_a_wide_filter_tree_is_charged_by_container_width():
    """An ``and``/``or`` tree's WIDTH is bounded, not only its depth."""
    branches = ", ".join('{ name: { exact: "x" } }' for _ in range(MAX_CONTAINER_WIDTH + 1))
    query = "{ allLibraryGenres(filter: { and: [%s] }) { name } }" % branches
    extensions = _rejection(_post("/rp-values/", query))
    assert extensions["bound"] == "max_container_width"


@pytest.mark.django_db
def test_relation_ids_in_one_mutation_are_bounded():
    mutation = (
        "mutation B($d: BookInput!) { createBookViaCustomInput(data: $d) "
        "{ node { title } errors { field messages } } }"
    )
    variables = {
        "d": {
            "title": "t",
            "subtitle": "s",
            "shelfId": 1,
            "genres": ["1"] * (MAX_RELATION_IDS + 1),
        },
    }
    extensions = _rejection(_post("/rp-values/", mutation, variables))
    assert extensions["bound"] == "max_relation_ids_per_mutation"


@pytest.mark.django_db
def test_relation_ids_across_several_mutation_fields_are_bounded_in_aggregate():
    """Two writes that each pass the per-field bound can still exceed the request's.

    Serial mutation fields are one request's worth of work, so the aggregate
    bound is the one that sees a batch assembled out of individually-legal
    writes.
    """
    mutation = """
    mutation B($a: BookInput!, $b: BookInput!) {
      first: createBookViaCustomInput(data: $a) { node { title } }
      second: createBookViaCustomInput(data: $b) { node { title } }
    }
    """
    payload = {
        "title": "t",
        "subtitle": "s",
        "shelfId": 1,
        "genres": ["1", "2"],
    }
    extensions = _rejection(
        _post("/rp-values/", mutation, {"a": payload, "b": dict(payload)}),
    )
    assert extensions["bound"] == "max_relation_ids_total"
    assert extensions["charged"] == 4


@pytest.mark.django_db
def test_one_variable_spliced_into_two_mutation_fields_is_charged_twice():
    """The bypass a charge-once-per-container cache left open, over the wire.

    ``$g`` is ONE Python list object, and splicing it into two mutation fields
    resolves to that same object both times. Charging a container once per
    request therefore charged the second field's relation ids as free - two
    fields of two ids apiece counted as two - and the aggregate bound never
    fired. Every reference is work, so every reference is charged: 4 against an
    aggregate of 3.
    """
    mutation = """
    mutation B($g: [ID!]!) {
      first: createBookViaCustomInput(
        data: { title: "t", subtitle: "s", shelfId: 1, genres: $g }
      ) { node { title } }
      second: createBookViaCustomInput(
        data: { title: "u", subtitle: "s", shelfId: 1, genres: $g }
      ) { node { title } }
    }
    """
    extensions = _rejection(_post("/rp-values/", mutation, {"g": ["1", "2"]}))
    assert extensions["bound"] == "max_relation_ids_total"
    assert extensions["charged"] == 4


# ---------------------------------------------------------------------------
# Raw-pk relation id sets: the write input's own bind record, not the scalar name
# ---------------------------------------------------------------------------


#: A ``Shelf`` write carries raw-pk relation lists on every flavor (the related
#: ``BranchType`` primary is non-Relay, so the ids render ``[Int!]``), while the
#: ``Book`` writes are the GlobalID twins (``[ID!]``). A name-keyed rule charges
#: the ``[ID!]`` twins and passes every raw-pk list as a membership list; the
#: bind specs - the same records the request-time decode walks - are what
#: classify both spellings alike.
_RAW_PK_SHELF_MODEL = (
    "mutation S($d: ShelfAlt_ubranchesBranchCodeInput!) { createShelf(data: $d) "
    "{ result { code } errors { field messages } } }"
)
_RAW_PK_SHELF_FORM = (
    "mutation S($d: ShelfRelationsFormInput!) { createShelfViaForm(data: $d) "
    "{ result { code } errors { field messages } } }"
)
_RAW_PK_SHELF_SERIALIZER = (
    "mutation S($d: AltBranchesShelfSerializerInput!) { "
    "createShelfViaAltBranchesSerializer(data: $d) "
    "{ result { code } errors { field messages } } }"
)
_GLOBAL_ID_SERIALIZER_UPDATE = (
    "mutation U($id: ID!, $d: BookGenresSerializerPartialInput!) { "
    "updateBookGenresViaSerializer(id: $id, data: $d) "
    "{ node { title } errors { field messages } } }"
)


def _data_input_type(field: str) -> str:
    """Return the generated input type name of a mutation field's ``data`` argument.

    Serializer hook-derived input names carry a descriptor digest, so the nested
    row's input type is read off the probe schema instead of being hard-coded.
    """
    mutation_field = _probe_schema(())._schema.mutation_type.fields[field]
    argument_type = mutation_field.args["data"].type
    while hasattr(argument_type, "of_type"):
        argument_type = argument_type.of_type
    return argument_type.name


@pytest.mark.django_db
def test_a_raw_pk_model_relation_list_over_the_bound_is_rejected():
    """A raw-pk relation list charges the relation bound, like its GlobalID twin.

    The wire item type of a raw-pk relation is ``Int`` - ``createShelf``'s
    ``altBranches`` renders ``[Int!]`` - so a classification keyed on the
    ``ID`` scalar name never saw these lists and the relation bound was free
    for every non-Relay write. The bind spec the owning mutation stashed is
    what classifies the list: width 3 against a per-mutation bound of 2.
    """
    variables = {"d": {"code": "RP-Model", "altBranches": [1, 1, 1]}}
    extensions = _rejection(_post("/rp-values/", _RAW_PK_SHELF_MODEL, variables))
    assert extensions["bound"] == "max_relation_ids_per_mutation"
    assert extensions["charged"] == MAX_RELATION_IDS + 1


@pytest.mark.django_db
def test_a_raw_pk_form_relation_list_over_the_bound_is_rejected():
    """The FORM flavor's raw-pk M2M charges the relation bound like its model twin."""
    extensions = _rejection(
        _post(
            "/rp-values/",
            _RAW_PK_SHELF_FORM,
            {"d": {"code": "RP-F", "altBranches": [1, 1, 1]}},
        ),
    )
    assert extensions["bound"] == "max_relation_ids_per_mutation"
    assert extensions["charged"] == MAX_RELATION_IDS + 1


@pytest.mark.django_db
def test_a_raw_pk_serializer_relation_list_over_the_bound_is_rejected():
    """The SERIALIZER flavor's raw-pk M2M charges the relation bound like its twins."""
    extensions = _rejection(
        _post(
            "/rp-values/",
            _RAW_PK_SHELF_SERIALIZER,
            {"d": {"code": "RP-2", "altBranches": [1, 1, 1]}},
        ),
    )
    assert extensions["bound"] == "max_relation_ids_per_mutation"
    assert extensions["charged"] == MAX_RELATION_IDS + 1


@pytest.mark.django_db
def test_a_nested_serializer_row_relation_list_is_charged_against_the_field():
    """A raw-pk relation list inside a NESTED row charges its enclosing field.

    ``createBranchWithNestedShelves`` carries ``shelves: [<row>!]``, and each row
    exposes a raw-pk ``altBranches`` list. The nested rows' own bind specs (the
    ``nested_specs`` records on the enclosing field's spec) classify the nested
    list, so a hostile client cannot park relation ids a level deep where the
    scalar name - absent here - would never see them.
    """
    input_type = _data_input_type("createBranchWithNestedShelves")
    mutation = (
        "mutation N($d: " + input_type + "!) { createBranchWithNestedShelves(data: $d) "
        "{ result { id } errors { field messages } } }"
    )
    variables = {
        "d": {"name": "RP-Nested", "shelves": [{"code": "RP-N1", "altBranches": [1, 1, 1]}]},
    }
    extensions = _rejection(_post("/rp-values/", mutation, variables))
    assert extensions["bound"] == "max_relation_ids_per_mutation"
    assert extensions["charged"] == MAX_RELATION_IDS + 1


@pytest.mark.django_db
def test_a_global_id_relation_list_still_charges_the_relation_bound():
    """The ``ID``-typed twin keeps its bound - the spec and the name agree there.

    The serializer UPDATE shape's relation list rides ``GlobalID``; it charged
    correctly under the name rule and must keep doing so under the spec rule,
    which only ever ADDS a signal, never replaces the fallback for inputs the
    package did not generate.
    """
    extensions = _rejection(
        _post(
            "/rp-values/",
            _GLOBAL_ID_SERIALIZER_UPDATE,
            {"id": "Qm9vazox", "d": {"genres": ["1", "2", "3"]}},
        ),
    )
    assert extensions["bound"] == "max_relation_ids_per_mutation"
    assert extensions["charged"] == MAX_RELATION_IDS + 1


@pytest.mark.django_db
def test_raw_pk_relation_lists_at_the_bound_execute():
    """The bound is a ceiling over legal writes, not a wall in front of them.

    Two visible branches at a per-field bound of two run the whole decode +
    write path: the bound charges the shape, and a legal width still writes.
    """
    home = library_models.Branch.objects.create(name="RPHome", city="open")
    alt1 = library_models.Branch.objects.create(name="RPAlt1", city="open")
    alt2 = library_models.Branch.objects.create(name="RPAlt2", city="open")
    payload = _post(
        "/rp-values/",
        _RAW_PK_SHELF_MODEL,
        {"d": {"code": "RP-OK", "branchId": home.pk, "altBranches": [alt1.pk, alt2.pk]}},
    )
    _no_rejection(payload)
    assert payload["data"]["createShelf"]["result"]["code"] == "RP-OK"
    shelf = library_models.Shelf.objects.get(code="RP-OK")
    assert set(shelf.alt_branches.values_list("pk", flat=True)) == {alt1.pk, alt2.pk}


@pytest.mark.django_db
def test_raw_pk_relation_ids_across_fields_accumulate_in_the_aggregate():
    """Two raw-pk writes that each pass the per-field bound exhaust the request's total.

    The aggregate is the bound that sees a batch assembled out of
    individually-legal writes, whatever flavor each write rides. Two model
    fields of two raw-pk ids apiece are 4 against an aggregate of 3 - and the
    per-field counter reset between them is what proves the aggregate is a
    separate budget, not the per-field one misfiring.
    """
    mutation = """
    mutation S($a: ShelfAlt_ubranchesBranchCodeInput!, $b: ShelfAlt_ubranchesBranchCodeInput!) {
      first: createShelf(data: $a) { result { code } }
      second: createShelf(data: $b) { result { code } }
    }
    """
    variables = {
        "a": {"code": "RP-A", "altBranches": [1, 2]},
        "b": {"code": "RP-2", "altBranches": [1, 2]},
    }
    extensions = _rejection(_post("/rp-values/", mutation, variables))
    assert extensions["bound"] == "max_relation_ids_total"
    assert extensions["charged"] == 4


@pytest.mark.django_db
def test_a_global_id_relation_and_a_raw_pk_relation_share_one_aggregate():
    """One aggregate budget, two spellings of the same write.

    The request batches a raw-pk model write (2 ids) with a GlobalID serializer
    update (2 ids): both charge ``max_relation_ids_total``, so a batch assembled
    from differently-typed relation lists cannot spend more than one budget.
    """
    mutation = """
    mutation M($s: ShelfAlt_ubranchesBranchCodeInput!, $d: BookGenresSerializerPartialInput!, $id: ID!) {
      shelf: createShelf(data: $s) { result { code } }
      book: updateBookGenresViaSerializer(id: $id, data: $d) { node { title } }
    }
    """
    variables = {
        "s": {"code": "RP-3", "altBranches": [1, 2]},
        "id": "Qm9vazox",
        "d": {"genres": ["1", "2"]},
    }
    extensions = _rejection(_post("/rp-values/", mutation, variables))
    assert extensions["bound"] == "max_relation_ids_total"
    assert extensions["charged"] == 4


@pytest.mark.django_db
def test_a_nested_row_relation_list_at_the_bound_is_not_rejected():
    """The under-boundary half on the nested tier: one row of one id stays legal."""
    input_type = _data_input_type("createBranchWithNestedShelves")
    mutation = (
        "mutation N($d: " + input_type + "!) { createBranchWithNestedShelves(data: $d) "
        "{ result { id } errors { field messages } } }"
    )
    variables = {"d": {"name": "RP-NestedOK", "shelves": [{"code": "RP-N2", "altBranches": [1]}]}}
    _no_rejection(_post("/rp-values/", mutation, variables))


@pytest.mark.django_db
def test_a_membership_list_inside_a_generated_mutation_input_stays_membership():
    """Spec-keyed classification charges only RELATION fields as relations.

    ``ShelfAlt_ubranchesBranchCodeInput.branchId`` is a raw-pk SINGLE relation
    (one id, not a list); its sibling ``code`` is a scalar. Neither is a relation
    LIST, so a raw-pk write carrying only those reaches the resolver with no
    resource rejection - the control proving the spec signal charges only the
    LIST fields that ARE relations, which is what keeps
    ``test_raw_pk_relation_lists_at_the_bound_execute``'s legal write (one FK +
    a two-id list) under the per-field bound of two.
    """
    mutation = (
        "mutation S($d: ShelfAlt_ubranchesBranchCodeInput!) { createShelf(data: $d) "
        "{ result { code } errors { field messages } } }"
    )
    payload = _post(
        "/rp-values/",
        mutation,
        {"d": {"code": "RP-OK", "branchId": 1}},
    )
    _no_rejection(payload)


@pytest.mark.django_db
def test_a_deeply_nested_variable_value_is_bounded_by_value_depth():
    """The bound the pre-parse depth scan structurally cannot supply.

    ``max_depth`` counts brackets in the document TEXT; this document has three
    of them however deep its variable is. Without a value-depth bound a
    10,000-deep payload passes every document bound and every total, because
    each level is one node wide.
    """
    payload = {"and": [{"and": [{"name": {"exact": "x"}}]}]}
    extensions = _rejection(
        _post("/rp-value-depth/", _GENRE_FILTER, {"f": payload}),
    )
    assert extensions["bound"] == "max_value_depth"
    assert extensions["limit"] == MAX_VALUE_DEPTH


@pytest.mark.django_db
def test_a_shallow_variable_value_is_not_rejected_on_value_depth():
    _no_rejection(_post("/rp-value-depth/", _GENRE_FILTER, {"f": {"name": {"exact": "x"}}}))


@pytest.mark.django_db
def test_a_scalar_larger_than_the_byte_bound_is_rejected():
    mutation = (
        "mutation S($d: ShelfSerializerInput!) { createShelfViaSerializer(data: $d) "
        "{ result { code } errors { field messages } } }"
    )
    variables = {"d": {"code": "c" * (MAX_SCALAR_BYTES + 1), "branchId": 1}}
    extensions = _rejection(_post("/rp-values/", mutation, variables))
    assert extensions["bound"] == "max_scalar_bytes"
    assert extensions["charged"] == MAX_SCALAR_BYTES + 1


def test_an_inline_string_argument_is_bounded_by_scalar_bytes():
    """A string literal in the document is charged the same bound as a variable string."""
    name = "Q" * (MAX_SCALAR_BYTES + 1)
    extensions = _rejection(
        _post("/rp-values/", '{ __type(name: "%s") { name } }' % name),
    )
    assert extensions["bound"] == "max_scalar_bytes"
    assert extensions["charged"] == MAX_SCALAR_BYTES + 1


@pytest.mark.django_db
def test_total_input_nodes_are_bounded_across_several_arguments():
    """Several individually-legal arguments can still exhaust the request's node budget."""
    branches = ", ".join(
        '{ name: { exact: "x" }, id: { exact: "1" } }' for _ in range(MAX_CONTAINER_WIDTH)
    )
    query = "{ allLibraryGenres(filter: { or: [%s] }) { name } }" % branches
    extensions = _rejection(_post("/rp-values/", query))
    assert extensions["bound"] == "max_input_nodes"


# ---------------------------------------------------------------------------
# Uploads: the bytes the transport body cap deliberately never measures
# ---------------------------------------------------------------------------


_SPECIMEN = (
    "mutation M($d: MediaSpecimenInput!) { createMediaSpecimen(data: $d) "
    "{ result { label } errors { field messages } } }"
)


@pytest.mark.django_db
def test_an_oversized_upload_is_rejected_by_the_policy_not_by_the_body_cap():
    """The multipart body is never materialized by the transport cap, so this is the bound.

    ``MAX_REQUEST_BODY_BYTES`` deliberately does not measure a multipart body -
    reading it would defeat Django's streaming upload handlers - which is exactly
    why per-file and aggregate upload bytes are the resource policy's job.
    """
    res = TestClient().query(
        _SPECIMEN,
        variables={"d": {"label": "l", "attachment": None, "image": None}},
        files={
            "d.attachment": SimpleUploadedFile("attachment.bin", b"z" * 200),
            "d.image": SimpleUploadedFile("image.bin", b"z" * 200),
        },
        assert_no_errors=False,
        url="/rp-uploads/",
    )
    assert res.response.status_code == 200, res.response.content
    extensions = _rejection(res.response.json())
    assert extensions["bound"] in {
        "max_upload_count",
        "max_upload_file_bytes",
        "max_upload_total_bytes",
    }


# ---------------------------------------------------------------------------
# Collection bounds the fields enforce
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_argument_smaller_limit_serializes_subset_and_charges_full_collection_cost():
    """Client limit narrows serialized rows while collection cost charges full max_list_rows."""
    library_models.Branch.objects.create(name="B1", city="Boston")
    library_models.Branch.objects.create(name="B2", city="Boston")
    library_models.Branch.objects.create(name="B3", city="Boston")

    # 1. On /rp-rows/ (max_list_rows=3), client limit: 2 serializes exactly 2 rows
    payload = _post("/rp-rows/", "{ allLibraryBranchesViaListField(limit: 2) { name } }")
    _no_rejection(payload)
    assert len(payload["data"]["allLibraryBranchesViaListField"]) == 2

    # 2. On /rp-list-cost/ (max_list_rows=3, max_collection_cost=2), client limit: 1
    # is rejected because pre-execution collection cost charges max_list_rows (3),
    # not the client limit (1).
    cost_payload = _post(
        "/rp-list-cost/",
        "{ allLibraryBranchesViaListField(limit: 1) { name } }",
    )
    ext = _rejection(cost_payload)
    assert ext["bound"] == "max_collection_cost"
    assert ext["charged"] == MAX_LIST_ROWS
    assert ext["limit"] == MAX_LIST_ROWS - 1


def _seed_five_branches():
    """Seed five same-city branches - more rows than the narrowed policy ceiling.

    The count is what makes an at-ceiling page a real window rather than the whole
    table, so a page of ``MAX_LIST_ROWS`` proves the bound and not the row count.
    """
    return [
        library_models.Branch.objects.create(name=f"B{index}", city="Boston") for index in range(5)
    ]


@pytest.mark.django_db
def test_list_argument_limit_at_and_over_narrowed_policy_ceiling():
    """Client limit at policy ceiling succeeds; over ceiling reports narrowed bound."""
    _seed_five_branches()

    # limit == MAX_LIST_ROWS (3) succeeds
    payload_at = _post(
        "/rp-rows/",
        f"{{ allLibraryBranchesViaListField(limit: {MAX_LIST_ROWS}) {{ name }} }}",
    )
    _no_rejection(payload_at)
    assert len(payload_at["data"]["allLibraryBranchesViaListField"]) == MAX_LIST_ROWS

    # limit == MAX_LIST_ROWS + 1 (4) rejects with LIST_ARGUMENT_INVALID naming ceiling 3
    payload_over = _post(
        "/rp-rows/",
        f"{{ allLibraryBranchesViaListField(limit: {MAX_LIST_ROWS + 1}) {{ name }} }}",
    )
    assert payload_over["data"] is None
    assert "errors" in payload_over
    err = payload_over["errors"][0]
    assert err["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err["extensions"]["reason"] == "over_ceiling"
    assert err["extensions"]["argument"] == "limit"
    assert err["extensions"]["value"] == MAX_LIST_ROWS + 1
    assert err["extensions"]["ceiling"] == MAX_LIST_ROWS


@pytest.mark.django_db
def test_list_argument_offset_at_and_over_narrowed_policy_ceiling():
    """Ordered offset at policy ceiling succeeds; over ceiling reports narrowed bound."""
    create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    _seed_five_branches()

    # offset == MAX_LIST_ROWS (3) with active ordering succeeds
    payload_at = _post(
        "/rp-rows/",
        f"""
        query {{
          allLibraryBranchesViaListField(
            orderBy: [{{ name: ASC }}]
            offset: {MAX_LIST_ROWS}
          ) {{
            name
          }}
        }}
        """,
        client=client,
    )
    _no_rejection(payload_at)
    # 5 branches total, offset 3 leaves 2
    assert len(payload_at["data"]["allLibraryBranchesViaListField"]) == 2

    # offset == MAX_LIST_ROWS + 1 (4) rejects with LIST_ARGUMENT_INVALID naming ceiling 3
    payload_over = _post(
        "/rp-rows/",
        f"""
        query {{
          allLibraryBranchesViaListField(
            orderBy: [{{ name: ASC }}]
            offset: {MAX_LIST_ROWS + 1}
          ) {{
            name
          }}
        }}
        """,
        client=client,
    )
    assert payload_over["data"] is None
    assert "errors" in payload_over
    err = payload_over["errors"][0]
    assert err["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err["extensions"]["reason"] == "over_ceiling"
    assert err["extensions"]["argument"] == "offset"
    assert err["extensions"]["value"] == MAX_LIST_ROWS + 1
    assert err["extensions"]["ceiling"] == MAX_LIST_ROWS


@pytest.mark.django_db
def test_list_argument_rejections_and_limit_zero_perform_no_sql():
    """Argument refusal and limit: 0 perform zero row-fetching queries."""
    library_models.Branch.objects.create(name="B1", city="Boston")
    library_models.Branch.objects.create(name="B2", city="Boston")

    # 1. Negative limit rejection
    with CaptureQueriesContext(connection) as ctx:
        payload_neg = _post(
            "/rp-rows/",
            "{ allLibraryBranchesViaListField(limit: -1) { name } }",
        )
    assert "errors" in payload_neg
    assert payload_neg["data"] is None, payload_neg
    assert len(ctx.captured_queries) == 0

    # 2. Limit zero short-circuit
    with CaptureQueriesContext(connection) as ctx:
        payload_zero = _post(
            "/rp-rows/",
            "{ allLibraryBranchesViaListField(limit: 0) { name } }",
        )
    assert "errors" not in payload_zero, payload_zero
    assert payload_zero["data"]["allLibraryBranchesViaListField"] == []
    assert len(ctx.captured_queries) == 0


@pytest.mark.django_db
def test_a_raw_root_list_stops_at_the_configured_maximum():
    """``DjangoListField`` is bounded whether or not the field says anything."""
    seed_data(2)
    payload = _post("/rp-rows/", "{ allLibraryBranchesViaListField { name } }")
    _no_rejection(payload)
    assert len(payload["data"]["allLibraryBranchesViaListField"]) <= MAX_LIST_ROWS


@pytest.mark.django_db
def test_the_list_sibling_cannot_bypass_the_connection_page_cap():
    """The bypass S3 names, closed from both ends.

    ``CategoryType.items`` is an explicit ``"both"`` opt-in, so the raw list
    sibling still exists - and it is bounded by ``max_list_rows`` rather than
    being the unbounded escape hatch beside a capped ``itemsConnection``.
    """
    seed_data(3)
    payload = _post(
        "/rp-rows/",
        "{ allCategories(first: 2) { edges { node { items { name } } } } }",
    )
    _no_rejection(payload)
    for edge in payload["data"]["allCategories"]["edges"]:
        assert len(edge["node"]["items"]) <= MAX_LIST_ROWS


@pytest.mark.django_db
@override_settings(**_ERROR_POLICY_PASS_THROUGH)
def test_a_connection_page_larger_than_the_policy_is_refused():
    """The policy is a ceiling over ``relay_max_results``, never a replacement for it.

    The refusal here comes from Strawberry's own ``relay_max_results`` check, which
    raises a plain ``ValueError`` rather than a ``GraphQLError`` - so the spec-048
    error policy classifies it as unexpected and masks its wording, and the bound in
    that wording is exactly what this row reads to prove the ceiling was lowered.
    ``DEBUG=True`` opens the policy's pass-through gate so the live request returns
    the ceiling's own message. The instrument is the gate rather than
    ``error_policy={"enabled": False}`` because the mounts here come from one
    ``@cache``-d ``_probe_schema`` shared by the whole suite: an opt-out at
    construction would silently change every other row's response boundary too.
    """
    seed_data(1)
    payload = _post(
        "/rp-rows/",
        "{ allCategories(first: %d) { edges { node { name } } } }" % (MAX_PAGE_SIZE + 1),
    )
    assert payload["data"] is None
    assert "cannot be higher than %d" % MAX_PAGE_SIZE in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_the_connection_only_default_leaves_no_raw_list_sibling():
    """``CategoryType.properties`` declares nothing, so the SDL carries no list form.

    The live half of the ``DEFAULT_RELATION_SHAPE`` flip: the raw sibling is
    absent from the schema, not merely bounded, so there is nothing to select.
    """
    payload = _post(
        "/rp-rows/",
        "{ allCategories(first: 1) { edges { node { properties { id } } } } }",
    )
    assert payload["data"] is None
    assert "Cannot query field 'properties'" in payload["errors"][0]["message"]


# ---------------------------------------------------------------------------
# The cooperative deadline, at every seam that hands work to the database
# ---------------------------------------------------------------------------


def _deadline_rejection(payload):
    """Return the deadline rejection in ``payload``, asserting it is the only error.

    Separate from ``_rejection`` because a deadline fires from inside a resolver
    rather than before execution, so the envelope is graphql-core's own
    resolver-error shape: the typed error rides in ``errors`` and ``data`` is
    nulled by the non-null field it propagated through.
    """
    errors = payload["errors"]
    assert len(errors) == 1, errors
    extensions = errors[0]["extensions"]
    assert extensions["code"] == RESOURCE_LIMIT_ERROR_CODE, extensions
    assert extensions["bound"] == "execution_deadline_seconds", extensions
    return extensions


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_connection_before_it_reaches_the_database():
    """The connection seam: the head every ``resolve_connection`` shape passes through."""
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            "/rp-deadline/",
            "{ allCategories(first: 1) { edges { node { name } } } }",
        )
    extensions = _deadline_rejection(payload)
    assert extensions["limit"] == 1
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_raw_list_before_it_reaches_the_database():
    """The ``bounded_rows`` seam, shared by both raw-list spellings."""
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post("/rp-deadline/", "{ allLibraryBranchesViaListField { name } }")
    _deadline_rejection(payload)
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_relay_refetch_before_any_id_is_decoded():
    """The Relay refetch seam: a decode is what makes the query inevitable."""
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = _post("/rp-deadline/", _NODES, {"ids": ["x"]})
    _deadline_rejection(payload)
    assert captured.captured_queries == []


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_write_before_its_transaction_opens():
    """The write seam: refusing before ``transaction.atomic()`` leaves nothing to unwind."""
    mutation = (
        'mutation { createBookViaCustomInput(data: { title: "t", subtitle: "s", shelfId: 1 }) '
        "{ node { title } errors { field messages } } }"
    )
    payload = _post("/rp-deadline/", mutation)
    _deadline_rejection(payload)


@pytest.mark.django_db
def test_an_unarmed_deadline_never_rejects():
    """The default policy carries no deadline, so no seam may reject on one."""
    seed_data(1)
    _no_rejection(_post("/rp-rows/", "{ allLibraryBranchesViaListField { name } }"))


# ---------------------------------------------------------------------------
# Enforcement authority: what a resolver reaches through ``info.schema``
# ---------------------------------------------------------------------------


def test_a_bound_declared_by_an_entry_is_the_one_a_request_is_held_to():
    """An entry carrying a policy is a declaration, and the declaration is what bounds.

    Read once where it is accepted and folded into the schema's own record, so
    the operation is bounded by it while the object that declared it never
    reaches the chain - and the package defaults, which would pass all three
    rows, never answer a bound the deployment did configure.
    """
    payload = _post("/rp-entry-rows/", "{ rows }")
    _no_rejection(payload)
    assert payload["data"] == {"rows": ["a"]}


def test_a_resolver_cannot_widen_the_next_request_through_the_schema():
    """The budget survives a resolver writing both names it can reach.

    ``info.schema`` is handed to every resolver, and the schema outlives the
    request, so a policy held as an ordinary attribute is a process-lived
    widening primitive rather than a same-request one: the first request sets
    it, every later request on that worker runs under it. Emptying the extension
    list is the wider version of the same reach - the next operation would arm
    no budget at all. Both are written through ``__dict__``, which is the
    spelling that gets past an ordinary property. Two requests, in order, are
    what make the claim: the write happens in the first, and the second is the
    one that must still be bounded.
    """
    assert _post("/rp-authority/", "{ widen }")["data"] == {"widen": 1}

    second = _post("/rp-authority/", "{ rows }")
    _no_rejection(second)
    assert second["data"]["rows"] == ["a"]

    third = _post(
        "/rp-authority/",
        "query T($p: OpaqueValue) { take(payload: $p) }",
        {"p": list(range(MAX_CONTAINER_WIDTH + 1))},
    )
    assert _rejection(third)["bound"] == "max_container_width"


def test_a_resolver_cannot_nominate_a_new_policy_authority_over_the_wire():
    """Presence of an enforcement extension is not evidence that it was configured.

    A replacement list can carry an ordinary resource-policy extension with a
    wider policy of its own, which every presence and deduplication check
    accepts while the configured bound is gone for the life of the process. The
    assignment is refused where it is made, so the request that tried it fails
    and the next one is still held to what the deployment configured.
    """
    attacked = _post("/rp-authority/", "{ nominate }")
    assert attacked.get("errors")

    second = _post("/rp-authority/", "{ rows }")
    _no_rejection(second)
    assert second["data"]["rows"] == ["a"]


def test_two_schemas_that_compare_equal_bound_their_own_requests():
    """A request is held to ITS schema's policy, not to one that compares equal to it.

    Two mounts, two equal-but-distinct schemas, two different row bounds: a
    registry keyed by hash and equality would answer both requests with whichever
    schema was constructed last, and would drop the survivor's configuration when
    the other was collected.
    """
    narrow = _post("/rp-equal-narrow/", "{ rows }")
    _no_rejection(narrow)
    assert narrow["data"]["rows"] == ["a"]

    wide = _post("/rp-equal-wide/", "{ rows }")
    _no_rejection(wide)
    assert wide["data"]["rows"] == ["a", "b", "c"]

    assert _post("/rp-equal-narrow/", "{ rows }")["data"]["rows"] == ["a"]


def test_a_policy_the_deployment_still_holds_cannot_widen_a_later_request():
    """Configuration intake copies; the object a deployment keeps is not the authority.

    An exact policy instance used to pass through intake unchanged, so the
    reference a deployment kept - a module-level object, or one a resolver can
    reach through any import - was the object every bound was read from, and a
    frozen dataclass admits ``policy.__dict__[bound] = wider``.
    """
    first = _post("/rp-retained/", "{ rows }")
    _no_rejection(first)
    assert first["data"]["rows"] == ["a"]

    RETAINED_POLICY.__dict__["max_list_rows"] = 999
    try:
        second = _post("/rp-retained/", "{ rows }")
    finally:
        RETAINED_POLICY.__dict__["max_list_rows"] = 1
    _no_rejection(second)
    assert second["data"]["rows"] == ["a"]


def _opaque_request(source, width):
    """One request carrying ``width`` members to the scalar argument, by ``source``.

    The three places a value enters an operation. A supplied variable arrives
    beside the document; an inline literal and a variable definition's default
    arrive INSIDE it, and those two are the ones GraphQL's own validation parses
    through the argument's scalar before execution begins.
    """
    members = list(range(width))
    literal = "[" + ", ".join(str(member) for member in members) + "]"
    if source == "variable":
        return "query T($p: OpaqueValue) { take(payload: $p) }", {"p": members}, members
    if source == "literal":
        return f"{{ take(payload: {literal}) }}", None, members
    return f"query T($p: OpaqueValue = {literal}) {{ take(payload: $p) }}", None, members


@pytest.mark.parametrize(
    "source",
    ["variable", "literal", "default"],
    ids=["supplied-variable", "inline-literal", "variable-default"],
)
def test_a_scalar_argument_is_bounded_by_the_shape_the_request_carried(source):
    """The value budget charges the RAW argument, before any scalar converts it.

    The walk reads the variables the request supplied and the argument ASTs the
    document carries, so an argument typed by a custom scalar is measured as the
    JSON container the client sent. Charging it before VALIDATION is what makes
    that true of all three sources: graphql-core validates a literal by parsing
    it through the scalar it is typed as, so a budget that ran after validation
    would have let the parser do its work on an argument the request was going
    to be refused for.
    """
    _scalar_parses.clear()
    query, variables, _ = _opaque_request(source, MAX_CONTAINER_WIDTH + 1)
    payload = _post("/rp-authority/", query, variables)
    extensions = _rejection(payload)
    assert extensions["bound"] == "max_container_width"
    assert extensions["charged"] == MAX_CONTAINER_WIDTH + 1
    assert _scalar_parses == []


@pytest.mark.parametrize(
    "source",
    ["variable", "literal", "default"],
    ids=["supplied-variable", "inline-literal", "variable-default"],
)
def test_a_scalar_argument_within_the_bound_reaches_its_parser(source):
    """The control, and the other half of the boundary: an admitted argument converts.

    One member under the bound the same request runs, and the parser sees the
    raw container the budget already charged - which is what makes the empty
    parse log in the rejecting row mean refused-before-conversion rather than
    never-wired-up.
    """
    _scalar_parses.clear()
    query, variables, members = _opaque_request(source, MAX_CONTAINER_WIDTH)
    payload = _post("/rp-authority/", query, variables)
    _no_rejection(payload)
    assert payload["data"] == {"take": "ok"}
    assert _scalar_parses
    assert all(parsed == members for parsed in _scalar_parses)


def test_no_name_on_a_schema_answers_with_the_policy_enforcing_it():
    """The authority is not an attribute, asked by content rather than by name.

    A row naming the attribute it expects to be absent passes the moment that
    attribute is renamed, and detecting a forged one and then continuing under
    the fallback is not preservation either - the fallback may be wider than
    what the deployment configured. Nothing ``info.schema`` puts in reach is a
    policy or holds one, so there is nothing to forge.
    """
    payload = _post("/rp-census/", "{ reachableAuthorities }")
    _no_rejection(payload)
    assert payload["data"] == {"reachableAuthorities": []}


@pytest.mark.parametrize("attempt", ["before", "after"])
def test_a_resolver_cannot_put_raw_exception_text_on_the_wire(attempt):
    """The record that settles the budget settles masking, and neither is reachable.

    Under ``DEBUG=False`` an unexpected resolver exception reaches the client as
    the policy's stable message plus a correlation id. A resolver that could
    reach the accepted error policy would turn that off for every later request
    the process served, so the sentinel is looked for in the response BEFORE the
    attempt and in the one AFTER it.
    """
    if attempt == "after":
        assert _post("/rp-authority/", "{ unmask }")["data"] == {"unmask": []}

    payload = _post("/rp-authority/", "{ boom }")
    assert payload["data"] is None
    error = payload["errors"][0]
    assert UNMASKED_SENTINEL not in json.dumps(payload)
    assert error["message"] == DEFAULT_ERROR_POLICY.message
    assert error["extensions"][DEFAULT_ERROR_POLICY.correlation_extension_key]


@pytest.mark.parametrize(
    "mount",
    ["/rp-accepted-instance/", "/rp-inherited-instance/"],
    ids=["explicit-policy", "inherited-policy"],
)
def test_no_name_on_an_accepted_extension_answers_with_the_policy_it_enforces(mount):
    """The same question of the entry a schema was configured WITH.

    Both configurations of that entry are asked: one that carries a policy, and
    one that carries none and reads its schema's. Neither holds a policy under
    any name a resolver reaches.
    """
    payload = _post(mount, "{ reachableAuthorities }")
    _no_rejection(payload)
    assert payload["data"] == {"reachableAuthorities": []}


@pytest.mark.parametrize(
    ("mount", "field", "reported"),
    [
        ("/rp-authority/", "reconfigure", "ConfigurationError"),
        ("/rp-accepted-instance/", "reconfigure", "unreachable"),
        ("/rp-inherited-instance/", "reconfigure", "unreachable"),
    ],
    ids=["schema", "accepted-extension", "accepted-extension-inheriting"],
)
def test_rerunning_a_constructor_over_the_wire_does_not_widen_a_later_request(
    mount,
    field,
    reported,
):
    """An object a resolver reaches is one whose ``__init__`` a resolver can call.

    A second construction would settle a new ceiling for every later request the
    process serves, which is the widening no attribute write achieves. The
    schema is refused where the call is made; the extension that spends its
    policy is not an entry at all, so there is nothing for the resolver to
    reach and call. Either way the deployment's configuration is what still
    bounds the next request.

    The initial configuration is varied because an extension built with no
    override of its own is configured too - it enforces the policy its schema
    resolved - and both spellings have to answer the same way.
    """
    first = _post(mount, "{ rows }")
    _no_rejection(first)
    assert first["data"]["rows"] == ["a"]

    attacked = _post(mount, "{ %s }" % field)
    assert attacked["data"] == {field: reported}, attacked

    second = _post(mount, "{ rows }")
    _no_rejection(second)
    assert second["data"]["rows"] == ["a"]


@pytest.mark.parametrize(
    ("mount", "field", "written"),
    [
        ("/rp-emptied-entries/", "emptyTheEntries", ["_django_extensions"]),
        ("/rp-widened-entries/", "widenTheEntries", ["_django_extensions"]),
        ("/rp-rewritten-entries/", "rewriteBehindTheNames", []),
    ],
    ids=["empty-the-entries", "replace-the-entries", "rewrite-behind-the-names"],
)
def test_writing_the_accepted_extensions_does_not_choose_what_runs_the_next_request(
    mount,
    field,
    written,
):
    """Membership is what decides whether an operation is bounded and masked at all.

    Keeping the policy values private answers a different question: a resolver
    that cannot reach a bound can still aim at which extensions read one. Each
    row rewrites the membership a different way and then asks a LATER request
    what enforced it - the already-resolved chain of the attacking request is
    not the acceptance criterion - and the answer is the configuration
    construction accepted: the row bound the deployment chose, and an unexpected
    exception still reaching the client masked.
    """
    first = _post(mount, "{ rows }")
    _no_rejection(first)
    assert first["data"]["rows"] == ["a"]

    attacked = _post(mount, "{ %s }" % field)
    assert attacked["data"] == {field: written}, attacked

    second = _post(mount, "{ rows }")
    _no_rejection(second)
    assert second["data"]["rows"] == ["a"]

    masked = _post(mount, "{ boom }")
    assert masked["data"] is None
    assert UNMASKED_SENTINEL not in json.dumps(masked)
    assert masked["errors"][0]["message"] == DEFAULT_ERROR_POLICY.message
    assert masked["errors"][0]["extensions"][DEFAULT_ERROR_POLICY.correlation_extension_key]


def test_an_extension_factory_still_builds_one_per_operation():
    """Refusing a SECOND construction of one instance is not refusing construction.

    A factory entry is how a consumer gets an extension per operation, and it is
    called once per operation by design. Each request must still get an instance
    of its own while the schema's own bound goes on holding it.
    """
    before = _post("/rp-factory-entry/", "{ builds }")
    _no_rejection(before)

    bounded = _post("/rp-factory-entry/", "{ rows }")
    _no_rejection(bounded)
    assert bounded["data"]["rows"] == ["a"]

    after = _post("/rp-factory-entry/", "{ builds }")
    _no_rejection(after)
    assert after["data"]["builds"] > before["data"]["builds"]


@pytest.mark.parametrize(
    ("mount", "field"),
    [("/rp-forged-entries/", "forge"), ("/rp-dropped-entries/", "drop")],
    ids=["forge-the-accepted-entries", "delete-the-accepted-entries"],
)
def test_losing_the_accepted_extensions_does_not_widen_the_next_request(mount, field):
    """A bound is not held in anything a resolver can forge or delete.

    Every private name a schema carries is replaced with an empty value of the
    same shape, and then deleted outright. The bound the deployment configured
    is read from neither: it was taken as a declaration at construction and is
    held where no name on the schema answers with it, so the request after the
    write is bounded exactly as the request before it - not widened to the
    package default, which is three times wider here. Each row gets its own
    mount because whatever a write does to a schema stays done.
    """
    first = _post(mount, "{ rows }")
    _no_rejection(first)
    assert first["data"]["rows"] == ["a"]

    attacked = _post(mount, f"{{ {field} }}")
    assert attacked["data"] == {field: ["_django_extensions"]}, attacked

    second = _post(mount, "{ rows }")
    _no_rejection(second)
    assert second["data"]["rows"] == ["a"]


@pytest.mark.parametrize(
    ("field", "reported"),
    [("rebind", "unreachable"), ("overwrite", "unreachable"), ("emptyTheEntry", [])],
    ids=["rebind", "overwrite", "empty-the-instance-dictionary"],
)
def test_an_accepted_extension_instance_cannot_widen_a_later_request(field, reported):
    """A declaration is read once and does not travel, so there is nothing left to write.

    Strawberry hands back an accepted instance unchanged and
    ``info.schema.extensions`` puts it in front of every resolver, which is
    exactly why an entry of this kind is read as a policy declaration at
    construction and folded into the schema's own record. Every write spelling
    these rows aim at the object therefore finds no object to aim at, and the
    bound the deployment declared is what the next request is held to.
    """
    first = _post("/rp-accepted-instance/", "{ rows }")
    _no_rejection(first)
    assert first["data"]["rows"] == ["a"]

    attacked = _post("/rp-accepted-instance/", "{ %s }" % field)
    assert attacked["data"] == {field: reported}, attacked

    second = _post("/rp-accepted-instance/", "{ rows }")
    _no_rejection(second)
    assert second["data"]["rows"] == ["a"]


# ---------------------------------------------------------------------------
# Composition: admission and an installed validation extension
# ---------------------------------------------------------------------------

#: The two positions a consumer can give a validation extension relative to the
#: package's own, both of them supported configurations, plus the control.
CACHE_ORDERS = ["none", "cache-first", "cache-last"]

CACHE_ORDER_IDS = [
    "no-cache",
    "cache-before-the-automatic-entry",
    "explicit-entry-before-the-cache",
]


def _empty_validation_cache() -> None:
    """Empty the module-level store ``ValidationCache`` shares across schemas.

    The cache is keyed by its ``maxsize`` and lives in upstream's module, not on
    any schema, so "cold" is a state of the process rather than of the mount and
    naming a row cold proves nothing unless the row puts the process in it.
    """
    _get_validate_cache(None).cache_clear()


CACHE_MOUNTS = {
    "none": "/rp-cache-none/",
    "cache-first": "/rp-cache-first/",
    "cache-last": "/rp-cache-last/",
}


@pytest.mark.parametrize("order", CACHE_ORDERS, ids=CACHE_ORDER_IDS)
@pytest.mark.parametrize("cache_state", ["cold", "warm"])
def test_an_alias_rejection_survives_an_installed_validation_extension(order, cache_state):
    """A rejection is not the mutable field it is published in.

    A validation extension that runs the pass itself assigns its own result over
    ``pre_execution_errors``. The cache's store is module-level and shared by
    every schema that asks for the same size, so the two states are set up
    rather than named: cold is the store emptied immediately before the request,
    warm is the same request made twice. Aliases are charged from the document's
    shape alone, so this row needs no custom scalar at all - if the only witness
    were a scalar parser, a rejection erased for an ordinary document would have
    nothing to report it.
    """
    _empty_validation_cache()
    query = "{ a: rows b: rows }"
    if cache_state == "warm":
        _rejection(_post(CACHE_MOUNTS[order], query))
    extensions = _rejection(_post(CACHE_MOUNTS[order], query))
    assert extensions["bound"] == "max_aliases"
    assert extensions["limit"] == CACHE_ALIASES
    assert extensions["charged"] == CACHE_ALIASES + 1


@pytest.mark.parametrize("order", CACHE_ORDERS, ids=CACHE_ORDER_IDS)
@pytest.mark.parametrize(
    "source",
    ["variable", "literal", "default"],
    ids=["supplied-variable", "inline-literal", "variable-default"],
)
def test_an_over_bound_argument_is_refused_before_any_installed_validation_runs(order, source):
    """Admission precedes the validation stage, whatever position the consumer chose.

    An installed validation extension runs the pass itself, and that pass parses
    every inline literal and every variable default through the scalar it is
    typed as. Ordering the package's own entry earlier or later cannot fix that
    for both halves of the matrix, so admission is not in the chain at all: it
    charges once the document is parsed and before any validation hook is
    entered, and a refused document is one nothing validates.
    """
    _scalar_parses.clear()
    query, variables, _ = _opaque_request(source, MAX_CONTAINER_WIDTH + 1)
    extensions = _rejection(_post(CACHE_MOUNTS[order], query, variables))
    assert extensions["bound"] == "max_container_width"
    assert extensions["charged"] == MAX_CONTAINER_WIDTH + 1
    assert _scalar_parses == []


@pytest.mark.parametrize("order", CACHE_ORDERS, ids=CACHE_ORDER_IDS)
@pytest.mark.parametrize(
    "source",
    ["variable", "literal", "default"],
    ids=["supplied-variable", "inline-literal", "variable-default"],
)
def test_an_argument_within_the_bound_still_executes_beside_a_validation_extension(order, source):
    """The other verdict, which is what keeps the rejecting row from being vacuous."""
    _scalar_parses.clear()
    query, variables, members = _opaque_request(source, MAX_CONTAINER_WIDTH)
    payload = _post(CACHE_MOUNTS[order], query, variables)
    _no_rejection(payload)
    assert payload["data"] == {"take": "ok"}
    assert _scalar_parses
    assert all(parsed == members for parsed in _scalar_parses)


@pytest.mark.parametrize(
    "mount",
    ["/rp-witness-cache-first/", "/rp-witness-cache-last/", "/rp-witness-cache-last-async/"],
    ids=["cache-before-the-witness", "cache-after-the-witness", "cache-after-the-witness-async"],
)
@pytest.mark.parametrize("verdict", ["rejected", "admitted"])
def test_a_rejected_operation_never_enters_the_executing_stage(mount, verdict):
    """Asked from outside the guard, on a schema carrying a validation cache.

    Upstream decides whether to execute from inside the validation stage, so
    what that decision reads is whatever the LAST validation hook to set up
    left published - and the cache publishes its own result there. The
    difference between "nothing ran" and "something ran and was stopped on the
    way out" is visible only to an entry in the chain ahead of the package's
    own, which is what this one is. The admitted row keeps the witness honest.
    """
    _ExecutionWitness.entered.clear()
    query = "{ a: rows b: rows }" if verdict == "rejected" else "{ a: rows }"
    if mount.endswith("-async/"):
        response = _await_response(
            AsyncTestClient().query(query, assert_no_errors=False, url=mount),
        )
        payload = json.loads(response.response.content)
    else:
        payload = _post(mount, query)

    if verdict == "rejected":
        assert _rejection(payload)["bound"] == "max_aliases"
        assert _ExecutionWitness.entered == []
    else:
        _no_rejection(payload)
        assert payload["data"] == {"a": ["a", "b", "c"]}
        assert _ExecutionWitness.entered == [query]


@pytest.mark.parametrize("order", CACHE_ORDERS, ids=CACHE_ORDER_IDS)
def test_ordinary_validation_still_answers_beside_the_admission_stage(order):
    """Admission stands down a document's validation only when it refused it.

    Emptying an admitted operation's validation rules would turn every schema
    carrying a cache into one that accepts nonsense, so the row an unknown field
    fails on is the control for the mechanism the refusing rows rely on.
    """
    payload = _post(CACHE_MOUNTS[order], "{ nosuchfield }")
    _no_rejection(payload)
    assert payload["data"] is None
    assert "nosuchfield" in payload["errors"][0]["message"]


@pytest.mark.parametrize(
    ("order", "mount"),
    [("cache-first", "/rp-cache-first-async/"), ("cache-last", "/rp-cache-last-async/")],
    ids=["cache-before-its-neighbour", "cache-after-its-neighbour"],
)
def test_the_composed_admission_stage_answers_the_same_on_the_async_transport(order, mount):
    """One verdict per request, whichever transport carried it."""
    _scalar_parses.clear()
    query, variables, _ = _opaque_request("literal", MAX_CONTAINER_WIDTH + 1)
    sync_extensions = _rejection(_post(CACHE_MOUNTS[order], query, variables))

    _scalar_parses.clear()
    response = _await_response(
        AsyncTestClient().query(
            query,
            variables=variables,
            assert_no_errors=False,
            url=mount,
        ),
    )
    assert _rejection(json.loads(response.response.content)) == sync_extensions
    assert _scalar_parses == []


def _seed_hostile_relation() -> None:
    """One patron with four loans, so a ceiling of one cannot be mistaken for the data."""
    branch = library_models.Branch.objects.create(name="hostile-branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="hostile-shelf")
    patron = library_models.Patron.objects.create(name="hostile-patron")
    for index in range(4):
        book = library_models.Book.objects.create(shelf=shelf, title=f"hostile-{index}")
        library_models.Loan.objects.create(book=book, patron=patron, note=f"loan-{index}")


_HOSTILE_RELATION_QUERY = "{ patrons { name loans { note } } }"


@pytest.mark.django_db
def test_a_relation_manager_cannot_widen_the_raw_list_bound_with_its_own_slice():
    """The many-side relation is bounded by what the package slices, not by the source.

    The generated ``loans`` resolver hands its source straight to the raw-list
    bound, and that source is whatever the relation manager returned. A manager
    returning a ``QuerySet`` subclass used to put the ceiling in that subclass's
    ``__getitem__``, so four related rows came back through a real request under
    a bound of one.
    """
    _seed_hostile_relation()
    with _hostile_relation_manager():
        payload = _post("/rp-hostile-relation/", _HOSTILE_RELATION_QUERY)
    _no_rejection(payload)
    assert payload["data"] == {
        "patrons": [
            {"name": "hostile-patron", "loans": [{"note": "loan-0"}]},
        ],
    }
    assert len(payload["data"]["patrons"][0]["loans"]) == HOSTILE_RELATION_ROWS


@pytest.mark.django_db
def test_an_ordinary_relation_manager_is_bounded_the_same_way():
    """The control: the same mount, the same document, Django's own manager.

    Without it the row above would prove only that something rejected four rows,
    not that the bound is the thing doing it.
    """
    _seed_hostile_relation()
    payload = _post("/rp-hostile-relation/", _HOSTILE_RELATION_QUERY)
    _no_rejection(payload)
    assert payload["data"] == {
        "patrons": [
            {"name": "hostile-patron", "loans": [{"note": "loan-0"}]},
        ],
    }


@pytest.mark.django_db(transaction=True)
def test_a_relation_manager_cannot_widen_the_raw_list_bound_on_the_async_transport():
    """Sync/async parity: the awaited relation branch is bounded by the same seam.

    The async many-side branch iterates the bound asynchronously instead of
    calling ``list(...)``, so it reaches the row source through its own call and
    owes its own proof.
    """
    _seed_hostile_relation()
    with _hostile_relation_manager():
        response = _await_response(
            AsyncTestClient().query(
                _HOSTILE_RELATION_QUERY,
                assert_no_errors=False,
                url="/rp-hostile-relation-async/",
            ),
        )
    payload = json.loads(response.response.content)
    _no_rejection(payload)
    assert payload["data"] == {
        "patrons": [
            {"name": "hostile-patron", "loans": [{"note": "loan-0"}]},
        ],
    }
    assert len(payload["data"]["patrons"][0]["loans"]) == HOSTILE_RELATION_ROWS


def _seed_carry_relation(patrons: int, loans_each: int) -> None:
    """``patrons`` patrons with ``loans_each`` loans apiece, over one shelf."""
    branch = library_models.Branch.objects.create(name="carry-branch")
    shelf = library_models.Shelf.objects.create(branch=branch, code="carry-shelf")
    for patron_index in range(patrons):
        patron = library_models.Patron.objects.create(name=f"carry-patron-{patron_index}")
        for loan_index in range(loans_each):
            book = library_models.Book.objects.create(
                shelf=shelf,
                title=f"carry-{patron_index}-{loan_index}",
            )
            library_models.Loan.objects.create(
                book=book,
                patron=patron,
                note=f"loan-{patron_index}-{loan_index}",
            )


CARRY_RELATION_LOANS = 3


def _carry_relation_payload(patrons: int) -> dict:
    """The response the public ``LoanQuerySet.as_manager()`` relation must produce."""
    return {
        "patrons": [
            {
                "name": f"carry-patron-{patron_index}",
                "loans": [
                    {"note": f"loan-{patron_index}-{loan_index}"}
                    for loan_index in range(CARRY_RELATION_LOANS)
                ],
            }
            for patron_index in range(patrons)
        ],
    }


@pytest.mark.django_db
@pytest.mark.parametrize("patrons", [2, 3], ids=["two-parents", "three-parents"])
def test_a_project_queryset_class_relation_costs_two_prefetch_queries(patrons):
    """The real project manager is windowed from the rows prefetch already fetched.

    Two parent cardinalities pin batching rather than merely one request's shape:
    the absolute number is one parent query plus one prefetch, and the payload
    comparison stops a cheaper count from meaning fewer rows.
    """
    _seed_carry_relation(patrons, CARRY_RELATION_LOANS)
    expected = _carry_relation_payload(patrons)

    with CaptureQueriesContext(connection) as query_ctx:
        payload = _post("/rp-carry-relation/", _HOSTILE_RELATION_QUERY)

    _no_rejection(payload)
    assert payload["data"] == expected
    assert len(query_ctx.captured_queries) == CARRY_RELATION_QUERIES


@pytest.mark.django_db(transaction=True)
def test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited():
    """Sync/async parity for the rebuilt relation source.

    Rows rather than a query count: ``CaptureQueriesContext`` binds to the
    calling thread's connection while the async branch runs its ORM work in
    ``sync_to_async`` worker threads, so an empty capture here would read exactly
    like a green zero. The payload cannot be produced without the relation's rows.
    """
    _seed_carry_relation(2, CARRY_RELATION_LOANS)
    response = _await_response(
        AsyncTestClient().query(
            _HOSTILE_RELATION_QUERY,
            assert_no_errors=False,
            url="/rp-carry-relation-async/",
        ),
    )
    payload = json.loads(response.response.content)
    _no_rejection(payload)
    assert payload["data"] == _carry_relation_payload(2)


@pytest.mark.django_db
def test_a_bound_at_the_representable_maximum_reaches_the_database():
    """The largest configurable bound has to work as a real ``LIMIT``.

    A bound is handed to the backend's adapter, which binds it as an integer of
    the backend's own width, so the top of the accepted domain is only the top
    if a request configured there executes. The row runs against whichever
    backend the suite is running on, so the sqlite tier and the Postgres tier
    each prove it for themselves.

    ``max_collection_cost`` is raised with it because the pre-execution cost
    charge is ``max_list_rows`` itself: left at its default, the request is
    refused by the cost bound before it can say anything about the row bound.
    """
    seed_data(2)
    payload = _post("/rp-max-bound/", "{ allLibraryBranchesViaListField { name } }")
    _no_rejection(payload)
    assert payload["data"]["allLibraryBranchesViaListField"] is not None


# ---------------------------------------------------------------------------
# Cross-cutting: one typed code on both transports
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_and_async_transports_share_one_typed_error_code():
    """The rejection is a ``GraphQLError``, so no transport translates it.

    Sync and async mounts of the package view must answer with the same code,
    the same bound, and the same charge - a per-transport difference here would
    mean a client cannot recognize the failure without knowing its transport.
    """
    variables = {"ids": ["x"] * (MAX_NODE_IDS + 1)}
    sync_extensions = _rejection(_post("/rp-values/", _NODES, variables))

    async_response = _await_response(
        AsyncTestClient().query(
            _NODES,
            variables=variables,
            assert_no_errors=False,
            url="/rp-values-async/",
        ),
    )
    async_payload = json.loads(async_response.response.content)
    assert _rejection(async_payload) == sync_extensions


def _await_response(coroutine):
    """Run one ``AsyncTestClient.query`` coroutine to completion on a fresh event loop."""
    import asyncio

    return asyncio.run(_resolve(coroutine))


async def _resolve(coroutine):
    return await coroutine


def _entry_request(entry, query):
    """POST one document to a shared-entry mount through that entry's own view color.

    ``entry`` is the ``(spelling, color)`` key rather than the mount, because the
    mount is display text ``ENTRY_MOUNTS`` derives from that key: reading the color
    back out of the URL would route an async mount through the synchronous client
    the moment the mount naming changes, and the row would still pass.
    """
    _, color = entry
    mount = ENTRY_MOUNTS[entry]
    if color == "async":
        response = _await_response(
            AsyncTestClient().query(query, assert_no_errors=False, url=mount),
        )
        return json.loads(response.response.content)
    return _post(mount, query)


@pytest.mark.parametrize(
    ("spelling", "color"),
    ENTRY_ROWS,
    ids=ENTRY_IDS,
)
def test_an_overlapping_request_does_not_admit_an_oversized_one(spelling, color):
    """Whichever object a consumer entry resolves to, the charge lands on its own document.

    Strawberry resolves a class and a fresh factory into a new extension per
    operation, and passes an instance and a singleton-returning factory through
    as ONE object every operation shares. The engine assigns
    ``execution_context`` on whatever it resolved, so for the shared pair a
    second request's assignment is a write onto the object the first request is
    still running through - and an enforcing hook reading its request off a
    shared entry would read the second request's benign document.

    The oversized request is held open between its parse hooks, the benign one
    runs to completion, and only then is the first released. The rejection has
    to be identical to the one the same document gets with no overlap at all,
    and the executing stage has to have been entered for the benign document
    alone.
    """
    entry = (spelling, color)
    oversized = "{ a: rows b: rows }"
    benign = "{ rows }"

    _ExecutionWitness.entered.clear()
    alone = _rejection(_entry_request(entry, oversized))
    assert alone["bound"] == "max_aliases"
    assert alone["limit"] == ENTRY_ALIASES
    assert _ExecutionWitness.entered == []

    _OverlapCoordinator.parked.clear()
    _OverlapCoordinator.released.clear()
    _OverlapCoordinator.armed = True
    overlapped = {}

    def _run_oversized():
        overlapped["payload"] = _entry_request(entry, oversized)

    held = threading.Thread(target=_run_oversized)
    held.start()
    try:
        assert _OverlapCoordinator.parked.wait(timeout=10), "the oversized request never parked"
        benign_payload = _entry_request(entry, benign)
    finally:
        _OverlapCoordinator.released.set()
        held.join(timeout=10)
        _OverlapCoordinator.armed = False

    _no_rejection(benign_payload)
    assert benign_payload["data"] == {"rows": ["a", "b", "c"]}
    assert _rejection(overlapped["payload"]) == alone
    assert _ExecutionWitness.entered == [benign]

    _ExecutionWitness.entered.clear()
    assert _rejection(_entry_request(entry, oversized)) == alone
    assert _ExecutionWitness.entered == []
