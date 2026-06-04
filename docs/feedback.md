# Feedback

Review target: `docs/spec-029-consumer_dx_cleanup-0_0_9.md`.

Stopped after the first actionable issue found.

## Finding

### P2 - Slice 1 still has stale migration language after the Decision 3 reversal

Revision 2 correctly changes Slice 1 from "migrate `extensions=[DjangoOptimizerExtension()]` to
class/factory form" to "keep the instance form because the plan cache is instance-bound." But the
spec still has old migration wording in the top glossary/dependency framing. In Key glossary
references, the `DjangoOptimizerExtension` bullet says Slice 1 "migrates" instance-form
construction to the factory-callable form, and the `DjangoConnectionField` dependency bullet says
the factory-callable migration should land before connection-field surfaces ship.

Those statements now contradict Decision 3 and the Slice checklist. They should be rewritten to say
Slice 1 documents and preserves the instance form for `DjangoOptimizerExtension`, while any
class/factory migration is deferred until the plan cache is relocated off the extension instance.

Affected spec sections: Key glossary references; dependency and forward-composition surfaces.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
