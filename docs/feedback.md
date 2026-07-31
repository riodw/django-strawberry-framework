# Adversarial review: spec-046 transport security

Reviewed the shipped implementation in `django_strawberry_framework/` against
[spec-046][spec-046] and the package/live transport tests. The major transport
boundaries are present and fail closed in the ordinary request shapes: Django
owns HTTP, the cap runs before parsing, JSON and multipart control fields have
the documented UTF-8 policy, and WebSocket Host/Origin/revalidation wrappers
are composed in the intended order.

## Findings

### [P2] Numeric subclasses can escape the typed configuration boundary

`django_strawberry_framework/consumers.py::resolved_revalidation_window` accepts
any `isinstance(value, (int, float))` value and then calls its overridable
`__float__`. Likewise,
`django_strawberry_framework/views.py::_resolved_max_request_body_bytes` calls
the overridable comparison `value <= 0` after accepting an `int` subclass.
Those operations are outside the error boundary. A consumer can reproduce the
leak without touching the network:

```python
class BadFloat(float):
    def __float__(self):
        raise RuntimeError("configuration hook")

class BadInt(int):
    def __le__(self, other):
        raise RuntimeError("configuration hook")
```

Passing `BadFloat(1)` to `resolved_revalidation_window` raises the raw
`RuntimeError`; passing `BadInt(1)` to `_resolved_max_request_body_bytes` does
the same. The documented contract is a construction/request-boundary
`ConfigurationError` for an unusable value, so a hostile or merely surprising
settings object can instead abort router construction or view dispatch with an
unrelated exception. This is fail-closed for authorization, but it is still a
broken public error contract and makes invalid deployment configuration harder
to diagnose.

The root fix is to reject only the supported built-in numeric types (while
keeping the explicit `bool` rejection), or to guard every user-defined numeric
conversion/comparison with `except Exception` and raise the existing typed
error with the original exception chained. Add rows for a float subclass whose
conversion raises and an int subclass whose validation comparison raises; both
must produce `ConfigurationError` rather than a raw exception.

### [P2] The default outbound revalidation path has unbounded per-connection head-of-line blocking

`django_strawberry_framework/consumers.py::send_revalidated_operation_frame`
holds the connection lock across `_actor_is_current` and the actual send. With
the default `websocket_revalidation_window=0.0`, every `next`, `data`, or
operation-scoped `error` frame performs a session-store/user lookup while all
other protected operations on that socket wait. A slow session backend, a
database pool exhaustion event, or a stuck synchronous adapter therefore pins
every active operation task on that connection behind one read; there is no
timeout or bounded latency at this boundary.

The serialization is deliberate and is required to prevent a validated sibling
from sending after revocation, so this is not a request to release the lock
early. It is an unresolved availability budget: the spec calls the path a hot
path, but the implementation has no measured latency/throughput budget or
explicit timeout/failure policy for a stalled store. Record a benchmark or an
explicit maintainer waiver, and decide whether a bounded, fail-closed session
read timeout belongs in the transport contract before treating this slice as
fully risk-closed.

## Deliberate risks checked and not raised as defects

- Multipart POSTs without a trustworthy declaration remain bounded only by
  Django's multipart/upload settings and the deployment proxy/server cap. The
  spec explicitly makes those co-requirements; the package must not materialize
  multipart bodies just to impose a second cap.
- Revocation is event-boundary-driven and does not poll idle sockets. The first
  later operation or information-bearing frame is revalidated and closes the
  connection; idle lifetime is intentionally deployment-owned.
- The body probe relies on Django/Python stream `read(size)` semantics. Its
  production WSGI/ASGI streams honor that contract, and the code correctly
  distinguishes safely unmeasurable from position-corrupted streams. A stream
  implementation that violates the standard read contract would invalidate any
  application-level byte bound, which is a deployment prerequisite rather than
  a new HTTP parser branch.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[spec-046]: spec-046-transport_security-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
