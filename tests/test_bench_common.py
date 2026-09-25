"""Script tests for the measurement plumbing the bench scripts share.

Keeps the database-free half of ``scripts/_bench_common.py`` (provenance
refusals, the package content digest and instrument blob ids, round summaries,
the ``--json`` document shape, the plan-cache reset guard, root-row counting)
and the ``-X importtime`` parser in
``scripts/importtime_report.py``. None of it has a wire shape: it is tooling
that measures the package, so there is no live sibling in
``examples/fakeshop/test_query/``. No test here opens a database or calls
``bootstrap_fakeshop_django`` past its mode check.
"""

import importlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import _bench_common

SCRIPTS = Path(_bench_common.__file__).resolve().parent

IMPORTTIME_FIXTURE = """\
import time: self [us] | cumulative | imported package
import time:       117 |        117 |   _io
import time:       900 |       3100 |     django.db
import time:      2100 |       2100 |       psycopg
import time:       289 |        289 |     django_strawberry_framework.exceptions
import time:       904 |        904 |           django_strawberry_framework.utils.relations
import time:      1361 |       3242 |     django_strawberry_framework.keyset
import time:       368 |       9000 | django_strawberry_framework
not an importtime line
"""


@pytest.fixture
def package_tree(tmp_path):
    """Build a small package tree: nested ``.py`` files plus a non-Python data file."""
    root = tmp_path / "pkg"
    (root / "sub").mkdir(parents=True)
    (root / "__init__.py").write_bytes(b"VALUE = 1\n")
    (root / "a.py").write_bytes(b"def a():\n    return 1\n")
    (root / "sub" / "__init__.py").write_bytes(b"")
    (root / "sub" / "b.py").write_bytes(b"B = 'b'\n")
    (root / "README.txt").write_bytes(b"not python\n")
    return root


@pytest.fixture
def importtime_report(monkeypatch):
    """Import ``scripts/importtime_report.py`` the way it runs: scripts dir on ``sys.path``."""
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("importtime_report")


def test_summarize_rounds_reports_fastest_sample_median_of_medians_and_spread():
    """``min`` is the fastest sample, ``median`` the median of round medians, ``spread`` their range."""
    summary = _bench_common.summarize_rounds([[1, 2, 3], [4, 5, 6], [2, 3, 4]])

    assert summary == {
        "min": 1,
        "median": 3,
        "spread": 3,
        "spread_pct": 100.0,
    }


@pytest.mark.parametrize("rounds", [[], [[1, 2], []]])
def test_summarize_rounds_refuses_an_empty_round(rounds):
    """A missing round has no median, so the summary refuses instead of reporting zero."""
    with pytest.raises(ValueError, match="non-empty round"):
        _bench_common.summarize_rounds(rounds)


def test_report_json_carries_header_rows_and_status_with_sorted_keys(tmp_path):
    """The written report has one fixed shape and sorted keys, so two runs diff line by line."""
    report = _bench_common.build_report(
        tool="bench_x",
        provenance={"package_file": "/tree/pkg/__init__.py", "db_name": "file:x"},
        params={"rounds": 3, "iterations": 10},
        rows=[{"label": "q", "status": "error"}],
        failures=["q: boom"],
    )
    path = tmp_path / "report.json"

    _bench_common.write_report(path, report)

    text = path.read_text(encoding="utf-8")
    loaded = json.loads(text)
    assert list(loaded) == [
        "failures",
        "header",
        "rows",
        "status",
    ]
    assert list(loaded["header"]) == ["params", "provenance", "tool"]
    assert list(loaded["header"]["params"]) == ["iterations", "rounds"]
    assert loaded["status"] == "failed"
    assert loaded["header"]["tool"] == "bench_x"
    assert text == json.dumps(loaded, indent=2, sort_keys=True) + "\n"


def test_report_status_is_ok_without_failures():
    """A run with no errored or skipped row reports ``ok``."""
    report = _bench_common.build_report(tool="t", provenance={}, params={}, rows=[], failures=[])

    assert report["status"] == "ok"


def test_memory_db_name_is_a_shared_cache_uri_per_alias():
    """Every alias gets its own named shared-cache in-memory database."""
    name = _bench_common.memory_db_name("default")

    assert name == "file:dsf-bench-default?mode=memory&cache=shared"
    assert _bench_common.is_memory_db_name(name)
    assert _bench_common.is_memory_db_name(":memory:")
    assert not _bench_common.is_memory_db_name("/tmp/db.sqlite3")
    assert name != _bench_common.memory_db_name("shard_b")


