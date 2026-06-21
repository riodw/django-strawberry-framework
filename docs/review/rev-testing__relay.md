# Review: `django_strawberry_framework/testing/relay.py`

Status: verified

## DRY analysis

- None — the module is the consumer-facing thin shell over already-single-sourced
  internals: `decode_global_id` is a verbatim re-export of
  `django_strawberry_framework/types/relay.py::decode_global_id` (one import, no
  re-implementation), and `global_id_for` reuses the live encode path
  (`types/relay.py::encode_typename`), the live gate constants
  (`types/base.py::_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` /
  `STRING_GLOBALID_STRATEGIES`), and the canonical `ConfigurationError` rather
  than re-spelling any of them. There is no second call site to consolidate
  against — minting through `encode_typename` is exactly what makes the helper
  consistent-by-construction with live emission.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `global_id_for` (`testing/relay.py::global_id_for`)
  mints the payload through `types/relay.py::encode_typename` — the exact slot
  computation the installed `resolve_typename` closure runs — so the helper
  cannot drift from live emission. It reuses the shared gate constants
  `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` and the
  `STRING_GLOBALID_STRATEGIES` frozenset from `types/base.py:107,113,122`
  (the same constants the Phase-2.5 validator and connection/relation-shape
  gates use), and raises the canonical `exceptions.ConfigurationError`.
  `decode_global_id` is re-exported verbatim from
  `types/relay.py::decode_global_id` (`testing/relay.py:45`) — same source as the
  package-root `relay.py:65` consumer, so the public contract is single-sourced.
- **New helpers considered.** None needed. The encode payload path is a single
  `encode_typename(definition, strategy, type_cls, None, None)` call; the
  `root`/`info` arguments are passed as `None` and the inline comment
  (`testing/relay.py #"never touch"`) correctly notes the string-strategy
  branches of `encode_typename` (`types/relay.py:479-482`) never read them —
  only the `callable` branch does, and that branch is gated out one block
  earlier. No wrapper would simplify the single call.
