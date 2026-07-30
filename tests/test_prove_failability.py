"""Script tests for the failability-proof runner's refusals and restore proof.

The runner writes to tracked production source, so the boundaries worth pinning
are the ones that stop it writing the wrong thing or leaving a mutation behind:
the exactly-once anchor, the inside-the-repo target check, the outside-the-repo
scratch check, the scope that may neither turn coverage on nor stop the run
early, the label that may not name a file other than the mutated one, the
restore proved by byte comparison, the acceptance rule that turns a row count
into a verdict, and the labelling that stops a narrowed (``--only``) run's
report from reading like a complete one.

One class of defect has recurred here more than any other: **the emitted record
reads more complete, or more true, than the run actually was** - a missing
baseline, an error-bearing run, a narrowed run, an unexplained zero, a pytest
exit code nothing read, manifest prose rendered instead of the bytes it claims
to describe, a record that never named the file the bytes went to while its
free-text label named a different one, and a scope whose own truncation made the
recorded count a count of other rows. The rows below pin each instance, and
``test_every_captured_field_of_a_run_outcome_is_load_bearing_in_the_record``
pins the shape rather than one instance of it.

``REPO_ROOT`` is monkeypatched to a ``tmp_path`` fake repo (as
``tests/test_clean_up.py`` does) and ``_run_scope`` is stubbed, so no test here
mutates a real file or spawns a real pytest.
"""

import dataclasses
import json

import pytest

from scripts import prove_failability

SOURCE = """def gate(value):
    if value is None:
        raise ValueError("no")
    return value
"""
ANCHOR = '    if value is None:\n        raise ValueError("no")'


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "package").mkdir(parents=True)
    target = repo / "package" / "views.py"
    target.write_text(SOURCE, encoding="utf-8")
    monkeypatch.setattr(prove_failability, "REPO_ROOT", repo)
    return repo


@pytest.fixture
def scratch_root(tmp_path):
    root = tmp_path / "scratch"
    (root / prove_failability.PRISTINE_DIRECTORY_NAME).mkdir(parents=True)
    return root


def _stub_run(
    monkeypatch,
    failed=(),
    errored=(),
    summary="stubbed",
    code=1,
    baseline_failed=(),
    baseline_errored=(),
    baseline_code=None,
    first_call_is_baseline=True,
):
    """Stub ``_run_scope``: the first call is the baseline, every later one the mutant.

    The baseline run is the default, so a stub that returned the mutant's failure
    set for both calls would difference the count to zero and pin nothing. Pass
    ``first_call_is_baseline=False`` for the ``--no-baseline`` path, where the only
    run there is *is* the mutant's.

    ``code`` and ``baseline_code`` are the two runs' pytest exit codes, which are
    a validity channel and not a diagnostic: ``baseline_code`` defaults to the
    code a real pytest would return for the stubbed failure set.
    """
    outcomes = []

    def fake_run_scope(entry):
        outcomes.append(entry)
        if first_call_is_baseline and len(outcomes) == 1:
            return prove_failability.RunOutcome(
                failed_node_ids=tuple(baseline_failed),
                error_node_ids=tuple(baseline_errored),
                summary="baseline: stubbed",
                return_code=(
                    baseline_code
                    if baseline_code is not None
                    else (0 if not baseline_failed else 1)
                ),
            )
        return prove_failability.RunOutcome(
            failed_node_ids=tuple(baseline_failed) + tuple(failed),
            error_node_ids=tuple(errored),
            summary=summary,
            return_code=code,
        )

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    return outcomes


def _manifest(tmp_path, **overrides):
    entry = {
        "label": "package/views.py::gate",
        "target": "package/views.py",
        "anchor": ANCHOR,
        "replacement": "    pass",
        "scope": ["tests/test_x.py"],
    }
    entry.update(overrides)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"proofs": [entry]}), encoding="utf-8")
    return path


def _single_entry(tmp_path, **overrides):
    entries, _ = prove_failability.load_manifest(_manifest(tmp_path, **overrides))
    return entries[0]


def _multi_manifest(tmp_path, count=3):
    """Write a ``count``-entry manifest, so ``--only`` can select a genuine subset."""
    proofs = [
        {
            "label": f"package/views.py::gate_{index}",
            "target": "package/views.py",
            "anchor": ANCHOR,
            "replacement": "    pass",
            "scope": [f"tests/test_{index}.py"],
        }
        for index in range(1, count + 1)
    ]
    path = tmp_path / "multi.json"
    path.write_text(json.dumps({"proofs": proofs}), encoding="utf-8")
    return path


def _four_failing_rows(monkeypatch):
    """Stub every entry as a pinned boundary: 4 attributable rows each, so the run exits 0.

    ``_stub_run`` treats only the very first call as a baseline, which is right for a
    one-entry manifest; a multi-entry run needs a baseline/mutant pair per entry, or
    entries after the first difference to zero and grade weakly pinned.
    """
    calls = []
    failed = tuple(f"tests/test_x.py::test_{index}" for index in range(4))

    def fake_run_scope(entry):
        calls.append(entry)
        if len(calls) % 2 == 1:
            return prove_failability.RunOutcome((), (), "baseline: stubbed", 0)
        return prove_failability.RunOutcome(failed, (), "stubbed", 1)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    return calls