def test_tracked_database_is_refused_and_other_names_pass(tmp_path):
    """Only a NAME resolving to the tracked fixture raises."""
    with pytest.raises(RuntimeError, match="tracked fixture"):
        _bench_common.assert_not_tracked_db(_bench_common.TRACKED_DB)

    _bench_common.assert_not_tracked_db(_bench_common.memory_db_name("default"))
    _bench_common.assert_not_tracked_db(tmp_path / "db.sqlite3")
    _bench_common.assert_not_tracked_db("fakeshop")


def test_package_outside_the_running_tree_is_refused(tmp_path):
    """A package file outside the script's tree raises; one inside passes."""
    with pytest.raises(RuntimeError, match="outside the running tree"):
        _bench_common.assert_package_in_tree(tmp_path / "pkg" / "__init__.py")

    _bench_common.assert_package_in_tree(_bench_common.REPO_ROOT / "pkg" / "__init__.py")


def test_package_digest_is_stable_and_ignores_non_python_files(package_tree):
    """Hashing one tree twice gives one digest; a non-``.py`` file is outside it."""
    first = _bench_common.package_digest(package_tree)

    assert first.startswith("sha256:")
    assert _bench_common.package_digest(package_tree) == first
    (package_tree / "README.txt").write_bytes(b"edited\n")
    assert _bench_common.package_digest(package_tree) == first


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda root: (root / "sub" / "b.py").write_bytes(b"B = 'c'\n"), id="bytes"),
        pytest.param(lambda root: (root / "a.py").rename(root / "c.py"), id="rename"),
        pytest.param(lambda root: (root / "sub" / "new.py").write_bytes(b""), id="added"),
    ],
)
def test_package_digest_changes_when_a_package_file_changes(package_tree, mutate):
    """Changing any ``.py`` file's bytes, path or presence moves the digest."""
    before = _bench_common.package_digest(package_tree)

    mutate(package_tree)

    assert _bench_common.package_digest(package_tree) != before


def test_package_digest_is_independent_of_file_system_order(package_tree, monkeypatch):
    """Files enumerated in the reverse order hash to the same digest."""
    forward = _bench_common.package_digest(package_tree)
    original_rglob = Path.rglob
    seen: list[list[str]] = []

    def reversed_rglob(self, pattern, *args, **kwargs):
        paths = sorted(original_rglob(self, pattern, *args, **kwargs), reverse=True)
        seen.append([path.name for path in paths])
        return iter(paths)

    monkeypatch.setattr(Path, "rglob", reversed_rglob)

    assert _bench_common.package_digest(package_tree) == forward
    assert seen == [
        [
            "b.py",
            "__init__.py",
            "a.py",
            "__init__.py",
        ],
    ]


def test_package_digest_refuses_a_tree_without_python_files(tmp_path):
    """An empty population raises instead of fingerprinting nothing."""
    with pytest.raises(ValueError, match="no .py file"):
        _bench_common.package_digest(tmp_path)


