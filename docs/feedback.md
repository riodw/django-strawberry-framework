# Review — spec-031 GlobalID encoding, fix-verification pass (`django_strawberry_framework/` only)

Second pass over the package source after the fix commit
(`356e6709`). Every prior finding was re-verified against the working tree;
the P1 fix was **re-reproduced with the same script shapes** that demonstrated
the bug, plus the two new shapes the fix introduces. No P1 or P2 findings
remain — three P3 residuals below.

## Prior findings — all verified fixed

| # | Was | Verdict | Evidence |
| - | --- | --- | --- |
| 1 | P1 inherited-closure misclassification | **FIXED** (root-cause, as recommended) | See behavioral re-verification below |
| 2 | P2 raw `spec-027 L<NN>` line refs in rewritten docstrings | **FIXED** | All `L<NN>` refs in `filters/base.py` replaced with `#"unique substring"` pinpoints; zero raw line refs remain in any spec-031-touched file |
| 3 | P3 `docs/feedback.md` citations in spec-031 files | **FIXED (one straggler — see residual 1)** | `types/relay.py`, `types/base.py`, `types/definition.py`, `types/finalizer.py`, `filters/base.py` all cleaned; spec-Decision halves retained |
| 4 | P3 stale `TODO(spec-027 Slice 1)` anchor | **FIXED** | Anchor + pseudocode block deleted from `types/relay.py` |
| 5 | P3 routing-audit remediation impossible for a non-Relay primary | **FIXED** | `_format_model_label_routing_error` branches the fix sentence on `strategy is None` (both branches kept grep-stable); `test_routing_audit_non_relay_primary_remediation_names_relay_shape` pins it |
| 6 | P3 `encode_typename` `type` branch production-dead | **FIXED** (retired by the P1 fix, as predicted) | The `type` branch is now the live implementation for the inherited-closure shadow case; docstring updated to say so |

### P1 fix — behavioral re-verification (script run against the working tree)

The implemented fix is exactly the recommended root-cause shape:
`_FRAMEWORK_CLOSURE_MARKER` stamped on the closure function in
`_install_typename_closure` (surviving `classmethod.__func__` retrieval),
`_consumer_overrode_resolve_typename` returning False for marked functions,
and `install_globalid_typename_resolver` installing the type's **own** closure
for the `type` classification when `_inherits_framework_closure(type_cls)` —
so an inherited parent closure (which captured the parent's `definition`) can
never keep shadowing Strawberry's default.

```text
1 parent: model | child: model | child own closure: True        (was: child "custom", no own closure)
2 finalize OK   | child: type+model                              (was: spurious both-declared ConfigurationError)
3 child effective: type | own closure: True | emits: TypeChild   (shadow case: emits own GraphQL name, not parent label)
4 abstract-override child: custom                                (consumer override semantics preserved)
```

The grandchild chain also holds by construction: a `type` child's own closure
carries the marker, so a grandchild sees a framework closure (not a consumer
override) and installs its own — the discrimination is transitive.

New package tests cover all the review-requested cases:
`test_concrete_relay_child_of_concrete_parent_records_own_strategy`,
`test_concrete_relay_child_with_meta_strategy_finalizes_cleanly`,
`test_type_strategy_child_shadows_inherited_framework_closure`,
`test_routing_audit_sees_child_true_recorded_strategy`,
`test_routing_audit_non_relay_primary_remediation_names_relay_shape`, and the
defensive `test_plain_function_resolve_typename_is_not_classified_override`.
Placement in `tests/types/test_relay_interfaces.py` is correct per AGENTS —
registry-lifecycle shapes are unreachable from a live query.

Hygiene: `ruff check` and `ruff format --check` pass clean over the package
(the COM812 formatter-conflict warning is pre-existing config, not this
change).

---

## Residual findings (all P3)

### P3 — One `docs/feedback.md` citation straggler in a spec-031 file

`registry.py::definition_for_graphql_name #"(``docs/feedback.md`` P1)"` — the
helper is new spec-031 code and was in scope for the citation sweep, but this
one docstring kept its feedback half. Drop it; the surrounding sentence
already cites the durable rule ("Keyed on `definition.graphql_type_name` …
NOT `type_cls.__name__`"), and spec-031 Decision 8 owns it. (The
`registry.py::TypeRegistry.clear #"P3b"` citation and the ones in
`connection.py` / `list_field.py` / `optimizer/extension.py` / `orders/` are
spec-030-era pre-existing — sweep candidates, unchanged, still out of this
card's obligation.)

### P3 — Two replacement pinpoint anchors are not unique in spec-027

The AGENTS source-ref rule prescribes `#"unique substring"`. Of the six new
pinpoints in `filters/base.py`, four are unique in
`docs/SPECS/spec-027-filters-0_0_8.md`, but two are not:

- `#"GlobalID type mismatch"` — 4 occurrences.
- `#"offending index named in the error"` — 2 occurrences.

They still land a reader in the right neighborhood, but they don't satisfy the
rule's letter and an ambiguous pinpoint degrades exactly like a line number
under future spec edits. Lengthen each to a unique span (e.g. extend
`#"GlobalID type mismatch"` with the adjacent words from the one sentence that
defines the error contract, and pick the spec's normative sentence for the
index-named-in-error contract rather than the recap that repeats it).

### P3 — spec-031 Decision 10 now lags the shipped behavior

The fix is better than the spec: Decision 10 still says the framework
"installs **nothing** for `type`" unconditionally and describes the override
test as the bare `__func__` identity check. The shipped code adds the
`_FRAMEWORK_CLOSURE_MARKER` sentinel, the marked-closure exclusion in
`_consumer_overrode_resolve_typename`, and the `type`-classification
shadow-install. Per the repo's spec-as-contract-record discipline (every prior
behavior delta got a Revision entry), add a Revision 6 entry + a Decision 10
amendment recording the marker mechanism and the shadow-install before Slice 5
closes the card — otherwise the card ships with its contract record
contradicting the implementation on the exact seam the last review fixed.

---

## Summary

| # | Sev | Area | One-line |
| - | --- | --- | --- |
| 1 | P3 | registry | Drop the lone remaining `docs/feedback.md` citation from `definition_for_graphql_name`'s docstring |
| 2 | P3 | filters | Lengthen the two non-unique spec-027 pinpoints (`#"GlobalID type mismatch"` ×4, `#"offending index named in the error"` ×2) to unique spans |
| 3 | P3 | docs | Amend spec-031 Decision 10 (+ Revision 6 entry) with the marker sentinel and the `type` shadow-install so the contract record matches shipped behavior |

Nothing here blocks the card. The P1 surface — classification, decode, audit,
and filter all reading one recorded strategy — is now consistent end-to-end,
including under concrete-inheritance and finalize-re-run composition.

## Validation

- Re-ran the prior P1 reproduction shapes plus the two fix-introduced shapes
  (`type` shadow-install; abstract-base consumer override) via a standalone
  script against fakeshop models; output quoted above; script removed.
- Confirmed zero raw `L<NN>` refs and zero `docs/feedback.md` citations in the
  spec-031-touched files except the one registry straggler named above.
- Verified all six new spec-027 pinpoint substrings against
  `docs/SPECS/spec-027-filters-0_0_8.md` (four unique, two ambiguous — residual 2).
- `uv run ruff check` / `uv run ruff format --check` over the package: clean.
- No package file was modified by this review; pytest not run per AGENTS.
