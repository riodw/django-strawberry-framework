"""Script tests for the N+1 detector's verdict and comparison logic.

Keeps the database-free half of ``scripts/count_queries.py``: the verdict a
list of per-cardinality query counts earns, the root-row growth gate that
decides whether a verdict is evidence, ``--cardinalities`` parsing, and the
``--compare`` delta and refusal. The counts are synthetic; the seeding and
execution half needs the fakeshop database and is exercised by running the
script in a workspace copy. There is no live sibling in
``examples/fakeshop/test_query/``: the script measures the package, it is not
reached by a query.
"""

import importlib
from pathlib import Path
from types import ModuleType

import pytest

from scripts import _bench_common

SCRIPTS = Path(_bench_common.__file__).resolve().parent


@pytest.fixture
def count_queries(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Import ``scripts/count_queries.py`` the way it runs: scripts dir on ``sys.path``."""
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("count_queries")


@pytest.mark.parametrize(
    ("counts", "verdict"),
    [
        ([4, 4, 4], "batched"),
        ([4, 4], "batched"),
        ([37, 73, 148], "scales with cardinality"),
        ([4, 5], "scales with cardinality"),
        ([4, 4, 5], "mixed"),
        ([5, 4, 6], "mixed"),
        ([6, 5, 4], "mixed"),
    ],
)
def test_counts_classify_by_shape_across_cardinalities(
    count_queries: ModuleType,
    counts: list[int],
    verdict: str,
):
    """Equal counts are batched, a rise at every step scales, anything else is mixed."""
    assert count_queries.classify_counts(counts) == verdict


def test_one_count_has_no_verdict(count_queries: ModuleType):
    """A single cardinality cannot show a shape, so classification refuses."""
    with pytest.raises(ValueError, match="two or more"):
        count_queries.classify_counts([4])


@pytest.mark.parametrize(
    ("root_rows", "grew"),
    [
        ([6, 12, 27], True),
        ([6, 12, 12], False),
        ([100, 100], False),
        ([6, None], False),
    ],
)
def test_verdict_is_evidence_only_when_root_rows_grew(
    count_queries: ModuleType,
    root_rows: list[int | None],
    grew: bool,
):
    """Flat or unknown root rows mean the added parents never reached a resolver."""
    assert count_queries.rows_grew(root_rows) is grew


def test_cardinalities_parse_sorted_and_refuse_zero_or_repeats(count_queries: ModuleType):
    """Cells run ascending; 0 fakes a slope and a repeat measures nothing new."""
    assert count_queries.parse_cardinalities("30,2,10") == [2, 10, 30]
    with pytest.raises(ValueError, match="positive"):
        count_queries.parse_cardinalities("0,2")
    with pytest.raises(ValueError, match="distinct"):
        count_queries.parse_cardinalities("2,2,10")


def _report(
    counts: list[int],
    *,
    sha1: str = "abc",
    name: str | None = None,
    verdict: str = "batched",
):
    report = _bench_common.build_report(
        tool="count_queries",
        provenance={"package_file": "/tree/pkg/__init__.py"},
        params={
            "graphql_operation_name": name,
            "operation_sha1": sha1,
            "optimizer": True,
            "seeder": "products",
        },
        rows=[
            {"cardinality": n, "queries": q, "root_rows": n * 6}
            for n, q in zip((2, 10, 30), counts, strict=False)
        ],
        failures=[],
    )
    report["verdict"] = verdict
    return report


def test_compare_prints_per_cardinality_deltas_and_both_verdicts(count_queries: ModuleType):
    """Each cardinality shows before, after and signed delta, then the verdict change."""
    before = _report([4, 4, 4])
    after = _report([4, 13, 33], verdict="scales with cardinality")

    lines = count_queries.compare_reports(before, after)

    assert lines == [
        "    N  before   after   delta",
        "    2       4       4      +0",
        "   10       4      13      +9",
        "   30       4      33     +29",
        "verdict: batched -> scales with cardinality",
    ]


@pytest.mark.parametrize(
    ("before", "after", "key"),
    [
        (("abc", None), ("def", None), "operation_sha1"),
        (("abc", "One"), ("abc", "Two"), "graphql_operation_name"),
        (("abc", None), ("abc", "Two"), "graphql_operation_name"),
    ],
)
def test_compare_refuses_a_different_operation(
    count_queries: ModuleType,
    before: tuple[str, str | None],
    after: tuple[str, str | None],
    key: str,
):
    """Deltas between two operations mean nothing, so the comparison refuses.

    One document can hold several operations, so the same fingerprint run
    under another operation name is a different measurement.
    """
    baseline = _report([4, 4, 4], sha1=before[0], name=before[1])
    current = _report([4, 4, 4], sha1=after[0], name=after[1])

    with pytest.raises(ValueError, match=key):
        count_queries.compare_reports(baseline, current)


@pytest.mark.parametrize(
    ("document", "operation_name", "effective"),
    [
        ("{ allItems { name } }", None, None),
        ("query One { allItems { name } }", None, "One"),
        ("query One { allItems { name } }", "One", "One"),
        ("query One { a } query Two { b }", None, "One"),
        ("query One { a } query Two { b }", "Two", "Two"),
        ("fragment F on Item { name } query Two { b }", None, "Two"),
        ("query {", None, None),
    ],
)
def test_effective_operation_name_is_the_one_executed(
    count_queries: ModuleType,
    document: str,
    operation_name: str | None,
    effective: str | None,
):
    """A missing name runs the first operation, so a named single operation compares alike."""
    assert count_queries.effective_operation_name(document, operation_name) == effective


def test_builtin_operations_name_a_known_seeder(count_queries: ModuleType):
    """Every built-in operation seeds rows its root field reads."""
    assert {op.seeder for op in count_queries.BUILTIN_OPERATIONS.values()} <= {
        "products",
        "library",
        "glossary",
    }