def test_git_blob_id_matches_git_hash_object(tmp_path):
    """The blob id computed without a repository equals ``git hash-object``."""
    path = tmp_path / "script.py"
    path.write_bytes(b"print('bench')\n\x00binary tail")
    completed = subprocess.run(
        ["git", "hash-object", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )

    assert _bench_common.git_blob_id(path) == completed.stdout.strip()


def test_instrument_ids_name_the_script_and_the_shared_module_by_tree_path():
    """Both instrument files are keyed by path relative to the tree, sorted."""
    script = SCRIPTS / "bench_plan_cache.py"

    ids = _bench_common.instrument_ids(script)

    assert ids == {
        "scripts/_bench_common.py": _bench_common.git_blob_id(_bench_common.BENCH_COMMON),
        "scripts/bench_plan_cache.py": _bench_common.git_blob_id(script),
    }
    assert _bench_common.instrument_ids(None)["__main__"] == "unavailable"


def test_provenance_dict_carries_the_digest_and_instrument_ids_as_a_mapping():
    """The ``--json`` provenance adds ``package_digest`` and an ``instrument_ids`` object."""
    provenance = _bench_common.BenchProvenance(
        package_file="/tree/django_strawberry_framework/__init__.py",
        package_digest="sha256:abc",
        instrument_ids=(("scripts/_bench_common.py", "1" * 40), ("scripts/x.py", "2" * 40)),
        repo_root="/tree",
        git_head="unavailable",
        settings_module="config.settings",
        db_alias="default",
        db_vendor="sqlite",
        db_name="file:x",
        python="3",
        django="5",
        strawberry="0",
        platform="p",
    )

    as_dict = provenance.as_dict()

    assert as_dict["package_digest"] == "sha256:abc"
    assert as_dict["instrument_ids"] == {
        "scripts/_bench_common.py": "1" * 40,
        "scripts/x.py": "2" * 40,
    }
    assert json.loads(json.dumps(as_dict)) == as_dict
    lines = provenance.lines()
    assert "  digest    sha256:abc" in lines
    assert f"  script    scripts/x.py blob {'2' * 40}" in lines


def test_bootstrap_refuses_an_unknown_mode_before_touching_django():
    """A mistyped mode raises ``ValueError`` naming the real modes."""
    with pytest.raises(ValueError, match="sqlite-memory"):
        _bench_common.bootstrap_fakeshop_django("sqlite")


def test_reset_plan_cache_clears_the_plan_cache_and_the_document_key_cache(monkeypatch):
    """The reset leaves both optimizer caches empty and the counters zeroed."""
    from collections import OrderedDict

    from graphql import parse

    import django_strawberry_framework.optimizer.extension as extension_module
    from django_strawberry_framework import DjangoOptimizerExtension

    monkeypatch.setattr(extension_module, "_doc_key_cache", OrderedDict())
    extension_module._doc_cache_entry(parse("query Q { field }").definitions[0], {})
    optimizer = DjangoOptimizerExtension()
    optimizer._plan_cache["k"] = "plan"
    optimizer._cache_hits, optimizer._cache_misses = 4, 2

    _bench_common.reset_plan_cache(optimizer)

    assert optimizer.cache_info() == (0, 0, 0)
    assert len(extension_module._doc_key_cache) == 0


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"allThings": [1, 2, 3]}, 3),
        ({"allItems": {"edges": [{}, {}]}}, 2),
        ({"scalar": 1}, None),
        (None, None),
    ],
)
def test_root_row_count_reads_the_first_list_or_connection(data, expected):
    """Root rows come from the first list field or a connection's ``edges``."""
    assert _bench_common.root_row_count(data) == expected


def test_parse_variables_accepts_an_object_and_refuses_other_json():
    """``--variables`` must be a JSON object."""
    assert _bench_common.parse_variables('{"first": 2}') == {"first": 2}
    assert _bench_common.parse_variables(None) is None
    with pytest.raises(TypeError, match="JSON object"):
        _bench_common.parse_variables("[1, 2]")


def test_importtime_parser_reads_times_names_and_depth(importtime_report):
    """Each ``import time`` line becomes a row; the header and other output are skipped."""
    rows = importtime_report.parse_importtime(IMPORTTIME_FIXTURE)

    assert [row.name for row in rows] == [
        "_io",
        "django.db",
        "psycopg",
        "django_strawberry_framework.exceptions",
        "django_strawberry_framework.utils.relations",
        "django_strawberry_framework.keyset",
        "django_strawberry_framework",
    ]
    by_name = {row.name: row for row in rows}
    assert (by_name["psycopg"].self_us, by_name["psycopg"].cumulative_us) == (2100, 2100)
    assert by_name["django_strawberry_framework"].depth == 0
    assert by_name["_io"].depth == 1
    assert by_name["django_strawberry_framework.utils.relations"].depth == 5


def test_importtime_summary_takes_per_module_minimum_and_groups_by_top_level(importtime_report):
    """Figures are per-module minima; non-package imports are summed per top-level name."""
    rounds = [
        importtime_report.parse_importtime(IMPORTTIME_FIXTURE),
        importtime_report.parse_importtime(
            IMPORTTIME_FIXTURE.replace("368 |       9000", "400 |       8000"),
        ),
    ]

    body = importtime_report.summarize(importtime_report.min_across_rounds(rounds), top=2)

    assert body["package_cumulative_us"] == 8000
    assert body["package_modules"] == 4
    assert body["package_self_us"] == 368 + 289 + 904 + 1361
    assert [row["module"] for row in body["top_by_cumulative"]] == [
        "django_strawberry_framework",
        "django_strawberry_framework.keyset",
    ]
    assert len(body["all_by_cumulative"]) == body["package_modules"]
    assert body["all_by_cumulative"][:2] == body["top_by_cumulative"]
    assert body["top_by_self"][0] == {
        "cumulative_us": 3242,
        "module": "django_strawberry_framework.keyset",
        "self_us": 1361,
    }
    assert body["top_level_self"] == [
        {"name": "psycopg", "self_us": 2100},
        {"name": "django", "self_us": 900},
    ]
