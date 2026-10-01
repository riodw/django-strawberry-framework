# Rationale: spec-006 — Public surface & documentation discipline (deliberation, rejected alternatives)

Deliberative companion to [`spec-006-public_surface-0_0_3.md`][spec-006]. The spec is the contract;
this file records why its rules have the shape they have. The spec has no numbered Decisions, so each
entry is keyed to a spec section.

## Why discipline rather than more documentation

Spec: [Problem statement][spec-006-problem].

The public surface goes wrong when a name, a document, and a test disagree about whether something
works. Condition 1 of the re-export rule says "effective end-to-end" rather than "exists" because a
headline feature can be importable while half-built, and an importable name reads as shipped.

## Why the roster lives in three artifacts, not this spec

Spec: [Where the public surface is defined][spec-006-surface] and [Decision for 0.0.3][spec-006-decision].

`__all__` is the surface, `tests/base/test_init.py::test_public_api_surface_is_pinned` pins it
verbatim, and `docs/GLOSSARY.md` `## Public exports` documents it. A copy of the tuple in a spec reads
as the current surface whatever surrounds it, and goes stale on the next promotion; the decision for
the optimizer names what was promoted and why, and points at where the tuple is pinned.

## Why the four conditions are necessary but not sufficient

Spec: [Top-level re-export rule][spec-006-reexport] and
[When a subsystem is top-level vs subpackage-only][spec-006-subsystem].

Several shipped, tested, documented, stable families stay out of the root namespace because for them
the import path is the consumer's opt-in: an optional distribution, `django.contrib.auth` machinery,
or a diagnostic surface unsafe to leave on. The rule therefore states necessity, and the boundary rule
places the sufficiency call with the spec that ships the subsystem.

- **Keep a biconditional and list the families as exceptions.** Rejected: they are not exceptions
  but the outcome of a rule each owning spec applied on purpose, and an exception list that grows
  with every subsystem is not a gate. Naming them here would also pull other specs' placement
  decisions into this document.
- **Enumerate the families that keep their subpackage path.** Rejected: the glossary documents each
  with its import path; a register here goes stale on the next one.
- **Why the dotted path is described two ways.** For a name that failed a condition it is a fallback;
  for a boundary family it is the contract. The import form cannot tell them apart, only the owning
  spec can.

## Why status is published per entry, from generated documents

Spec: [How status is published][spec-006-readme] and [Status-marker vocabulary][spec-006-vocabulary].

A status marker on every entry makes a section boundary that encodes the same status redundant, and a
redundant boundary is a second place for the fact to go stale. The markers live in `docs/GLOSSARY.md`
and `docs/TREE.md`, both rendered from a database, so a marker cannot disagree with the record behind
it; onboarding prose points at them instead of carrying markers of its own.

- **A `Current` / `Planned` / `Not implemented yet` README sectioning.** Rejected: the third section
  duplicates the second once markers are in place, and hand-kept sections drift where generated
  per-entry markers cannot.
- **Restate the marker vocabulary here.** Rejected: `docs/GLOSSARY.md` `## Status legend` renders
  from the same database as the markers it explains, so it is the single source; a copy here decays
  the moment the rendered one moves.
- **Why two legend properties are restated.** A marker names a release, and condition 3 reads that
  stamp; a marker attaches to an entry, which is the argument against sectioning. Changing either
  changes this spec's gate.

## Why the signaling rules use patterns, not named features

Spec: [Alpha signaling rules][spec-006-signaling].

An example of hedged language whose subject later ships teaches the opposite of the rule. The rules
are stated as language patterns (present tense for `shipped`, hedged and release-named for unshipped,
both halves for `alpha constraint`), which cannot ship and so cannot rot.

## Why a subsystem spec's obligations are discharged against artifacts

Spec: [What a subsystem spec owes these rules][spec-006-owes].

An obligation to come back and edit this document leaves no trace when skipped, so nothing can check
it. Each obligation a subsystem spec owes (a published marker, a pinning test and export pin, a stated
placement decision, a new marker in the legend) lands in its own change against an artifact something
already checks.

- **Keep an amendment obligation and add a compliance check.** Rejected: the only enforcement would
  be another rule an author must remember, the same failure one level up.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-006]: ../spec-006-public_surface-0_0_3.md
[spec-006-decision]: ../spec-006-public_surface-0_0_3.md#decision-for-003
[spec-006-owes]: ../spec-006-public_surface-0_0_3.md#what-a-subsystem-spec-owes-these-rules
[spec-006-problem]: ../spec-006-public_surface-0_0_3.md#problem-statement
[spec-006-readme]: ../spec-006-public_surface-0_0_3.md#how-status-is-published
[spec-006-reexport]: ../spec-006-public_surface-0_0_3.md#top-level-re-export-rule
[spec-006-signaling]: ../spec-006-public_surface-0_0_3.md#alpha-signaling-rules
[spec-006-subsystem]: ../spec-006-public_surface-0_0_3.md#when-a-subsystem-is-top-level-vs-subpackage-only
[spec-006-surface]: ../spec-006-public_surface-0_0_3.md#where-the-public-surface-is-defined
[spec-006-vocabulary]: ../spec-006-public_surface-0_0_3.md#status-marker-vocabulary

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
