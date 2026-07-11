"""Planning anchors for spec-044 DjangoDebugExtension mechanics tests."""

# TODO(spec-044 Slice 1): Replace these anchors after implementing the leaf.
# Do not run pytest unless the maintainer explicitly asks.
#
# Test construction rules:
# - Import private helpers only to isolate mechanics that HTTP cannot force.
# - Use real GraphQLError, ExecutionResult, Strawberry Schema/MaskErrors, real
#   database wrappers, and a real bounded deque wherever practical.
# - Fake only the private acquisition boundary needed to force partial setup
#   failure; never mock Strawberry's extension runner.
# - Parametrize truly identical bodies: prior flag False/True, serializer row
#   forms, both masking orders, both async completion orders, and repeated
#   get_results calls. Keep materially different setup in separate tests.
# - Re-spell wire keys and the 10-second threshold as independent literals.
#   Never build expected values through production serializers or import the
#   production threshold into assertions.
#
# Serializer/collector pseudocode:
# 1. Exception serialization:
#    - hand-raise an exception so it owns a real traceback
#    - assert excType == "<class 'ValueError'>", exact message, and stack
#      includes "Traceback" plus the raise site
# 2. SQL serialization:
#    - parametrically cover SELECT, non-SELECT, and
#      "3 times: INSERT ..." executemany entries
#    - assert duration string converts to float
#    - assert isSlow is False at 10.0 and True only above 10.0
#    - assert isSelect uses stripped, case-insensitive SELECT prefix
#    - assert executemany SQL remains verbatim and isSelect is False
# 3. original_error collection:
#    - result None and errors None each return []
#    - pure validation GraphQLError (original_error None) is skipped
#    - wrapped Python exception serializes its terminal original
#    - explicitly raised nested GraphQLError remains represented
#    - malformed original_error cycles terminate without hanging
#    - multiple qualifying errors preserve result order and are not deduped
#
# Coordinator/log-slice pseudocode:
# 4. Saved-value restore:
#    - acquire the same real wrapper with force_debug_cursor initially False
#      and True in separate parameter rows
#    - first acquire sets True, second acquire reaches depth 2
#    - release in both orders; first release keeps True/depth 1
#    - final release restores the exact initial value and deletes the map key
#    - assert map keys are concrete wrappers, not aliases
# 5. Distinct wrapper isolation:
#    - acquire two concrete wrappers representing the same alias in separate
#      local contexts/threads
#    - assert independent entries and restoration
# 6. Partial setup unwind:
#    - let first alias acquire successfully and force the second acquisition
#      to raise at the private boundary
#    - assert ExitStack restored the first alias and the active map is empty
# 7. Query-log slicing:
#    - append rows after a retained start length and assert only the suffix
#    - shorten the deque below the snapshot and assert []
#    - fill/roll a bounded deque and pin only the documented best-effort
#      behavior; do not claim exact rows survive rollover
#
# Extension lifecycle pseudocode:
# 8. No-stash and pure get_results:
#    - zero-argument DjangoDebugExtension() succeeds; do not pass an execution
#      context into construction
#    - fresh instance returns {}, never {"debug": None}
#    - assign a completed payload and call get_results twice
#    - assert equal results and unchanged payload identity/content
#    - assert json.dumps succeeds
# 9. Real conditional double-call recovery:
#    - instrument a tiny extension/get_results call counter
#    - drive a validation-failure operation whose on_operation teardown raises
#      after the early return evaluated _handle_execution_result
#    - assert one call for the abandoned early result and one for the recovery
#      result
#    - separately prove a generic recovery path does not automatically imply
#      two calls
# 10. Result absence on pre-execution failure:
#     - parse and validation failures leave the debug key absent
#     - an executed no-op produces both empty lists
# 11. MaskErrors ordering with real extensions:
#     - [MaskErrors, DjangoDebugExtension] yields masked GraphQL errors while
#       debug captures the original exception
#     - reversed order yields debug.exceptions == []
#
# Merge/result-map pseudocode:
# 12. Extension-list precedence:
#     - two tiny extensions publish the same key with distinct markers
#     - direct sync and async schema execution each keep the later-listed
#       extension value
# 13. Async context-result precedence:
#     - seed ExecutionContext.extensions_results with a colliding marker
#       through a small real extension/hook
#     - assert async runner overlays it after extension outputs
#     - assert the sync runner has no equivalent overlay
# 14. Existing result-map replacement:
#     - return/prepopulate an ExecutionResult.extensions sentinel before
#       schema result handling
#     - assert the completed extension map replaces it rather than merging
#
# Concurrency/attribution pseudocode:
# 15. Async shared-wrapper overlap:
#     - materialize every tested connections[alias] in the parent async
#       context before creating either task and record object identities
#     - create two schema.execute tasks so both inherit those wrappers
#     - inside each operation assert wrapper identity equals the parent object
#     - synchronize raising async resolvers until coordinator depth is 2
#     - release in both completion orders
#     - assert each response has only its own exception marker
#     - assert final depth zero, active map empty, and every saved flag restored
#     - assert only SQL list type, never async SQL contents
# 16. Nested/reentrant same-thread attribution:
#     - outer sync resolver executes an inner sync schema operation using the
#       same concrete wrapper and query log
#     - assert coordinator depth/restoration remains correct
#     - assert inner payload owns its interval
#     - assert outer payload intentionally also includes inner SQL rows
# 17. Concurrent sync instance isolation at the dependency floor:
#     - one schema with the debug class executes two distinguishable blocking
#       resolvers in a ThreadPoolExecutor behind one barrier/event helper
#     - assert each response contains only its own exception/query marker
#     - assert each thread-local wrapper restores its flag
#     - record the exact node id so maintainers can run this same test in an
#       isolated strawberry-graphql==0.316.0 environment
#     - state explicitly: distinct executor-thread wrappers prove fresh
#       extension instances, not same-wrapper coordinator refcounting
#
# Coverage/command handoff:
# - Every production branch must map to a named assertion above, including
#   both saved flag directions, depth decrement/delete, result/errors None,
#   error-chain cycle stop, shorter log clamp, empty/populated stash, async
#   overlay, and masking order.
# - Record for the maintainer:
#     uv run pytest tests/extensions/test_debug.py
#     uv run pytest examples/fakeshop/test_query/test_debug_extension_api.py
