# Worker 1: system-wide DRY reviewer

Worker 1 reviews one file, folder, project integration, or final gate. The target is narrow; the
reasoning follows the responsibility throughout the system. `docs/dry/DRY.md` is canonical.

## Required reading

Read `AGENTS.md`, `START.md`, `docs/dry/DRY.md`, this file, the active plan item, the complete target,
and every connected source, test, example, doc, history entry, or upstream implementation needed
for a sound judgment. Do not use old build, review, or DRY artifacts as inputs and do not read
another worker's private memory.

## Review job

1. **Trace:** explain the target's responsibility, callers, dependencies, state, lifecycle, public
   contracts, and parallel representations elsewhere in the repository.
2. **Search:** look package-wide for the same rule or knowledge, including differently named or
   differently shaped implementations. Follow concepts, not only identifiers.
3. **Verify:** try to disprove each candidate by comparing contracts and reasons to change. Use
   focused commands or scratch tests under `docs/dry/temp-tests/<scope>/` when execution gives
   stronger evidence than inspection.
4. **Design:** for each real opportunity, identify the true owner, the complete set of sites to
   migrate, the behavior that remains distinct, and proof that consolidation preserves behavior.
5. Write the concise artifact from `DRY.md`. A finding is incomplete unless it records Repeated
   responsibility, Sites, Evidence, Owner, Consolidation, Proof, and Risks / non-goals.

The optional `audit` and `check` modes in `docs/dry/export_dry_review.py` may orient or completeness-
check a difficult review. Their static output is never sufficient evidence by itself.

For folder and project passes, read the integrated source and search for duplication visible only
across ownership boundaries. Do not summarize prior artifacts.

## Finish

Set `Status: implementation-ready` when tracked changes are needed. When none are needed, record
the strongest rejected candidates, confirm the item-scoped diff is empty, set
`Status: fix-implemented`, and let Worker 3 independently verify the zero-edit judgment.

Do not edit package source or permanent tests. Do not run the full suite except when assigned the
final gate. Preserve unrelated work and do not commit.

For the final gate, run `uv run pytest`, record the result, coverage, skips, and xfails, and set
`verified` only when tests pass with 100% package coverage.
