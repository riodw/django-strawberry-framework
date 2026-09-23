"""Tests for TREE renderer planned descriptions, replacements, and source discovery.

Repo tooling: these rows pin ``scripts/build_tree_md.py`` module first-line
rule, ``--list-docstrings`` output, the stale ``--check`` report and exit
codes, planned-path annotations, target-layout replacements, and fakeshop
source discovery, which run at render time against the working tree and an
in-process card snapshot.
A live ``/graphql/`` request has no wire shape for TREE.md markdown, a
curated planned-path sentence, or a filesystem inventory the renderer walks,
so none of these rows can move. There is no live sibling in
``examples/fakeshop/test_query/``.
"""

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import build_tree_md
from scripts.build_tree_md import (
    DEFAULT_PACKAGE_DIR,
    DELIMITER,
    PLANNED_PATH_DESCRIPTIONS,
    REPO_ROOT,
    RULE_ENDS_WITH_PERIOD,
    RULE_NO_EG_IE,
    RULE_NOT_BANG_OR_QUESTION,
    RULE_ONE_SENTENCE,
    RULE_PARSES,
    RULE_PRESENT,
    SENTENCE_BREAK_RE,
    ModuleDescriptionError,
    PlannedPath,
    TargetNode,
    TreeRenderError,
    _planned_paths_from_rows,
    docstring_module_paths,
    fakeshop_app_names,
    first_line_violations,
    first_python_docstring_sentence,
    main,
    remove_target_replacements,
    render_fakeshop_project_tree,
    render_target_tree,
    render_tree_doc,
    stale_report,
    tree_row_paths,
)

_FAKESHOP_PROJECT = REPO_ROOT / "examples" / "fakeshop"
_FAKESHOP_APP_NAMES = fakeshop_app_names(_FAKESHOP_PROJECT / "apps")
_CURATED_PLANNED_DESCRIPTIONS = tuple(PLANNED_PATH_DESCRIPTIONS.items())
_FAKESHOP_TREE_SOURCE_FILES = (
    "graphql_client.py",
    "manage.py",
    "schema_reload.py",
    "strategy_schemas.py",
    "constraints.py",
    "filters_genre.py",
    "serializers.py",
    "signals.py",
    "factories.py",
)
_FAKESHOP_APP_LOCAL_TESTS = ("test_signals.py", "test_import_spec_terms.py")


def _card(
    number: int,
    key: str,
    card_id: str,
    title: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        number=number,
        card_id=card_id,
        title=title,
        status=SimpleNamespace(key=key),
    )


def _row(path: str, *, is_directory: bool, cards: list) -> SimpleNamespace:
    return SimpleNamespace(
        path=path,
        is_directory=is_directory,
        cards=SimpleNamespace(all=lambda cards=cards: list(cards)),
    )


@pytest.fixture(scope="module")
def rendered_fakeshop_project_tree() -> str:
    return "\n".join(render_fakeshop_project_tree(_FAKESHOP_PROJECT))


def test_planned_path_uses_branch_specific_description() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/fieldset/",
        is_directory=True,
        card_id="TODO-BETA-046-0.1.1",
        card_title="`FieldSet`",
    )

    assert planned.description == (
        "planned by TODO-BETA-046-0.1.1 - FieldSet computed fields, resolver overrides, "
        "field permissions, and optimizer dependencies."
    )


def test_planned_path_falls_back_to_card_title_without_curated_description() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/not_curated/",
        is_directory=True,
        card_id="TODO-BETA-099-0.9.9",
        card_title="`SomethingNew`",
    )

    assert planned.description == "planned by TODO-BETA-099-0.9.9 - `SomethingNew`."


def test_planned_path_title_fallback_is_normalized_not_double_terminated() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/not_curated/",
        is_directory=True,
        card_id="TODO-BETA-099-0.9.9",
        card_title="Already a sentence.  ",
    )

    assert planned.description == "planned by TODO-BETA-099-0.9.9 - Already a sentence."


def test_planned_path_rejects_a_two_sentence_title_like_any_summary() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/not_curated/",
        is_directory=True,
        card_id="TODO-BETA-099-0.9.9",
        card_title="First sentence. Second sentence",
    )

    with pytest.raises(TreeRenderError, match="ONE sentence"):
        _ = planned.description


def test_curated_planned_descriptions_are_present() -> None:
    """The curated planned-path descriptions mapping is non-empty."""
    assert len(PLANNED_PATH_DESCRIPTIONS) > 0