- **Duplication risk in the current file.** The repeated `"global_id_for:"`
  literal (4x, the static overview's lone repeated literal) is the message
  prefix on each distinct `ConfigurationError` raise; the rest of each message
  differs and names the specific failure mode. Hoisting the prefix to a constant
  would hurt grep-ability of the raise sites and is not a real consolidation.

### Other positives

- **Gate ordering is correct and load-bearing.** `global_id_for` checks
  `definition is None` → not finalized → `strategy is None` → strategy not in
  `STRING_GLOBALID_STRATEGIES`, in that order. The `finalized` gate precedes the
  strategy read deliberately: the strategy stamp is written in Phase 2.5 *before*
  Phase 3 flips `finalized`, so a partial-finalize failure can leave a non-`None`
  strategy on an unfinalized type; reading the stamp first would mint an id in
  violation of the "finalized Relay-Node-shaped type" contract. The inline
  comment (`testing/relay.py #"Gate on"`) documents exactly this and matches the
  re-entrancy reasoning in `types/relay.py::install_globalid_typename_resolver`
  (the step-0 guard, `types/relay.py:545-553`).
- **Reads the stamped strategy, never the setting.** `global_id_for` reads
  `definition.effective_globalid_strategy` (the finalize-frozen value,
  `types/definition.py:179`) rather than `RELAY_GLOBALID_STRATEGY` — so the
  minted id matches what the type actually emits even when a per-type
  `Meta.globalid_strategy` overrides the schema default.
- **`callable`/`custom` fail loud, not silently wrong.** Both fall outside
  `STRING_GLOBALID_STRATEGIES` (`{"model", "type", "type+model"}`) and raise a
  `ConfigurationError` explaining the encoder needs a live `(root, info)` the
  helper cannot supply — the honest contract boundary, not a best-effort guess.
- **Strategy-aware encoding matches live emission, verified at source.**
  `encode_typename` (`types/relay.py:470-482`): `model` / `type+model` (members of
  `MODEL_LABEL_STRATEGIES`, `types/relay.py:402`) → `definition.model._meta.label_lower`;
  `type` → `definition.graphql_type_name`. This is byte-identical to the docstring's
  promised payload mapping and to the slot the installed closure emits.
- **Asymmetry contract documented, not papered over.** The module docstring
  states `decode_global_id(global_id_for(T, pk)) == (T, str(pk))` holds only for
  lone/primary model-label types and `type`-strategy payloads, because a
  secondary model-label emitter's payload decodes to the model's *primary* via
  `registry.get(model)`. Confirmed against `decode_global_id` Step 1
  (`types/relay.py:707` `registry.get(model)`) — this is the same routing a live
  `node(id:)` performs, correctly framed as expected behavior rather than a bug.
- **Import-cost framing accurate.** Keeping the helpers out of `testing/__init__.py`
  (whose `__all__` is `["safe_wrap_connection_method"]` only) keeps
  `import django_strawberry_framework.testing` light; the `types`-package imports
  are paid only by suites importing the submodule. The `testing/__init__`
  docstring and `docs/GLOSSARY.md:53` both state the submodule path is the public
  entry "by design" — consistent across module, package init, and GLOSSARY.

### Summary

Public consumer test-helper module: `global_id_for(type_cls, id)` mints the
strategy-aware encoded `GlobalID` a finalized Relay-Node type emits, and
`decode_global_id` is a verbatim re-export of the internal decode dispatch. Both
diffs against the per-cycle baseline (`f2365341`) and against HEAD are empty; the
file last changed in `6148d3f1` (cumulative-in-HEAD). The strategy-aware
encoding was verified against `types/relay.py::encode_typename` and
`MODEL_LABEL_STRATEGIES` (model/type+model → model label, type → graphql type
name) — it matches what the live closure emits. The re-export shares its source
with the package-root consumer. The `GLOSSARY` entry is contract-level and
accurate (no drift); private gate constants and `encode_typename` carry no
GLOSSARY entry, which is correct. No High, Medium, or Low findings. Zero edits to
any tracked file → no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged`.
- `uv run ruff check --fix .` — `All checks passed!`.

### Notes for Worker 3
- Both `git diff f23653415f65ebb7e84240d81cf25977683dca66 -- django_strawberry_framework/testing/relay.py`
  and `git diff HEAD -- django_strawberry_framework/testing/relay.py` are empty;
  the file last changed in `6148d3f1` (cumulative-in-HEAD). Dirty working-tree
  files are `docs/review/*`, `docs/dry/*`, `docs/feedback2.md`, and `docs/spec-*`
  scratchpads only — out of scope per AGENTS.md #34.
- No High / no behavior-changing Medium / no Low findings.
- No GLOSSARY-only fix in scope: `docs/GLOSSARY.md:53` carries a contract-level
  entry for `global_id_for` / `decode_global_id` ("mint and decode the
  strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits …
  NOT re-exported from the `testing` root, by design"). Verified accurate against
  source — the strategy-aware encode (`encode_typename`), the re-export source,
  and the non-re-export from `testing/__init__.py` (`__all__ =
  ["safe_wrap_connection_method"]`) all match. The private gate constants
  (`_RELAY_NODE_GATE_*`, `STRING_GLOBALID_STRATEGIES`) and `encode_typename`
  carry no GLOSSARY entry — absence correct (internal/no `__all__`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits. The module docstring, the `global_id_for`
docstring, and the inline gate/encode comments were each cross-checked against
source and are accurate: the Phase-2.5-before-Phase-3 finalized-gate reasoning
matches `install_globalid_typename_resolver`; the "string-strategy branches never
touch root/info" comment matches `encode_typename:479-482`; the asymmetry
contract matches `decode_global_id` Step 1's `registry.get(model)` routing.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edits this cycle (AGENTS.md: "Do not update
CHANGELOG.md unless explicitly instructed"), and the active plan
(`docs/review/review-0_0_11.md`) records no changelog action for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to address — genuine no-source-edit (shape #5)
cycle. Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle
pattern.` as the shape gate requires. Independently confirmed the `None.`
findings genuine:

- **Mint path matches live emission.** `global_id_for`
  (`testing/relay.py::global_id_for`) calls
  `encode_typename(definition, strategy, type_cls, None, None)` — the exact
  per-strategy slot computation `_install_typename_closure`'s installed closure
  runs (`types/relay.py::_install_typename_closure` calls
  `encode_typename(definition, strategy, cls, root, info)`). Verified against
  source: `model` / `type+model` ∈ `MODEL_LABEL_STRATEGIES`
  (`types/relay.py:402`) → `definition.model._meta.label_lower`; `type` →
  `definition.graphql_type_name` (`types/relay.py:479-482`). The `None`/`None`
  `root`/`info` are safe — only the `callable` branch reads them and it is gated
  out earlier (`strategy not in STRING_GLOBALID_STRATEGIES` raise).
- **Gate ordering is sound.** `finalized` checked before the strategy read; the
  strategy stamp (`effective_globalid_strategy`, `types/definition.py:179`,
  default `None`) is written in Phase 2.5 before Phase 3 flips `finalized`
  (`types/definition.py:180`), so a partial-finalize could leave a non-`None`
  strategy on an unfinalized type — reading the stamp first would mint in
  violation of the contract. Pinned by
  `test_global_id_for_strategy_stamped_but_unfinalized_raises`.
- **Gate constants single-sourced.** `_RELAY_NODE_GATE_LEAD` /
  `_RELAY_NODE_GATE_INHERIT_TAIL` / `STRING_GLOBALID_STRATEGIES` are imported
  from `types/base.py:107,113,122` (the same constants the connection / relation
  gates use, `base.py:219,271`) — no re-spelling.
- **`decode_global_id` is a verbatim re-export.** Imported from
  `types/relay.py::decode_global_id` (`testing/relay.py:45`) — the same source
  the package-root consumer imports (`relay.py:65`
  `from .types.relay import _NODE_TYPE_HINT_ATTR, decode_global_id`). Single
  source, no re-implementation.

### DRY findings disposition
DRY-None genuine: the module is the consumer-facing thin shell — one re-export,
one reuse of the live encode path plus shared gate constants and canonical
`ConfigurationError`. No second mint call site exists to consolidate against;
minting through `encode_typename` is what makes the helper
consistent-by-construction with live emission. The repeated `"global_id_for:"`
prefix (4x) is a per-raise message prefix whose hoisting would hurt grep-ability
of the raise sites — correctly not a consolidation.

### Temp test verification
- None used. Confirmed via existing focused suite.

### Verification outcome
`cycle accepted; verified`. Sets top-level `Status: verified` and marks the
`testing/relay.py` checkbox in `docs/review/review-0_0_11.md`.

Zero-edit proof: `git diff f23653415f65ebb7e84240d81cf25977683dca66 --
django_strawberry_framework/testing/relay.py` AND `git diff HEAD --` both empty;
owned-paths `--stat` vs baseline
(`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty; the
file last changed in `6148d3f1` (cumulative-in-HEAD). Dirty working tree is
`docs/review/*`, `docs/dry/*`, `docs/feedback2.md`, `docs/spec-038-*` only —
out-of-scope scratchpads per AGENTS.md #34, no sibling-cycle attribution needed.

GLOSSARY: `docs/GLOSSARY.md:53` carries a contract-level entry for
`global_id_for` / `decode_global_id` ("mint and decode the strategy-aware
encoded `GlobalID` a finalized Relay-Node-shaped type emits … NOT re-exported
from the `testing` root, by design"). Verified accurate vs live source — the
strategy-aware encode, the re-export source, and the non-re-export from
`testing/__init__.py` (`__all__ = ["safe_wrap_connection_method"]`) all match.
Private gate constants and `encode_typename` carry no GLOSSARY entry (absence
correct — internal). Genuine #5, not a missed #4.

Focused suite: `uv run pytest tests/testing/test_relay.py -q` → 10 passed (the
coverage FAIL is the expected single-file-run artifact, not a test failure). The
suite pins both halves of the contract: model/type/type+model mint, callable /
custom / unfinalized / non-Node / strategy-stamped-but-unfinalized raises, the
primary round-trip, and the secondary→primary decode asymmetry.

Changelog: `Not warranted`, cites both AGENTS.md and the active plan's silence
— `git diff -- CHANGELOG.md` empty. Cycle is internal-only (no public-API
surface change this cycle), so "Not warranted" is the correct state.

---

## Iteration log
