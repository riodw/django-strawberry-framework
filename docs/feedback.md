# Permissions Subsystem Specification Review (`0.0.10`)

I have conducted a rigorous review of `docs/spec-034-permissions-0_0_10.md` and the associated companion CSV `docs/spec-034-permissions-0_0_10-terms.csv`. The design is solid, heavily referencing upstream behaviors accurately, and successfully addressing edge cases like N+1 queries, async contexts, and cycle detection. 

Below are the findings, categorized by severity, intended to tighten the specification before execution.

## High Priority (Requires Change)

*   **H1: Absolute Local File Path in Reference Links**
    *   **Location**: `docs/spec-034-permissions-0_0_10.md` (Lines 78 and 632)
    *   **Issue**: The `[upstream-permissions]` link definition points to a hardcoded local absolute path (`/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/permissions.py`). This breaks portability and will fail for other developers, in CI environments, or on GitHub. 
    *   **Recommendation**: Replace the absolute path with a URL to the external repository's file on GitHub or a generic representation if a direct URL is unavailable. 

## Medium Priority (Edge Cases & Contract Clarifications)

*   **M1: Sliced Target Querysets in Subqueries**
    *   **Location**: `docs/spec-034-permissions-0_0_10.md` (Decision 5, Step 4 & Edge cases and constraints)
    *   **Issue**: The cascade injects `target_qs` into an `__in` subquery (`Q(fk__in=target_qs)`). If a consumer's `get_queryset` hook returns a sliced queryset (e.g., `queryset[:10]`), Django will raise a `NotSupportedError` upon evaluation because `LIMIT` is generally not supported inside `IN` subqueries by most SQL dialects.
    *   **Recommendation**: Add a bullet under the "Edge cases and constraints" section explicitly stating that a consumer's `get_queryset` must not return a sliced queryset when used with `apply_cascade_permissions`, as it breaks Django's `__in` subquery compilation.

## Low Priority (Refinements)

*   **L1: Explicit Acknowledgment of `asgiref` ContextVar Propagation**
    *   **Location**: `docs/spec-034-permissions-0_0_10.md` (Decision 10 & Edge cases and constraints)
    *   **Issue**: The async variant uses `sync_to_async(thread_sensitive=True)`. The `ContextVar` cycle guard functions safely across this async-to-sync boundary *only* because Django's `asgiref` library actively propagates context variables into the thread pool. 
    *   **Recommendation**: It may be worth adding a brief parenthetical note in Decision 10 or the cycle-guard edge case that the request isolation relies on `asgiref`'s thread context propagation.

## Endorsements (Technically Sound Behaviors)

*   **Cycle Guard Resolution**: The module-level `ContextVar` implementation (installing at the root call, cleaning up in a `finally` block, and discarding on frame exit) is a highly robust and elegant way to solve mutual cascade loops (`A <-> B`) without blocking sibling fields from evaluating. 
*   **Database Routing (`.using(queryset.db)`)**: Ensuring that `target_qs` binds to the caller's resolved alias is a precise and necessary constraint to prevent cross-database join errors in Django. The explicit fallback awareness is extremely accurate. 
*   **Zero Added Round-Trips**: The subquery composition (`fk__in=...`) safely leverages Django's lazy evaluation, meaning it evaluates in a single pass without eager materialization.

**Conclusion**: The spec is extremely thorough. Aside from the hardcoded path (H1), the implementation plan is ready to execute with minor documentation updates for constraint awareness (M1).