@pytest.mark.parametrize(
    ("path", "summary"),
    _CURATED_PLANNED_DESCRIPTIONS,
    ids=[path.rstrip("/").replace("/", "-") for path, _ in _CURATED_PLANNED_DESCRIPTIONS],
)
def test_curated_planned_description_is_one_sentence(path: str, summary: str) -> None:
    """Each curated planned-path summary is one sentence and wins over the card title."""
    planned = PlannedPath(path=path, is_directory=True, card_id="X-1", card_title="ignored")
    assert planned.description == f"planned by X-1 - {summary}"


def test_planned_rows_skip_paths_that_already_exist_on_disk() -> None:
    shipped = _row(
        "django_strawberry_framework/relay.py",
        is_directory=False,
        cards=[_card(10, "wip", "WIP-10", "already shipped")],
    )
    pending = _row(
        "django_strawberry_framework/fieldset/",
        is_directory=True,
        cards=[
            _card(30, "todo", "TODO-30", "later linker"),
            _card(12, "wip", "WIP-12", "owning card"),
        ],
    )

    planned = _planned_paths_from_rows([shipped, pending])

    assert [entry.path for entry in planned] == ["django_strawberry_framework/fieldset/"]
    assert planned[0].card_id == "WIP-12"


def test_target_replacement_removes_superseded_flat_module() -> None:
    root = TargetNode(
        name="django_strawberry_framework/",
        is_dir=True,
        description="",
        children={
            "permissions.py": TargetNode(
                name="permissions.py",
                is_dir=False,
                description="",
            ),
        },
    )
    planned = PlannedPath(
        path="django_strawberry_framework/permissions/",
        is_directory=True,
        card_id="TODO-BETA-051-0.1.4",
        card_title="redaction",
    )

    remove_target_replacements(root, "django_strawberry_framework/", planned)

    assert "permissions.py" not in root.children


def test_target_tree_replaces_flat_module_with_planned_package(tmp_path) -> None:
    package_dir = tmp_path / "django_strawberry_framework"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text('"""Test package root."""\n')
    (package_dir / "permissions.py").write_text('"""Flat permissions module."""\n')
    planned = PlannedPath(
        path="django_strawberry_framework/permissions/",
        is_directory=True,
        card_id="TODO-BETA-051-0.1.4",
        card_title="redaction",
    )

    rendered = "\n".join(
        render_target_tree(package_dir, "django_strawberry_framework/", [planned]),
    )

    assert "permissions/" in rendered
    assert "permissions.py" not in rendered


@pytest.mark.parametrize("filename", _FAKESHOP_TREE_SOURCE_FILES)
def test_fakeshop_project_tree_includes_source_file(
    filename: str,
    rendered_fakeshop_project_tree: str,
) -> None:
    """Root helpers and app sources the renderer is meant to walk appear in the tree."""
    assert filename in rendered_fakeshop_project_tree


@pytest.mark.parametrize("app_name", _FAKESHOP_APP_NAMES)
def test_fakeshop_project_tree_includes_app(
    app_name: str,
    rendered_fakeshop_project_tree: str,
) -> None:
    """Every filesystem-discovered fakeshop app is a directory in the project tree."""
    assert f"{app_name}/" in rendered_fakeshop_project_tree


def test_discovered_fakeshop_apps_equal_the_installed_local_apps() -> None:
    """The rendered app inventory is the settings' ``apps.*`` list, exactly.

    Read from the settings source rather than a configured Django so the tree
    renderer's discovery is checked against the project's own declaration, and a
    seventh app added to either side without the other fails here.
    """
    settings_text = (_FAKESHOP_PROJECT / "config" / "settings.py").read_text(
        encoding="utf-8",
    )
    installed = tuple(sorted(set(re.findall(r'"apps\.(\w+)\.apps\.', settings_text))))

    assert fakeshop_app_names(_FAKESHOP_PROJECT / "apps") == installed
    assert installed  # the regex must have found the local apps at all


@pytest.mark.parametrize("filename", _FAKESHOP_APP_LOCAL_TESTS)
def test_fakeshop_project_tree_excludes_app_local_test(
    filename: str,
    rendered_fakeshop_project_tree: str,
) -> None:
    """Each app's own tests tree is omitted from the project tree."""
    assert filename not in rendered_fakeshop_project_tree


