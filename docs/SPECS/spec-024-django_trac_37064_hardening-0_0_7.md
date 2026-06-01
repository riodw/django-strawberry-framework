# Spec: Django Trac #37064 hardening + `safe_wrap_connection_method`

Target release: `0.0.7` (per [KANBAN.md][kanban] card `DONE-024-0.0.7`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

This file is intentionally lightweight. It preserves the card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository file. Before implementation work starts from this file, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

## Card snapshot

- Card: `DONE-024-0.0.7`
- Status: `done` / Done
- Milestone: `alpha` / Alpha (pre-0.1.0)
- Priority: Low
- Severity: Low
- Planning state: Shipped
- Relative size: S
- Labels: `django-integration`, `hardening`

## Planning note

shipped

## Other

- defensive hardening unique to this package; neither upstream ships a Django Trac #37064 patch.
- two-half defense for Trac #37064: a package-level unwrap patch (auto-applied at app-load) plus the cooperative `safe_wrap_connection_method` helper + tests.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
