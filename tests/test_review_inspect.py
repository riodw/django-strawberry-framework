"""Repo-tooling tests for the static review inspector ``scripts/review_inspect.py``.

The inspector parses a file without importing it and writes a line-preserving
stripped copy, a text overview, and optionally a JSON document. A live
``/graphql/`` request has no wire shape for generated review aids, so there is no
live sibling in ``examples/fakeshop/test_query/``. Every row runs against a
fixture package under ``tmp_path``.
"""

import json
import subprocess
from pathlib import Path

import pytest

from scripts import review_inspect

PACKAGE = "django_strawberry_framework"
REL_PATH = f"{PACKAGE}/sample.py"
STEM = f"{PACKAGE}__sample"

SAMPLE = '''"""Fixture module for the inspector."""

import re
from typing import TYPE_CHECKING, TypeVar

from django.conf import settings

if TYPE_CHECKING:
    hidden_call()

T = TypeVar("T")
PATTERN = re.compile(r"[0-9]+")
DEBUG = settings.DEBUG
registry_setup()


class Loader:
    """Load rows."""

    columns = make_columns()

    def resolve_items(self, info, rows):
        """Resolve items per row."""
        for row in rows:
            Item.objects.filter(pk=row)
        return self._load(rows)

    def _load(self, rows):
        # previously loaded rows one at a time; see walker.py:12 and walker.py::Walker.walk
        lookup = {}
        items = Item.objects.filter(pk__in=rows)
        for obj in Item.objects.filter(active=True):
            lookup.get(obj)
        return [row for row in items]

    async def afetch(self, rows, flag: bool, strict=False, *, kw=True):
        """Fetch rows"""
        return [await row.asave() for row in rows]


def build(model, plan):
    return model._meta.get_field("id"), plan.merge_metadata_from(model)


def test_behaviour():
    """Tests that the loader loads."""
'''

OTHER = """from .sample import build

VALUE = build(None, None)
"""


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _line_of(source: str, needle: str) -> int:
    matches = [index for index, line in enumerate(source.splitlines(), start=1) if needle in line]
    assert len(matches) == 1, (needle, matches)
    return matches[0]


def _run(tmp_path: Path, *extra: str, source: str = SAMPLE) -> tuple[Path, Path]:
    target = _write(tmp_path / REL_PATH, source)
    _write(tmp_path / PACKAGE / "other.py", OTHER)
    out_dir = tmp_path / "out"
    exit_code = review_inspect.main(
        [
            str(target),
            "--output-dir",
            str(out_dir),
            "--root",
            str(tmp_path),
            *extra,
        ],
    )
    assert exit_code == 0
    return target, out_dir


@pytest.fixture
def document(tmp_path: Path) -> dict:
    json_path = tmp_path / "sample.json"
    _run(tmp_path, "--json", str(json_path))
    return json.loads(json_path.read_text(encoding="utf-8"))


def _symbol(document: dict, qualname: str) -> dict:
    matches = [entry for entry in document["symbols"] if entry["qualname"] == qualname]
    assert len(matches) == 1, qualname
    return matches[0]


def test_text_mode_writes_only_the_overview_and_a_line_preserving_stripped_copy(
    tmp_path: Path,
) -> None:
    target, out_dir = _run(tmp_path)

    assert sorted(path.name for path in out_dir.iterdir()) == [
        f"{STEM}.overview.md",
        f"{STEM}.stripped.py",
    ]
    stripped = (out_dir / f"{STEM}.stripped.py").read_text(encoding="utf-8").splitlines()
    source = target.read_text(encoding="utf-8").splitlines()
    assert len(stripped) == len(source)
    line = _line_of(SAMPLE, "Item.objects.filter(pk=row)")
    assert stripped[line - 1] == source[line - 1]
    overview = (out_dir / f"{STEM}.overview.md").read_text(encoding="utf-8")
    assert "line numbers match the source line-for-line" in overview
    assert "not canonical" not in overview


