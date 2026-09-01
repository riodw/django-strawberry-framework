"""Planned live async-HTTP contract for ``DjangoListField`` (spec-050 Slice 4).

This suite is intentionally exempt from ``examples/fakeshop/graphql_client.py``:
that helper is synchronous by construction, while these cases must cross a real
``AsyncClient`` -> ``AsyncDjangoGraphQLView`` -> graphql-core async-completion
boundary. The exemption is local to this module and must be added to the live-tier
README when the tests land.

No case may set ``DJANGO_ALLOW_ASYNC_UNSAFE``. The suite exists to prove that a
final lazy queryset is represented by the package's async-only completion adapter
instead of being synchronously iterated inside the event loop.
"""

# TODO(spec-050 slice 4): Replace this planning-only module with the async live
# suite after Slices 1-3 land. Use only already-registered fakeshop DjangoTypes;
# throwaway DjangoType declarations would mutate the registry and fail the
# acceptance conftest's identity guard.
#
# Pseudocode - shared mount and isolation:
#
# - Import app types inside the schema-building fixture after
#   ``_reload_project_schema_for_acceptance_tests``. Keep one module-level schema
#   holder, one ``AsyncDjangoGraphQLView`` callable, and one urlpatterns entry.
# - Implement ``_post_async(schema, query, variables=None)`` with
#   ``AsyncClient.post`` under ``override_settings(ROOT_URLCONF=__name__)``.
#   Set the holder immediately before the request and clear it plus Django URL
#   caches in ``finally``.
# - Seed library rows in sync helpers using inline ``Model.objects.create(...)``
#   and enter them through ``sync_to_async``. Every test carries
#   ``@pytest.mark.django_db(transaction=True)``; none imports product seed
#   helpers unless that test genuinely creates product models too.
# - Build schema variants with and without ``DjangoOptimizerExtension`` and with
#   default/snake/custom naming configs. Declare only test-local root fields over
#   the apps' already-finalized types.
#
# Pseudocode - queryset completion and pipeline parity:
#
# - Exercise the default resolver, a CONFORMING LAZY sync consumer returning
#   Manager, the same returning QuerySet, and an ``async def`` consumer
#   returning QuerySet. "Conforming lazy" is load-bearing: the adapter removes
#   only the framework's own final iteration and cannot make an EVALUATING sync
#   resolver safe, so no case may assert that it does. For each, request an
#   ordered offset/limit page and assert exact data with no
#   ``SynchronousOnlyOperation`` and no unsafe env escape hatch.
# - Repeat the final queryset case with optimizer off and on. Data must match;
#   the package tier separately inspects adapter identity and inner slice marks
#   because worker-thread SQL capture cannot prove root planning.
# - Under the async wrapper, use the existing BranchType visibility hook plus
#   the public async OrderSet path to record visibility -> order -> window.
#   Assert a restricted row is removed before the offset and that order denial
#   serializes before the offset guard; do not mutate a registered type merely
#   to turn its otherwise-valid sync visibility hook into ``async def``.
# - Preserve nullable None and materialized-list shapes under limit/zero offset.
#   Supplying orderBy to either non-queryset shape yields ``queryset_required``;
#   nonzero offset yields ``order_required`` without attempting sync ORM work.
#
# Pseudocode - async-only iterables and cleanup:
#
# - Return an async generator directly and from a plain sync resolver. Every
#   LIVE success case here is LIMIT-ONLY or ``offset: 0``: the public field
#   rejects positive offset on an async-only source (spec-050 Decision 8), so a
#   live accepted-offset case would contradict the decision rather than exercise
#   it. Its accepted arithmetic is pinned in tests/test_resource_policy.py.
#   Assert the limit consumes exactly the accepted window, completion serializes
#   a list, and the generator's body ``finally`` witness runs on the accepted
#   stop -- valid ONLY here, because the generator has been advanced at least
#   once.
# - Two DIFFERENT facts, never conflated. "``aclose()`` was invoked" needs a
#   custom async iterator whose own ``aclose`` increments a counter; that is
#   what the limit-zero and pre-bound-rejection rows assert, beside zero
#   ``__anext__`` calls. "The generator BODY finalized" needs a real async
#   generator and at least one prior advance: ``aclose()`` on an unstarted async
#   generator does not enter the body, so neither its setup nor its ``finally``
#   runs, and advancing it to observe one would destroy the zero-consumption
#   guarantee the row exists to prove. Each test's name and docstring says which
#   fact it asserts.
# - For natural exhaustion before the stop, assert the source's explicit
#   ``aclose`` witness is NOT invoked.
# - Supply orderBy or nonzero offset to an async-only source. Assert zero
#   advancement, one close, and the exact ``LIST_ARGUMENT_INVALID`` reason.
#   Do NOT assert ``BaseException.__notes__`` content here: the production
#   GraphQL JSON envelope does not serialize notes. Live asserts the complete
#   public extensions map and that a cleanup failure did not displace the
#   primary domain error; exact note content and precedence stay package-tier.
#
# Pseudocode - naming and error transport:
#
# - Introspect/query the default, ``auto_camel_case=False``, and custom converter
#   schemas. For negative/over-cap/order/queryset errors, assert ``argument`` is
#   the active wire spelling selected from the real Strawberry argument
#   definition, not the helper fallback.
# - Pair every payload assertion with HTTP 200, exact ``data`` nullability, and
#   the complete error extension map; a bare ``errors`` truthiness assertion is
#   insufficient because it would also accept validation or event-loop crashes.
#
# Pseudocode - generated bookkeeping after the suite replaces this stub:
#
# - Once this path is in the git index, run the tracked-path constants builder;
#   do not hand-edit ``apps/kanban/constants.py``. Regenerate ``docs/TREE.md``
#   in Slice 5, and update the KANBAN/glossary databases through their owning
#   workflows rather than patching their generated Markdown exports.