def test_a_proof_mutates_runs_restores_and_proves_the_restore_by_byte_comparison(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    seen = _stub_run(monkeypatch, failed=("tests/test_x.py::test_a", "tests/test_x.py::test_b"))
    entry = _single_entry(tmp_path)

    result = prove_failability.execute_entry(entry, scratch_root)

    # The mutation was live while the scope ran, and is gone afterwards. The scope
    # ran twice: once unmutated for the baseline, once with the mutation live.
    assert seen == [entry, entry]
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert "filecmp.cmp(shallow=False) True" in result.restore_proof
    assert result.failed_count == 2
    assert result.failure is None
    # No marker survives a proved restore, so a leftover marker always means trouble.
    assert not (scratch_root / prove_failability.ACTIVE_MARKER_NAME).exists()


def test_the_mutated_text_is_what_the_scope_actually_runs_against(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    target = fake_repo / "package" / "views.py"
    observed = {}
    calls = []

    def fake_run_scope(entry):
        calls.append(entry)
        observed[f"text{len(calls)}"] = target.read_text(encoding="utf-8")
        if len(calls) == 1:
            # The baseline runs before the marker is written: nothing is mutated yet.
            assert not (scratch_root / prove_failability.ACTIVE_MARKER_NAME).exists()
        else:
            observed["marker"] = json.loads(
                (scratch_root / prove_failability.ACTIVE_MARKER_NAME).read_text(encoding="utf-8"),
            )
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)

    prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert observed["text1"] == SOURCE
    assert observed["text2"] == "def gate(value):\n    pass\n    return value\n"
    assert observed["marker"]["mutated_file"] == str(target)
    assert observed["marker"]["restore_from"].endswith("__package__views.py")


def test_a_delete_entry_removes_the_anchor_text(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    target = fake_repo / "package" / "views.py"
    observed = {}
    calls = []

    def fake_run_scope(entry):
        calls.append(entry)
        # The second call is the mutant; the first is the unmutated baseline.
        observed["text"] = target.read_text(encoding="utf-8")
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    # ``delete`` and ``replacement`` are mutually exclusive, so build without one.
    manifest = tmp_path / "delete.json"
    manifest.write_text(
        json.dumps(
            {
                "proofs": [
                    {
                        "label": "package/views.py::gate",
                        "target": "package/views.py",
                        "anchor": ANCHOR,
                        "delete": True,
                        "scope": ["tests/test_x.py"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    entries, _ = prove_failability.load_manifest(manifest)
    assert entries[0].replacement is None
    assert entries[0].mutation.startswith("deleted:")

    prove_failability.execute_entry(entries[0], scratch_root)

    assert observed["text"] == "def gate(value):\n\n    return value\n"
    assert target.read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize(
    ("anchor", "expected"),
    [("not in the file at all", 0), ("value", 3)],
)
def test_an_anchor_that_does_not_match_exactly_once_mutates_nothing(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
    anchor,
    expected,
):
    seen = _stub_run(monkeypatch)
    entry = _single_entry(tmp_path, anchor=anchor)

    result = prove_failability.execute_entry(entry, scratch_root)

    assert seen == []
    assert f"anchor matched {expected} times" in result.failure
    assert result.outcome is None
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert not list((scratch_root / prove_failability.PRISTINE_DIRECTORY_NAME).iterdir())


def test_check_anchors_only_validates_without_mutating_or_running(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    seen = _stub_run(monkeypatch)

    result = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
        anchors_only=True,
    )

    assert seen == []
    assert result.failure is None
    assert result.outcome is None
    # An unrun entry is not a zero-row entry: it must not read as weakly pinned.
    assert result.is_weakly_pinned is False
    assert result.is_inside_rerun_floor is False


def test_a_failed_restore_raises_writes_a_marker_and_stops_the_run(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    _stub_run(monkeypatch)
    monkeypatch.setattr(prove_failability.filecmp, "cmp", lambda *args, **kwargs: False)

    with pytest.raises(prove_failability.RestoreProofError):
        prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    marker = json.loads(
        (scratch_root / prove_failability.RESTORE_FAILED_MARKER_NAME).read_text(encoding="utf-8"),
    )
    assert marker["mutated_file"] == str(fake_repo / "package" / "views.py")
    # The active marker deliberately survives: it is what identifies the live mutation.
    assert (scratch_root / prove_failability.ACTIVE_MARKER_NAME).exists()


def test_an_unwritable_target_is_a_restore_proof_error_not_a_bare_oserror(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    def refuse(*args, **kwargs):
        raise PermissionError("read-only file system")

    def fake_run_scope(entry):
        # Break the restore only AFTER the pristine copy was taken, so the
        # failure lands where a real read-only tree would put it.
        monkeypatch.setattr(prove_failability.shutil, "copyfile", refuse)
        return prove_failability.RunOutcome((), (), "stubbed", 1)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)

    with pytest.raises(prove_failability.RestoreProofError, match="could not be restored"):
        prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)


def test_a_pristine_copy_that_cannot_be_taken_stops_before_mutating(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    seen = _stub_run(monkeypatch)

    def refuse(*args, **kwargs):
        raise PermissionError("no space left on device")

    monkeypatch.setattr(prove_failability.shutil, "copy2", refuse)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert seen == []
    assert "nothing was mutated" in result.failure
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


def test_a_target_outside_the_repository_is_refused(fake_repo, tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text(SOURCE, encoding="utf-8")

    with pytest.raises(prove_failability.ManifestError, match="outside the repository"):
        prove_failability.load_manifest(_manifest(tmp_path, target=str(outside)))


def test_a_scratch_root_inside_the_repository_is_refused(fake_repo):
    with pytest.raises(prove_failability.ManifestError, match="inside the repository"):
        prove_failability._resolve_scratch_root(str(fake_repo / "docs"))


def test_a_scratch_root_outside_the_repository_is_created(fake_repo, tmp_path):
    resolved = prove_failability._resolve_scratch_root(str(tmp_path / "outside-scratch"))

    assert (resolved / prove_failability.PRISTINE_DIRECTORY_NAME).is_dir()


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"scope": ["tests/test_x.py", "--cov=package"]}, "forbidden"),
        ({"scope": []}, "non-empty list"),
        ({"anchor": ""}, "must not be empty"),
        ({"label": ""}, "non-empty string"),
        ({"target": ""}, "non-empty string"),
        ({"delete": True}, "not both"),
        ({"anchor": {"a": 1}}, "list of strings"),
        ({"mutation": 7}, "must be a string"),
    ],
)
def test_manifest_refusals(
    fake_repo,
    tmp_path,
    overrides,
    expected,
):
    with pytest.raises(prove_failability.ManifestError, match=expected):
        prove_failability.load_manifest(_manifest(tmp_path, **overrides))


@pytest.mark.parametrize(
    "label",
    [
        "package/other.py::gate",
        "django_strawberry_framework/views.py::GraphQLView.dispatch",
        'package/other.py #"if value is None"',
    ],
)
def test_a_label_whose_leading_path_disagrees_with_the_target_is_refused(
    fake_repo,
    tmp_path,
    label,
):
    # The fail-open this closes: `label` is free manifest text and `target` is resolved
    # separately, so an entry could name a PRODUCTION boundary while the bytes landed in
    # a test file - and the label was the record's only file identity, so nothing
    # downstream could notice. `relative_target` already existed; it just falsified
    # nothing.
    with pytest.raises(prove_failability.ManifestError, match="is not the mutation target"):
        prove_failability.load_manifest(_manifest(tmp_path, label=label))


@pytest.mark.parametrize(
    "label",
    [
        "gate",
        "GraphQLView.dispatch",
        'GraphQLView.dispatch #"if value is None"',
        "package/views.py::gate",
        'package/views.py::gate #"raise ValueError"',
        'package/views.py #"raise ValueError"',
    ],
)
def test_a_label_that_claims_no_path_or_the_right_one_is_accepted(fake_repo, tmp_path, label):
    # Only DISAGREEMENT is refused, never absence: `AGENTS.md` "Source references in
    # docs and code comments" also blesses `path #"unique substring"` and a bare symbol,
    # so a label with no path prefix is a legitimate shape and must not be rejected. A
    # bare symbol carrying a substring pointer is the trap - `GraphQLView.dispatch` has a
    # dotted tail that reads like a filename, and refusing it would be a false refusal.
    assert prove_failability.load_manifest(_manifest(tmp_path, label=label))[0][0].label == label


def test_an_absolute_leading_path_and_a_top_level_one_are_both_read_as_path_claims(
    fake_repo,
    tmp_path,
):
    # Two spellings a substring comparison would get wrong: the same file given
    # absolutely (agrees - accept), and a repo-root file named without any `/` at all
    # (disagrees - refuse), which is why the check resolves paths and asks the
    # filesystem rather than matching text.
    absolute = str((fake_repo / "package" / "views.py").resolve())
    entries, _ = prove_failability.load_manifest(_manifest(tmp_path, label=f"{absolute}::gate"))
    assert entries[0].relative_target == "package/views.py"

    (fake_repo / "conftest.py").write_text(SOURCE, encoding="utf-8")
    with pytest.raises(prove_failability.ManifestError, match="is not the mutation target"):
        prove_failability.load_manifest(_manifest(tmp_path, label="conftest.py::gate"))


@pytest.mark.parametrize(
    "fragment",
    [
        "-x",
        "-xvs",
        "-svx",
        "--exitfirst",
        "--maxfail=3",
        "--maxfail",
    ],
)
def test_a_scope_that_stops_the_run_early_is_refused_like_cov(fake_repo, tmp_path, fragment):
    # Verified against a real 9-row scope before this was written: `-n0 -x` grades a
    # 4-row boundary as 1 row (**WEAKLY PINNED**) and `-n0 --maxfail=3` grades it 3 rows
    # (inside the re-run acceptance floor), both at pytest exit 1 with every recorded field
    # present, and both reporting fewer pre-existing rows than were already failing. The
    # exit-code channel does not see it: it is only under this repo's default `-n auto`
    # that the same fragments interrupt the session (exit 2) and are already invalid.
    # What no channel can see is that the fragment travels in the RECORDED scope, so the
    # mandatory independent re-run reproduces the same wrong number.
    with pytest.raises(prove_failability.ManifestError, match="stops the run early"):
        prove_failability.load_manifest(
            _manifest(tmp_path, scope=["tests/test_x.py", fragment]),
        )


@pytest.mark.parametrize(
    "scope",
    [
        ["tests/test_x.py", "-k", "test_expiry"],
        ["tests/test_x.py", "-ktest_expiry"],
        ["tests/test_x.py", "-n0"],
        ["tests/test_exitfirst.py::test_maxfail"],
    ],
)
def test_a_scope_that_merely_narrows_the_row_set_is_not_refused(fake_repo, tmp_path, scope):
    # `-k`, `--deselect` and a node id narrow the row set IDENTICALLY in the unmutated
    # and the mutated run, so the set difference stays a difference of the same rows - a
    # focused scope is the whole point. What is refused is a cut whose position depends
    # on the failures of the run making it. `-ktest_expiry` and a path containing an `x`
    # are the shapes a substring search for `-x` would refuse by mistake.
    assert prove_failability.load_manifest(_manifest(tmp_path, scope=scope))[0][0].scope == tuple(
        scope,
    )


def test_a_missing_replacement_and_a_missing_anchor_are_both_refused(fake_repo, tmp_path):
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps({"proofs": [{"label": "x", "target": "package/views.py", "scope": ["a"]}]}),
        encoding="utf-8",
    )
    with pytest.raises(prove_failability.ManifestError, match="'anchor' is required"):
        prove_failability.load_manifest(path)

    path.write_text(
        json.dumps(
            {
                "proofs": [
                    {
                        "label": "x",
                        "target": "package/views.py",
                        "anchor": ANCHOR,
                        "scope": ["a"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    with pytest.raises(prove_failability.ManifestError, match="'replacement' or 'delete'"):
        prove_failability.load_manifest(path)


def test_an_unknown_entry_key_is_refused_so_a_typo_is_not_silently_ignored(fake_repo, tmp_path):
    with pytest.raises(prove_failability.ManifestError, match=r"unknown key\(s\) \['ancor'\]"):
        prove_failability.load_manifest(_manifest(tmp_path, ancor=ANCHOR))


def test_a_multi_line_anchor_may_be_given_as_a_list_of_lines(fake_repo, tmp_path):
    entry = _single_entry(
        tmp_path,
        anchor=["    if value is None:", '        raise ValueError("no")'],
        replacement=["    pass"],
    )

    assert entry.anchor == ANCHOR
    assert entry.replacement == "    pass"


def test_duplicate_labels_are_refused(fake_repo, tmp_path):
    entry = {
        "label": "same",
        "target": "package/views.py",
        "anchor": ANCHOR,
        "replacement": "    pass",
        "scope": ["tests/test_x.py"],
    }
    path = tmp_path / "dupes.json"
    path.write_text(json.dumps({"proofs": [entry, dict(entry)]}), encoding="utf-8")

    with pytest.raises(prove_failability.ManifestError, match="duplicate label"):
        prove_failability.load_manifest(path)


@pytest.mark.parametrize(
    ("selectors", "expected"),
    [
        ([], ["a", "b", "c"]),
        (["2"], ["b"]),
        (["c", "a"], ["c", "a"]),
        (["1", "1"], ["a"]),
    ],
)
def test_only_selects_by_index_or_label_substring(selectors, expected):
    entries = [
        prove_failability.ProofEntry(name, prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
        for name in ("a", "b", "c")
    ]

    selected = prove_failability.select_entries(entries, selectors)

    assert [entry.label for entry in selected] == expected


@pytest.mark.parametrize("selector", ["9", "nope"])
def test_only_refuses_a_selector_that_matches_nothing(selector):
    entries = [
        prove_failability.ProofEntry("a", prove_failability.REPO_ROOT, "x", "y", "m", ("s",)),
    ]

    with pytest.raises(prove_failability.ManifestError):
        prove_failability.select_entries(entries, [selector])


def test_xdist_progress_lines_are_not_mistaken_for_failing_node_ids():
    stdout = (
        "[gw3] [ 50%] FAILED tests/test_x.py::test_progress_line_only\n"
        "FAILED tests/test_x.py::test_real - AssertionError: boom\n"
        "FAILED tests/test_x.py::test_real - a duplicate summary line\n"
        "ERROR tests/test_y.py - collection blew up\n"
        "=== 1 failed, 1 error, 40 passed in 3.21s ===\n"
    )

    failed, errored, summary = prove_failability._parse_run_output(stdout)

    assert failed == ("tests/test_x.py::test_real",)
    assert errored == ("tests/test_y.py",)
    assert "1 failed, 1 error, 40 passed" in summary


@pytest.mark.parametrize(
    ("failed_rows", "weak", "floor"),
    [
        (0, True, True),
        (1, True, True),
        (2, False, True),
        (3, False, True),
        (4, False, False),
    ],
)
def test_the_acceptance_rule_flags_weak_pinning_and_the_rerun_floor(failed_rows, weak, floor):
    entry = prove_failability.ProofEntry(
        "label",
        prove_failability.REPO_ROOT,
        "a",
        "b",
        "m",
        ("s",),
    )
    outcome = prove_failability.RunOutcome(
        failed_node_ids=tuple(f"tests/test_x.py::test_{index}" for index in range(failed_rows)),
        error_node_ids=(),
        summary="stubbed",
        return_code=1,
    )
    result = prove_failability.ProofResult(entry, outcome, "proved", None)

    assert result.failed_count == failed_rows
    assert result.is_weakly_pinned is weak
    assert result.is_inside_rerun_floor is floor
    assert ("WEAKLY PINNED" in prove_failability._verdict(result)) is weak


def test_the_baseline_runs_by_default_and_excludes_rows_that_were_already_failing(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # No ``capture_baseline`` argument: the pre-mutation run is a mandatory field of
    # the record, so it is the default. One pre-existing failing row would otherwise
    # inflate the count and make this genuinely 1-row boundary read as 2-row pinned.
    calls = _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_boundary",),
        baseline_failed=("tests/test_x.py::test_flaky",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert len(calls) == 2
    assert result.baseline is not None
    assert result.outcome.failed_node_ids == (
        "tests/test_x.py::test_flaky",
        "tests/test_x.py::test_boundary",
    )
    assert result.attributable_node_ids == ("tests/test_x.py::test_boundary",)
    assert result.failed_count == 1
    assert result.is_weakly_pinned is True


def test_opting_out_of_the_baseline_records_the_missing_mandatory_field(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    calls = _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_boundary",),
        baseline_failed=("tests/test_x.py::test_flaky",),
    )

    result = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
        capture_baseline=False,
    )

    # Only the mutant ran, so the count is the raw failure set - the pre-existing
    # row inflates it. The report must say the field is missing, not imply a green
    # pre-mutation state, because "2 rows" here is not attributable to the mutation.
    assert len(calls) == 1
    assert result.baseline is None
    assert result.failed_count == 1
    report = prove_failability.render_report([result])
    assert "**NOT CAPTURED** (`--no-baseline`)" in report
    assert "not a compliant proof" in report


def test_collection_errors_make_the_count_invalid_rather_than_footnoted(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_a", "tests/test_x.py::test_b"),
        errored=("tests/test_y.py",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.error_count == 1
    assert result.invalid_count_reason is not None
    verdict = prove_failability._verdict(result)
    assert "INVALID COUNT" in verdict
    assert "1 collection/setup error(s)" in verdict
    assert "not a valid count" in verdict
    report = prove_failability.render_report([result])
    assert "NOT A VALID COUNT" in report
    assert "collection/setup errors: 1" in report
    assert "ERROR `tests/test_y.py`" in report


def test_a_baseline_collection_error_also_invalidates_the_count(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # The pre-mutation run is the reference the mutant is differenced against, so a
    # scope that cannot even collect unmutated is no reference at all.
    _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_a", "tests/test_x.py::test_b"),
        baseline_errored=("tests/test_y.py",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.error_count == 1
    assert "in the baseline run" in result.invalid_count_reason


@pytest.mark.parametrize(
    ("code", "reading"),
    [
        (5, "pytest collected no test at all"),
        (4, "pytest rejected the invocation as a usage error"),
        (2, "pytest was interrupted"),
        (3, "pytest hit an internal error"),
        (99, "pytest exited outside its documented code set"),
    ],
)
def test_a_mutant_run_that_could_not_report_is_an_invalid_count_not_a_measured_zero(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
    code,
    reading,
):
    # pytest emits no FAILED line for exit 5, 4, 2 or 3, which is textually identical
    # to a clean run of a boundary nothing pins. Recorded as a measured 0 the entry
    # earns the `why 0` slot, and a hand fill-in of "harness-impossible interleaving"
    # converts a mistyped scope path into an accepted boundary - fail-open, and the
    # same class as the collection-error case above.
    _stub_run(monkeypatch, failed=(), code=code)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.failed_count == 0
    assert f"the mutant run exited {code}" in result.invalid_count_reason
    assert reading in result.invalid_count_reason
    assert "INVALID COUNT" in prove_failability._verdict(result)
    # An uncountable run is not a small count: claiming both would prescribe two
    # opposite remedies (more rows, versus fix the run) in one verdict.
    assert result.is_weakly_pinned is False
    assert result.is_inside_rerun_floor is False
    assert "WEAKLY PINNED" not in report
    # And the zero that was never measured is not offered the judgement slot.
    assert "why 0:" not in report
    assert "no `why 0` is asked for here" in report
    assert f"pytest exit code: {code}" in report


def test_exit_five_reads_as_a_wrong_scope_and_every_other_code_as_a_broken_run(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # "Your scope matched no tests" is a different operator action from "your run blew
    # up" - correct the scope path or node id, versus fix the run - so the two must not
    # collapse into one generic sentence that leaves the reader guessing which happened.
    _stub_run(monkeypatch, failed=(), code=5)
    collected_nothing = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
    ).invalid_count_reason

    _stub_run(monkeypatch, failed=(), code=4)
    blew_up = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
    ).invalid_count_reason

    assert "the scope matched no test at all" in collected_nothing
    assert "a node id that no longer exists" in collected_nothing
    assert "correct the scope and re-run" in collected_nothing
    assert "the run did not complete" not in collected_nothing
    assert "the run did not complete" in blew_up
    assert "the scope matched no test" not in blew_up


@pytest.mark.parametrize("code", [5, 4, 2])
def test_a_baseline_run_that_could_not_report_also_invalidates_the_count(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
    code,
):
    # The pre-mutation run is the reference the mutant's failure set is differenced
    # against, so a baseline that never collected is no reference at all - and its
    # empty failure set otherwise reads as "nothing was already failing". The mutant
    # here reports 4 rows, so without reading the baseline's code this grades pinned.
    _stub_run(
        monkeypatch,
        failed=tuple(f"tests/test_x.py::test_{index}" for index in range(4)),
        baseline_code=code,
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.failed_count == 4
    assert f"the baseline run exited {code}" in result.invalid_count_reason
    assert "invalidates the difference as well" in result.invalid_count_reason
    assert "INVALID COUNT" in prove_failability._verdict(result)
    assert f"(pytest exit code {code})" in prove_failability.render_report([result])


def test_every_invalidating_reason_is_named_rather_than_only_the_first(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # Three independent invalidations at once. Reporting one and dropping the others
    # would send the reader to fix the collection error and re-run into the same two
    # broken invocations.
    _stub_run(monkeypatch, errored=("tests/test_y.py",), code=5, baseline_code=4)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert len(result.invalid_count_reasons) == 3
    assert "1 collection/setup error(s)" in result.invalid_count_reason
    assert "the mutant run exited 5" in result.invalid_count_reason
    assert "the baseline run exited 4" in result.invalid_count_reason


def test_two_runs_that_failed_the_same_way_are_named_once_not_twice(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # A mistyped scope path collects nothing in either run, and repeating the same
    # paragraph under two headings is how a reader learns to skim the verdict.
    _stub_run(monkeypatch, failed=(), code=5, baseline_code=5)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.invalid_count_reasons == (
        prove_failability._uncountable_run_reason("both the mutant and the baseline run", 5),
    )
    assert "both the mutant and the baseline run exited 5" in result.invalid_count_reason
    assert "invalidates the difference as well" in result.invalid_count_reason


def test_a_genuinely_measured_zero_still_carries_the_why_zero_judgement_slot(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # Exit 0 means the scope ran and every row passed: that IS a zero-row result, and
    # the judgement belongs there. The exit-code check must not swallow the real case.
    _stub_run(monkeypatch, failed=(), code=0)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.invalid_count_reason is None
    assert result.is_weakly_pinned is True
    assert "why 0: <fill in" in report
    assert "no `why 0` is asked for here" not in report


def test_main_fails_when_the_scope_collected_nothing_at_all(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    # A typo'd scope path or a retired node id exits 5 with no FAILED lines; the
    # record used to call that a measured 0 and hand it the why-0 slot.
    _stub_run(monkeypatch, failed=(), code=5)

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 1
    captured = capsys.readouterr()
    assert "NOT A VALID COUNT" in captured.out
    assert "the mutant run exited 5" in captured.out
    assert "why 0:" not in captured.out


def test_a_clean_run_has_no_error_count_and_no_invalid_verdict(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.error_count == 0
    assert result.invalid_count_reason is None
    assert prove_failability._verdict(result) == "pinned"


def test_the_report_carries_the_scope_the_node_ids_and_the_restore_proof(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    _stub_run(monkeypatch, failed=("tests/test_x.py::test_a",), summary="1 failed in 1.00s")

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert report.startswith("### Failability proofs")
    assert "package/views.py::gate" in report
    assert "tests/test_x.py::test_a" in report
    assert "1 failed in 1.00s" in report
    assert "filecmp.cmp(shallow=False) True" in report
    assert "WEAKLY PINNED" in report
    assert "git" in report
    assert "pre-mutation (unmutated) state of this scope: `baseline: stubbed`" in report


def test_the_record_names_the_file_that_was_actually_mutated(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # `relative_target` was computed and rendered nowhere, so every file identity in the
    # emitted record came from the free-text label - the record could not name the file
    # the bytes went to even though the value that falsifies the label already existed.
    # Varying only the target must change the record: the same load-bearing requirement
    # `test_every_captured_field_of_a_run_outcome_is_load_bearing_in_the_record` puts on
    # the observation fields, applied to the one input that is not merely an identifier
    # a reader re-runs.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    entry = _single_entry(tmp_path)

    result = prove_failability.execute_entry(entry, scratch_root)
    report = prove_failability.render_report([result])

    assert "| File mutated |" in report
    assert "| `package/views.py` |" in report
    assert "   - file mutated: `package/views.py`" in report
    moved = dataclasses.replace(
        result,
        entry=dataclasses.replace(entry, target=fake_repo / "package" / "elsewhere.py"),
    )
    assert prove_failability.render_report([moved]) != report


def test_manifest_prose_accompanies_the_derived_mutation_and_never_replaces_it(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # The fail-open this closes: the manifest's optional free-text `mutation` was
    # rendered INSTEAD of the derived anchor -> replacement, so an entry claiming "the
    # Host-validation gate deleted" printed exactly that while its anchor may only have
    # perturbed an adjacent line - which `### What gets recorded` forbids outright ("a
    # mutation must remove the boundary, not merely perturb code near it"). The report
    # carried no rendering of the real bytes, so no reader downstream could audit the
    # claim against what was written.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    claimed = "the Host-validation gate deleted"
    entry = _single_entry(tmp_path, mutation=claimed)

    result = prove_failability.execute_entry(entry, scratch_root)
    report = prove_failability.render_report([result])

    derived = '`if value is None: raise ValueError("no")` -> `pass`'
    assert entry.prose == claimed
    assert entry.mutation == derived
    assert derived in report
    assert f"builder's description (unverified prose): {claimed}" in report


def test_an_entry_without_prose_renders_the_derived_mutation_alone(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # Absence of the "unverified prose" marker must mean something, so an entry that
    # made no claim does not get an empty one.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    entry = _single_entry(tmp_path)

    report = prove_failability.render_report(
        [prove_failability.execute_entry(entry, scratch_root)],
    )

    assert entry.prose == ""
    assert entry.mutation_applied == entry.mutation
    assert '`if value is None: raise ValueError("no")` -> `pass`' in report
    assert "builder's description" not in report


def test_the_table_prints_the_scope_as_a_runnable_command_not_a_bare_path(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # The independent re-run happens "at the scope the record names"; a bare path in
    # the column headed "Scope as run" forces the re-runner to reconstruct --no-cov and
    # the rest of the flag set out of a prose paragraph instead of copying a command.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    entry = _single_entry(tmp_path)

    report = prove_failability.render_report(
        [prove_failability.execute_entry(entry, scratch_root)],
    )

    assert entry.scope_as_run.startswith("uv run pytest --no-cov")
    assert entry.scope_as_run.endswith("tests/test_x.py")
    assert f"| `{entry.scope_as_run}` |" in report


def test_every_captured_field_of_a_run_outcome_is_load_bearing_in_the_record():
    """No field of the observation type may be captured and then read by nothing.

    This pins the recurring class rather than one instance of it. ``return_code``
    was captured from this script's first version and consumed by nothing, which
    is how a pytest exit 5 came to be recorded as a measured zero; the same shape
    would recur the next time a field is added to the captured observation and
    the record is not taught to read it. Varying one field at a time and
    requiring the rendered record to change is the cheapest mechanical statement
    of "every claim in the record is backed by an observation, and every
    observation reaches the record".

    Scoped deliberately to the observation type: ``ProofEntry`` holds *inputs*,
    and an input the record does not render is a different question (a reader
    re-runs an identifier rather than trusting it).
    """
    variants = {
        "failed_node_ids": ("tests/test_x.py::test_other",),
        "error_node_ids": ("tests/test_y.py",),
        "summary": "a different summary line",
        "return_code": 5,
    }
    captured = {field.name for field in dataclasses.fields(prove_failability.RunOutcome)}
    assert set(variants) == captured, "a new captured field needs a variant here"
    entry = prove_failability.ProofEntry("a", prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
    reference = prove_failability.RunOutcome(("tests/test_x.py::test_a",), (), "stubbed", 1)
    unaltered = prove_failability.render_report(
        [prove_failability.ProofResult(entry, reference, "proved", None)],
    )

    for name, value in variants.items():
        altered = dataclasses.replace(reference, **{name: value})
        report = prove_failability.render_report(
            [prove_failability.ProofResult(entry, altered, "proved", None)],
        )
        assert report != unaltered, f"RunOutcome.{name} never reaches the emitted record"


def test_a_zero_row_entry_carries_a_why_zero_placeholder_the_tool_cannot_fill(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # Weakly pinned and harness-impossible prescribe opposite responses, so the
    # emitted subsection must carry the slot rather than guess or omit it.
    _stub_run(monkeypatch, failed=())

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.failed_count == 0
    assert "why 0: <fill in - weakly pinned" in report
    assert "harness-impossible interleaving" in report
    assert "MUST be replaced by hand" in report


def test_a_nonzero_row_entry_carries_no_why_zero_placeholder(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert "why 0:" not in prove_failability.render_report([result])


def test_a_row_that_is_only_zero_after_the_baseline_difference_still_gets_the_placeholder(
    fake_repo,
    scratch_root,
    tmp_path,
    monkeypatch,
):
    # The pre-existing row is the whole failure set, so nothing is attributable: the
    # fail-open this closes is exactly this entry reading as a pinned 1-row boundary.
    _stub_run(
        monkeypatch,
        failed=(),
        baseline_failed=("tests/test_x.py::test_flaky",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.failed_count == 0
    assert "why 0: <fill in" in report
    assert "pre-existing failing rows excluded from the count: 1" in report


def test_main_returns_zero_on_a_pinned_boundary_and_one_on_a_weakly_pinned_one(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    manifest = _manifest(tmp_path)
    scratch = tmp_path / "outside-scratch"

    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    assert prove_failability.main([str(manifest), "--scratch-root", str(scratch)]) == 0

    _stub_run(monkeypatch, failed=("tests/test_x.py::test_only",))
    assert prove_failability.main([str(manifest), "--scratch-root", str(scratch)]) == 1
    assert "WEAKLY PINNED" in capsys.readouterr().out


def test_main_fails_when_collection_errors_make_the_count_invalid(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    # 4 attributable failures would be a pinned boundary; 8 rows that never ran mean
    # the run is not evidence of anything. This is the recorded csrf_exempt incident.
    _stub_run(
        monkeypatch,
        failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)),
        errored=tuple(f"tests/test_y{i}.py" for i in range(8)),
    )

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 1
    captured = capsys.readouterr()
    assert "NOT A VALID COUNT" in captured.out
    assert "8 collection/setup error(s)" in captured.out


def test_main_refuses_output_without_a_baseline_and_runs_nothing(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    seen = _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
            "--output",
            str(output),
        ],
    )

    assert code == 1
    assert seen == []
    assert not output.exists()
    assert "--no-baseline cannot be combined with --output" in capsys.readouterr().err


def test_check_anchors_only_may_write_output_without_a_baseline(fake_repo, tmp_path, monkeypatch):
    # Nothing ran, so there is no count for a missing baseline to inflate and the
    # emitted block says so in its own words rather than claiming a proof.
    seen = _stub_run(monkeypatch)
    output = tmp_path / "anchors.md"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
            "--check-anchors-only",
            "--output",
            str(output),
        ],
    )

    assert code == 0
    assert seen == []
    assert "no mutation was applied and no scope was run" in output.read_text(encoding="utf-8")


def test_no_baseline_without_output_runs_the_scope_once(fake_repo, tmp_path, monkeypatch):
    seen = _stub_run(
        monkeypatch,
        failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)),
        first_call_is_baseline=False,
    )

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
        ],
    )

    assert code == 0
    assert len(seen) == 1


def test_the_legacy_baseline_flag_is_accepted_and_wins_over_no_baseline(
    fake_repo,
    tmp_path,
    monkeypatch,
):
    seen = _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
            "--baseline",
        ],
    )

    assert code == 0
    assert len(seen) == 2


def test_main_reports_a_manifest_error_without_running_anything(tmp_path, capsys):
    manifest = tmp_path / "broken.json"
    manifest.write_text("{not json", encoding="utf-8")

    assert prove_failability.main([str(manifest)]) == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_main_aborts_with_a_dedicated_code_when_a_restore_cannot_be_proved(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    _stub_run(monkeypatch)
    monkeypatch.setattr(prove_failability.filecmp, "cmp", lambda *args, **kwargs: False)

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 3
    assert "RESTORE FAILED" in capsys.readouterr().err


def test_a_failed_restore_still_writes_the_partial_report_to_the_output_path(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    # A partial record of a run that stopped with a possibly-live mutation is exactly
    # what the next reader needs; stdout-only would lose it.
    _stub_run(monkeypatch)
    monkeypatch.setattr(prove_failability.filecmp, "cmp", lambda *args, **kwargs: False)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--output",
            str(output),
        ],
    )

    assert code == 3
    written = output.read_text(encoding="utf-8")
    assert written.startswith("### Failability proofs")
    assert "RUN ABORTED - A RESTORE COULD NOT BE PROVED" in written
    assert prove_failability.RESTORE_FAILED_MARKER_NAME in written
    assert "PARTIAL record" in written
    assert "_(no entry completed)_" in written
    assert "partial report written to" in capsys.readouterr().err


def test_an_only_run_labels_its_report_a_partial_record_at_both_ends_and_in_the_table(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    # The fail-open this closes: `--only 3 --output` used to emit a block textually
    # identical to a complete run's, so a record covering one boundary of twenty could
    # be pasted into a subsection that requires one entry per new boundary, and a
    # reader of the record - who never sees the command line - had nothing to notice.
    _four_failing_rows(monkeypatch)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--only",
            "2",
            "--output",
            str(output),
        ],
    )

    assert code == 0
    written = output.read_text(encoding="utf-8")
    lines = written.rstrip().split("\n")
    # Directly under the heading, ahead of the procedure prose: the first thing read.
    assert lines[0] == "### Failability proofs"
    assert lines[2].startswith("**PARTIAL RECORD - `--only` NARROWED THIS RUN: 1 of 3 manifest")
    assert "`--only 2`" in lines[2]
    # And on the last line, because a top-only notice is lost when the block is pasted
    # from part-way down.
    assert lines[-1].startswith("**Reminder, PARTIAL RECORD: this block covers 1 of 3 manifest")
    # The entries that went unproved are named, not merely counted.
    assert "- `package/views.py::gate_1`" in written
    assert "- `package/views.py::gate_3`" in written
    # And the `#` column carries the manifest position, so the single row cannot read
    # as entry 1 of 1 even with every line of prose stripped out.
    assert "| 2 | `package/views.py::gate_2` |" in written
    assert "2. `package/views.py::gate_2` - pinned" in written
    assert "PARTIAL RUN: --only selected 1 of 3 manifest entries" in capsys.readouterr().err


def test_a_full_run_says_nothing_about_selection_so_the_partial_notice_stays_meaningful(
    fake_repo,
    tmp_path,
    monkeypatch,
):
    # Absence of the notice is only evidence if the notice is never noise, so a run
    # that covered the whole manifest emits no selection prose at all.
    _four_failing_rows(monkeypatch)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--output",
            str(output),
        ],
    )

    assert code == 0
    written = output.read_text(encoding="utf-8")
    assert "PARTIAL RECORD" not in written
    assert "did NOT prove" not in written
    assert "manifest entries" not in written
    # Numbering is unchanged for a full run: manifest position and row number agree.
    assert "| 3 | `package/views.py::gate_3` |" in written


def test_only_selectors_that_cover_the_whole_manifest_are_not_a_partial_record(
    fake_repo,
    tmp_path,
    monkeypatch,
):
    # Partial is about coverage, not about the flag: a selector set that names every
    # entry leaves no boundary unproved, so labelling it partial would be false.
    _four_failing_rows(monkeypatch)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--only",
            "gate",
            "--output",
            str(output),
        ],
    )

    assert code == 0
    assert "PARTIAL RECORD" not in output.read_text(encoding="utf-8")


def test_only_is_still_allowed_output_unlike_no_baseline_which_is_refused(
    fake_repo,
    tmp_path,
    monkeypatch,
    capsys,
):
    # The two flags are not the same fault. --no-baseline omits a field ARTIFACT.md
    # requires, so no annotation can make that report a compliant record. --only emits
    # a truthful record of fewer boundaries - and the mandatory independent
    # re-run of a *subset* is exactly what it is for, and that re-run gets recorded.
    # Refusing --output would push that re-run back to hand-copied stdout, which is
    # where a banner gets dropped. So: labelled, not refused.
    manifest = _multi_manifest(tmp_path)
    scratch = tmp_path / "outside-scratch"
    narrowed = tmp_path / "narrowed.md"
    baseline_less = tmp_path / "baseline-less.md"

    _four_failing_rows(monkeypatch)
    assert (
        prove_failability.main(
            [
                str(manifest),
                "--scratch-root",
                str(scratch),
                "--only",
                "1",
                "--output",
                str(narrowed),
            ],
        )
        == 0
    )

    seen = _four_failing_rows(monkeypatch)
    code = prove_failability.main(
        [
            str(manifest),
            "--scratch-root",
            str(scratch),
            "--only",
            "1",
            "--no-baseline",
            "--output",
            str(baseline_less),
        ],
    )

    written = narrowed.read_text(encoding="utf-8")
    assert written.startswith("### Failability proofs")
    assert "PARTIAL RECORD" in written
    assert code == 1
    assert seen == []
    assert not baseline_less.exists()
    assert "--no-baseline cannot be combined with --output" in capsys.readouterr().err


def test_an_aborted_narrowed_run_keeps_the_partial_record_notice(fake_repo, tmp_path, monkeypatch):
    # Two independent reasons the record is partial: the restore that stopped the run
    # and the selection that shrank it. The reader needs both, so neither replaces
    # the other.
    _stub_run(monkeypatch)
    monkeypatch.setattr(prove_failability.filecmp, "cmp", lambda *args, **kwargs: False)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--only",
            "2",
            "--output",
            str(output),
        ],
    )

    assert code == 3
    written = output.read_text(encoding="utf-8")
    assert "PARTIAL RECORD - `--only` NARROWED THIS RUN: 1 of 3" in written
    assert "RUN ABORTED - A RESTORE COULD NOT BE PROVED" in written


def test_an_entry_with_no_manifest_position_falls_back_to_its_row_number():
    # ProofEntry can be built by hand (no manifest, so no position); the report must
    # still number the row rather than printing a 0.
    entry = prove_failability.ProofEntry("a", prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
    outcome = prove_failability.RunOutcome(("tests/test_x.py::test_a",), (), "stubbed", 1)

    report = prove_failability.render_report(
        [prove_failability.ProofResult(entry, outcome, "proved", None)],
    )

    assert entry.manifest_position == 0
    assert "| 1 | `a` |" in report


def test_describe_selection_counts_coverage_rather_than_trusting_the_selector_list():
    entries = [
        prove_failability.ProofEntry(name, prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
        for name in ("a", "b", "c")
    ]

    partial = prove_failability.describe_selection(entries, entries[:1], ["1"])
    whole = prove_failability.describe_selection(entries, entries, [])

    assert partial.is_partial is True
    assert partial.selected_total == 1
    assert partial.omitted_labels == ("b", "c")
    assert partial.selector_text == "--only 1"
    assert whole.is_partial is False
    assert whole.selected_total == 3
    assert whole.selector_text == "no selector"


def test_the_output_flag_writes_the_report_to_disk(fake_repo, tmp_path, monkeypatch):
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    output = tmp_path / "proofs.md"

    prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--output",
            str(output),
        ],
    )

    assert output.read_text(encoding="utf-8").startswith("### Failability proofs")