def test_code_digest_moves_with_code_and_never_with_prose(tmp_path: Path, capsys) -> None:
    """A docstring, comment or layout edit keeps the digest; an executable edit moves it."""
    original = 'def f(x):\n    """Return x."""\n    return x  # plain\n'
    reworded = 'def f(x):\n    """Return ``x``\n\n    unchanged.\n    """\n\n    return x\n'
    changed = 'def f(x):\n    """Return x."""\n    return x + 1\n'
    paths = []
    for name, text in (("a.py", original), ("b.py", reworded), ("c.py", changed)):
        paths.append(tmp_path / name)
        paths[-1].write_text(text, encoding="utf-8")

    assert review_inspect.main(["--code-digest", *map(str, paths[:2])]) == 0
    assert review_inspect.main(["--code-digest", *map(str, paths)]) == 1

    digests = [line.split()[0] for line in capsys.readouterr().out.splitlines()[2:]]
    assert len(digests) == 3
    assert digests[0] == digests[1]
    assert digests[0] != digests[2]


def test_code_digest_reads_a_revision_path_from_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``<rev>:<path>`` is the committed text, digested like a file."""
    committed = "X = 1\n"
    (tmp_path / "m.py").write_text(committed, encoding="utf-8")
    for command in (
        ["init", "-q"],
        ["add", "m.py"],
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "m",
        ],
    ):
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                *command,
            ],
            check=True,
        )
    (tmp_path / "m.py").write_text("X = 2\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert review_inspect._read_digest_source("HEAD:m.py") == committed
    with pytest.raises(FileNotFoundError):
        review_inspect._read_digest_source("HEAD:missing.py")
    with pytest.raises(FileNotFoundError):
        review_inspect._read_digest_source("no-such-file.py")


def test_every_row_names_its_enclosing_symbol_or_module_line(tmp_path: Path) -> None:
    _target, out_dir = _run(tmp_path)
    overview = (out_dir / f"{STEM}.overview.md").read_text(encoding="utf-8")

    meta_line = _line_of(SAMPLE, "model._meta.get_field")
    assert f"- line {meta_line} `{REL_PATH}::build`: `_meta` in" in overview
    import_line = _line_of(SAMPLE, "import re")
    assert f'- line {import_line} `{REL_PATH} #"import re"`: `import re`' in overview
    comment_line = _line_of(SAMPLE, "# previously loaded")
    assert f"- line {comment_line} `{REL_PATH}::Loader._load`: `# previously" in overview


def test_meta_call_filter_matches_attribute_access_not_substring(document: dict) -> None:
    calls = [item["call"] for item in document["calls_of_interest"]["items"]]

    assert "model._meta.get_field" in calls
    assert "plan.merge_metadata_from" not in calls


@pytest.mark.parametrize(
    ("extra", "expect_notice"),
    [((), True), (("--no-cap",), False)],
)
def test_capped_sections_print_the_total_and_no_cap_lists_every_row(
    tmp_path: Path,
    extra: tuple[str, ...],
    expect_notice: bool,
) -> None:
    source = "".join(f"value_{index} = model._meta\n" for index in range(60))
    _target, out_dir = _run(tmp_path, *extra, source=source)
    overview = (out_dir / f"{STEM}.overview.md").read_text(encoding="utf-8")
    markers = overview.split("## Django / ORM markers", 1)[1].split("## Calls of interest", 1)[0]

    assert ("(10 more not shown; 60 total" in markers) is expect_notice
    assert markers.count("`_meta` in") == (50 if expect_notice else 60)


def test_json_header_carries_the_git_blob_id(tmp_path: Path, document: dict) -> None:
    target = tmp_path / REL_PATH
    expected = subprocess.run(
        ["git", "hash-object", str(target)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    header = document["header"]
    assert header["blob"] == expected
    assert header["blob_source"] == "git"
    assert header["path"] == REL_PATH
    assert header["line_count"] == len(SAMPLE.splitlines())
    assert header["generated_at"]
    assert review_inspect._sha1_blob_id(target.read_bytes()) == expected


def test_json_blob_id_falls_back_to_the_same_sha1_without_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _write(tmp_path / REL_PATH, SAMPLE)
    expected = review_inspect._blob_id(target)

    def _no_git(*args, **kwargs):
        raise OSError("git unavailable")

    monkeypatch.setattr(review_inspect.subprocess, "run", _no_git)

    assert review_inspect._blob_id(target) == (expected[0], "sha1")


def test_symbol_table_fields(document: dict) -> None:
    afetch = _symbol(document, "Loader.afetch")
    assert afetch["kind"] == "async method"
    assert afetch["is_public"] is True
    assert afetch["has_docstring"] is True
    assert afetch["docstring_first_line"] == "Fetch rows"
    assert afetch["parameter_count"] == 4
    assert afetch["positional_boolean_params"] == ["flag", "strict"]
    assert afetch["await_count"] == 1

    resolve = _symbol(document, "Loader.resolve_items")
    assert (resolve["def_line"], resolve["end_line"]) == (
        _line_of(SAMPLE, "def resolve_items"),
        _line_of(SAMPLE, "return self._load(rows)"),
    )
    assert resolve["code_lines"] == 4
    assert resolve["max_nesting_depth"] == 1
    assert resolve["first_party_calls"] == ["self._load"]
    assert resolve["hot_entry_reasons"] == ["name `resolve_items`", "`info` parameter"]

    load = _symbol(document, "Loader._load")
    assert load["is_public"] is False
    assert [call["reason"] for call in load["db_calls"]] == ["orm:.filter", "orm:.filter"]

    build = _symbol(document, "build")
    assert build["kind"] == "function"
    assert build["has_docstring"] is False
    assert build["callers_approximate"] is True
    assert f'{PACKAGE}/other.py #"VALUE = build(None, None)"' in build["callers"]
    assert _symbol(document, "Loader")["kind"] == "class"


def test_per_row_leads_flag_loop_bodies_only(document: dict) -> None:
    per_row = {
        (lead["where"], lead["line"]): lead for lead in document["performance_leads"]["per_row"]
    }

    positive = per_row[(f"{REL_PATH}::Loader.resolve_items", _line_of(SAMPLE, "filter(pk=row)"))]
    assert positive["reason"] == "orm:.filter"
    assert positive["loop"] == {"kind": "for", "line": _line_of(SAMPLE, "for row in rows:")}
    awaited = per_row[(f"{REL_PATH}::Loader.afetch", _line_of(SAMPLE, "await row.asave()"))]
    assert awaited["loop"]["kind"] == "comprehension"

    # Negative controls: a queryset call outside any loop, a loop iterable (evaluated
    # once), and ``dict.get(key)`` inside a loop body are not per-row work.
    lines = {line for _where, line in per_row}
    assert _line_of(SAMPLE, "filter(pk__in=rows)") not in lines
    assert _line_of(SAMPLE, "filter(active=True)") not in lines
    assert _line_of(SAMPLE, "lookup.get(obj)") not in lines
    assert len(per_row) == 2


def test_hot_path_reachability_follows_self_calls(document: dict) -> None:
    leads = document["performance_leads"]

    entries = [entry["where"] for entry in leads["hot_entry_points"]]
    assert f"{REL_PATH}::Loader.resolve_items" in entries
    assert {"where": f"{REL_PATH}::Loader._load", "via": f"{REL_PATH}::Loader.resolve_items"} in (
        leads["hot_reachable"]
    )


def test_import_time_work_lists_module_and_class_body_calls(document: dict) -> None:
    rows = {
        (row["line"], row["kind"], row["text"])
        for row in document["performance_leads"]["import_time"]
    }

    assert rows == {
        (_line_of(SAMPLE, "PATTERN = re.compile"), "regex-compile", "re.compile"),
        (_line_of(SAMPLE, "DEBUG = settings.DEBUG"), "settings-read", "settings.DEBUG"),
        (_line_of(SAMPLE, "registry_setup()"), "call", "registry_setup"),
        (_line_of(SAMPLE, "columns = make_columns()"), "call", "make_columns"),
    }


def test_comments_census_flags(document: dict) -> None:
    census = {(entry["kind"], entry["owner"]): entry for entry in document["comments_census"]}

    comment = census[("comment", "Loader._load")]
    assert "previously" in comment["flags"]["provenance"]
    assert comment["flags"]["line-cite"] == ["walker.py:12"]
    assert comment["flags"]["symbol-cite"] == ["walker.py::Walker.walk"]
    assert census[("docstring", "test_behaviour")]["flags"]["test-docstring-prefix"] == ["Tests"]
    assert census[("missing-docstring", "build")]["flags"] == {"public-no-docstring": ["build"]}
    assert census[("docstring", "Loader.afetch")]["flags"] == {
        "first-line-no-period": ["Fetch rows"],
    }
    # Negative control: a present-tense docstring ending in a period carries no flag.
    assert census[("docstring", "Loader")]["flags"] == {}
    assert ("missing-docstring", "Loader._load") not in census