_ACCEPTED_FIRST_LINES = (
    "Plain one-sentence summary.",
    "Reads ``Meta.cursor_field`` from ``utils/write_transaction.py``.",
    "Pinned to 0.0.14 and phase-2.5 behavior.",
    "Uses e.g.-style prose with no space after the dot.",
)
_REJECTED_FIRST_LINES = (
    ("Excited summary!", [RULE_NOT_BANG_OR_QUESTION]),
    ("Is this a summary?", [RULE_NOT_BANG_OR_QUESTION]),
    ("Summary with no terminator", [RULE_ENDS_WITH_PERIOD]),
    ("Summary wrapped onto the next", [RULE_ENDS_WITH_PERIOD]),
    ("Covers helpers, e.g. the walker.", [RULE_NO_EG_IE]),
    ("Covers one helper, i.e. the walker.", [RULE_NO_EG_IE]),
    ("First sentence. Second sentence.", [RULE_ONE_SENTENCE]),
    ("Walker vs. planner split.", [RULE_ONE_SENTENCE]),
    (
        "Covers e.g. the walker. And more!",
        [RULE_NOT_BANG_OR_QUESTION, RULE_NO_EG_IE, RULE_ONE_SENTENCE],
    ),
)


def _render_accepts(sentence: str) -> bool:
    """Return the render's acceptance predicate, restated independently of the rule names."""
    return sentence.endswith(".") and SENTENCE_BREAK_RE.search(sentence[:-1]) is None


def _write_module(path: Path, source: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


@pytest.fixture
def fake_package(tmp_path: Path) -> Path:
    """A package with one folder row, a passing module, and three rule breakers."""
    package = tmp_path / "fakepkg"
    _write_module(package / "__init__.py", '"""Fake package root."""\n')
    _write_module(package / "good.py", '"""Good summary.\n\nDetail prose. More detail."""\n')
    _write_module(package / "shouty.py", '"""Shouty summary!"""\n')
    _write_module(package / "bare.py", "VALUE = 1\n")
    _write_module(package / "sub" / "__init__.py", '"""Subpackage, e.g. helpers."""\n')
    _write_module(package / "migrations" / "0001_initial.py", "VALUE = 1\n")
    _write_module(package / "__pycache__" / "stale.py", "VALUE = 1\n")
    return package.resolve()


@pytest.mark.parametrize("sentence", _ACCEPTED_FIRST_LINES)
def test_first_line_rule_accepts_one_period_terminated_sentence(sentence: str) -> None:
    """Interior dots with no following space are not sentence breaks."""
    assert first_line_violations(sentence) == []
    assert _render_accepts(sentence)


@pytest.mark.parametrize(("sentence", "rules"), _REJECTED_FIRST_LINES)
def test_first_line_rule_names_every_broken_rule(sentence: str, rules: list[str]) -> None:
    """Each rejection is named by rule, and the render rejects the same line."""
    assert [violation.rule for violation in first_line_violations(sentence)] == rules
    assert not _render_accepts(sentence)


def test_first_python_docstring_sentence_reads_the_first_physical_line_only(
    tmp_path: Path,
) -> None:
    """Later paragraphs are detail prose; only line one renders."""
    module = _write_module(
        tmp_path / "mod.py",
        '"""\n\n  Module summary.\n\n  Second paragraph. With two sentences.\n"""\n',
    )
    assert first_python_docstring_sentence(module) == "Module summary."


def test_first_python_docstring_sentence_rejects_a_wrapped_summary(tmp_path: Path) -> None:
    """A summary that wraps onto a second line fails rather than rendering half of it."""
    module = _write_module(tmp_path / "mod.py", '"""Module summary that\nwraps."""\n')
    with pytest.raises(ModuleDescriptionError) as raised:
        first_python_docstring_sentence(module)
    assert raised.value.rule == RULE_ENDS_WITH_PERIOD
    assert raised.value.path == module


@pytest.mark.parametrize(
    ("source", "rule"),
    [
        ("VALUE = 1\n", RULE_PRESENT),
        ('""""""\n', RULE_PRESENT),
        ("def broken(:\n", RULE_PARSES),
    ],
    ids=["no-docstring", "empty-docstring", "syntax-error"],
)
def test_first_python_docstring_sentence_rejects_an_absent_docstring(
    tmp_path: Path,
    source: str,
    rule: str,
) -> None:
    """A module with no usable docstring names itself and the rule."""
    module = _write_module(tmp_path / "mod.py", source)
    with pytest.raises(ModuleDescriptionError, match=r"\[" + rule + r"\]") as raised:
        first_python_docstring_sentence(module)
    assert str(module) in str(raised.value)


def test_module_description_error_is_a_tree_render_error() -> None:
    """Existing ``TreeRenderError`` handlers keep catching description failures."""
    assert issubclass(ModuleDescriptionError, TreeRenderError)


def test_default_population_is_every_package_module_including_init() -> None:
    """``__init__.py`` first lines are folder rows, so the default listing carries them."""
    modules = docstring_module_paths([], DEFAULT_PACKAGE_DIR)
    assert DEFAULT_PACKAGE_DIR / "__init__.py" in modules
    assert DEFAULT_PACKAGE_DIR / "optimizer" / "__init__.py" in modules
    assert DEFAULT_PACKAGE_DIR / "optimizer" / "walker.py" in modules
    assert all("__pycache__" not in module.parts for module in modules)


def test_list_docstrings_text_flags_each_breaker_by_rule(
    fake_package: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One row per module, the rendered line verbatim, reasons indented under failures."""
    status = main(["--list-docstrings", str(fake_package)])
    lines = capsys.readouterr().out.splitlines()

    assert status == 1
    assert lines == [
        f"ok    {fake_package / '__init__.py'} (folder row): Fake package root.",
        f"FAIL  {fake_package / 'bare.py'}: <no first line>",
        f"      [{RULE_PRESENT}] is missing a module docstring.",
        f"ok    {fake_package / 'good.py'}: Good summary.",
        f"FAIL  {fake_package / 'shouty.py'}: Shouty summary!",
        lines[5],
        f"FAIL  {fake_package / 'sub' / '__init__.py'} (folder row): Subpackage, e.g. helpers.",
        lines[7],
    ]
    assert lines[5].startswith(f"      [{RULE_NOT_BANG_OR_QUESTION}] ")
    assert lines[7].startswith(f"      [{RULE_NO_EG_IE}] ")


def test_list_docstrings_json_carries_the_same_rows(
    fake_package: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON rows name the path, row kind, rendered line, and every broken rule."""
    status = main(
        [
            "--list-docstrings",
            str(fake_package / "good.py"),
            str(fake_package / "sub"),
            "--json",
        ],
    )
    payload = json.loads(capsys.readouterr().out)

    assert status == 1
    assert payload["total"] == 2
    assert payload["failing"] == 1
    assert [
        (
            row["path"],
            row["row"],
            row["line"],
            row["ok"],
        )
        for row in payload["modules"]
    ] == [
        (
            str(fake_package / "good.py"),
            "file",
            "Good summary.",
            True,
        ),
        (
            str(fake_package / "sub" / "__init__.py"),
            "folder",
            "Subpackage, e.g. helpers.",
            False,
        ),
    ]
    assert [violation["rule"] for violation in payload["modules"][1]["violations"]] == [
        RULE_NO_EG_IE,
    ]


def test_list_docstrings_passes_a_clean_selection(
    fake_package: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit 0 when every listed first line keeps the rule."""
    assert main(["--list-docstrings", str(fake_package / "good.py")]) == 0
    assert capsys.readouterr().out.startswith("ok    ")


@pytest.mark.parametrize("name", ["missing.py", "notes.txt"])
def test_list_docstrings_rejects_a_bad_path_as_a_caller_error(
    fake_package: Path,
    name: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A path that is absent or not a module exits 2, not the rule-violation code."""
    (fake_package / "notes.txt").write_text("notes\n", encoding="utf-8")
    assert main(["--list-docstrings", str(fake_package / name)]) == 2
    assert name in capsys.readouterr().err


def test_list_docstrings_and_check_are_exclusive() -> None:
    """Combining the modes is a caller error (argparse exit 2)."""
    with pytest.raises(SystemExit) as raised:
        main(["--list-docstrings", "--check"])
    assert raised.value.code == 2


def test_tree_row_paths_rebuilds_nested_repository_paths() -> None:
    """Rows inside fenced trees map to root label plus every parent directory."""
    lines = [
        "prose outside a tree",
        "```text",
        "pkg/                              # Root.",
        "\u251c\u2500\u2500 a.py                      # A.",
        "\u251c\u2500\u2500 sub/    # Sub.",
        "\u2502   \u2514\u2500\u2500 b.py                  # B.",
        "\u2514\u2500\u2500 last/    # Last.",
        "    \u2514\u2500\u2500 c.py                  # C.",
        "```",
    ]
    assert tree_row_paths(lines) == {
        2: "pkg/",
        3: "pkg/a.py",
        4: "pkg/sub/",
        5: "pkg/sub/b.py",
        6: "pkg/last/",
        7: "pkg/last/c.py",
    }


def test_stale_report_bounds_the_diff_by_hunk_count(tmp_path: Path) -> None:
    """Hunks past ``max_hunks`` are counted, not printed."""
    old = "\n".join(f"line {index}" for index in range(60))
    new = (
        old.replace("line 5", "LINE 5").replace("line 30", "LINE 30").replace("line 55", "LINE 55")
    )
    report = stale_report(tmp_path / "TREE.md", old, new, max_hunks=1)

    assert report[0] == "No tree row differs; the difference is in the generated prose."
    assert sum(line.startswith("@@") for line in report) == 1
    assert report[-1] == "... 2 more hunk(s) omitted; --max-hunks 0 prints all."


@pytest.fixture
def tree_doc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    """A TREE.md carrying a fresh render of the real package and fakeshop trees.

    The board read is replaced with an empty result: the real one bootstraps
    Django and widens process-wide settings, which would leak into every later
    test on this worker, and planned rows are not what these rows pin.
    """
    monkeypatch.setattr(build_tree_md, "fetch_planned_paths", list)
    md_path = tmp_path / "TREE.md"
    md_path.write_text(f"# Head kept verbatim\n\n{DELIMITER}\n", encoding="utf-8")
    rendered = render_tree_doc(md_path, DEFAULT_PACKAGE_DIR)
    md_path.write_text(rendered, encoding="utf-8")
    return md_path, rendered


def test_check_passes_a_fresh_file(
    tree_doc: tuple[Path, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The fixture's own render is up to date."""
    md_path, _ = tree_doc
    assert main(["--check", "--md", str(md_path)]) == 0
    assert "is up to date" in capsys.readouterr().out


def test_stale_check_names_the_module_whose_row_differs(
    tree_doc: tuple[Path, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A hand-edited row is named by repository path and shown in the diff."""
    md_path, rendered = tree_doc
    walker_summary = first_python_docstring_sentence(
        DEFAULT_PACKAGE_DIR / "optimizer" / "walker.py",
    )
    assert rendered.count(f"# {walker_summary}") == 2  # current tree + target layout
    md_path.write_text(
        rendered.replace(f"# {walker_summary}", "# Hand-edited summary.", 1),
        encoding="utf-8",
    )

    status = main(["--check", "--md", str(md_path)])
    err = capsys.readouterr().err

    assert status == 1
    assert "is not up to date" in err
    assert "Tree rows that differ (1):\n  django_strawberry_framework/optimizer/walker.py\n" in err
    diff_lines = err.splitlines()
    assert any(
        line.startswith("-") and "walker.py" in line and line.endswith("# Hand-edited summary.")
        for line in diff_lines
    )
    assert any(
        line.startswith("+") and "walker.py" in line and line.endswith(f"# {walker_summary}")
        for line in diff_lines
    )


def test_render_description_error_exits_1_naming_the_path(
    tree_doc: tuple[Path, str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A broken description is a documentation failure (1), not a stale file."""
    md_path, _ = tree_doc
    bad = PlannedPath(
        path="django_strawberry_framework/not_curated/",
        is_directory=True,
        card_id="TODO-1",
        card_title="First sentence. Second sentence",
    )
    monkeypatch.setattr(build_tree_md, "fetch_planned_paths", lambda: [bad])

    status = main(["--check", "--md", str(md_path)])
    err = capsys.readouterr().err

    assert status == 1
    assert "module description rule broken in" in err
    assert f"django_strawberry_framework/not_curated: [{RULE_ONE_SENTENCE}]" in err
    assert "is not up to date" not in err


def test_missing_delimiter_is_a_caller_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A TREE.md without the generated-section delimiter exits 2."""
    md_path = tmp_path / "TREE.md"
    md_path.write_text("# No delimiter here\n", encoding="utf-8")
    assert main(["--check", "--md", str(md_path)]) == 2
    assert "missing delimiter line" in capsys.readouterr().err


def test_missing_tree_file_exits_2_through_cli_exit(tmp_path: Path) -> None:
    """An absent ``--md`` file is an ``OSError``, which the shared CLI wrapper maps to 2."""
    with pytest.raises(SystemExit) as raised:
        build_tree_md.cli_exit(lambda: main(["--check", "--md", str(tmp_path / "absent.md")]))
    assert raised.value.code == 2
