"""Script tests for the ``path::Symbol`` citation gate.

Repo tooling: these rows pin ``scripts/check_citations.py`` (symbol resolution,
the function-body, dunder and wrapped-line rules, the ``--paths`` / ``--json`` /
``--substrings`` / ``--cited-by`` reviewer flags, and the default gate's exit
codes). A CLI that reads source text has no ``/graphql/`` wire shape, so there is
no live sibling in ``examples/fakeshop/test_query/``.

``REPO_ROOT`` is monkeypatched to a ``tmp_path`` fake tree, so no row reads the
real repository.
"""

import json
import textwrap

import pytest

from scripts import check_citations

MODULE = '''\
"""Fixture module."""

import os as operating_system

LIMIT = 3
__all__ = ["Widget", "build"]


class Widget:
    """A widget."""

    size: int = 1

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    def render(self):
        rendered_markup = "<widget/>"
        return rendered_markup


def build(count):
    scratch_total = count * 2

    def inner_factory():
        return scratch_total

    return inner_factory
'''


def _write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """Build a fake repo with the four source trees, a board and docs."""
    monkeypatch.setattr(check_citations, "REPO_ROOT", tmp_path)
    for name in check_citations.SOURCE_TREES:
        (tmp_path / name).mkdir()
    _write(tmp_path, "django_strawberry_framework/widgets.py", MODULE)
    _write(tmp_path, "KANBAN.md", "# Board\n")
    return tmp_path


def _cite(root, text, name="tests/test_citer.py"):
    """Write one citing source and return its checked outcomes."""
    source = _write(root, name, text)
    corpus = check_citations.iter_python_sources()
    index = check_citations.suffix_index(corpus)
    return check_citations.evaluate_source(
        source,
        corpus,
        index,
        require_file=True,
        substrings=True,
    )


def _verdicts(outcomes):
    return [(outcome.citation.text, outcome.resolved) for outcome in outcomes]


def test_module_and_class_scope_bindings_resolve(tree):
    outcomes = _cite(
        tree,
        """\
        # widgets.py::Widget widgets.py::Widget.render widgets.py::Widget.size
        # widgets.py::LIMIT widgets.py::operating_system widgets.py::build
        """,
    )
    assert all(resolved for _, resolved in _verdicts(outcomes))
    assert len(outcomes) == 6


def test_a_function_local_variable_is_not_citable(tree):
    outcomes = _cite(
        tree,
        """\
        # widgets.py::scratch_total widgets.py::build.scratch_total
        # widgets.py::rendered_markup widgets.py::Widget.render.rendered_markup
        """,
    )
    assert _verdicts(outcomes) == [
        ("widgets.py::scratch_total", False),
        ("widgets.py::build.scratch_total", False),
        ("widgets.py::rendered_markup", False),
        ("widgets.py::Widget.render.rendered_markup", False),
    ]


def test_a_nested_def_inside_a_function_stays_citable(tree):
    outcomes = _cite(tree, "# widgets.py::inner_factory widgets.py::build.inner_factory\n")
    assert _verdicts(outcomes) == [
        ("widgets.py::inner_factory", True),
        ("widgets.py::build.inner_factory", True),
    ]


BLOCKS_MODULE = """\
try:
    from fast_backend import accelerate
except ImportError:
    FALLBACK_LIMIT = 1


def outer(value):
    with open(value) as handle:
        def in_with():
            return handle
        block_local = 2
    for _ in range(value):
        class InFor:
            pass
    match value:
        case 1:
            def in_case():
                return block_local
"""


def test_a_name_bound_inside_a_compound_block_is_citable_and_a_local_still_is_not(tree):
    _write(tree, "django_strawberry_framework/blocks.py", BLOCKS_MODULE)
    outcomes = _cite(
        tree,
        """\
        # blocks.py::FALLBACK_LIMIT blocks.py::outer.in_with blocks.py::outer.InFor
        # blocks.py::outer.in_case blocks.py::outer.block_local
        """,
    )
    assert _verdicts(outcomes) == [
        ("blocks.py::FALLBACK_LIMIT", True),
        ("blocks.py::outer.in_with", True),
        ("blocks.py::outer.InFor", True),
        ("blocks.py::outer.in_case", True),
        ("blocks.py::outer.block_local", False),
    ]


def test_a_dunder_is_resolved_as_one_symbol_not_skipped_as_a_family(tree):
    outcomes = _cite(
        tree,
        """\
        # widgets.py::__all__ widgets.py::Widget.__init_subclass__
        # widgets.py::Widget.__post_init__ widgets.py::Widget.re_ widgets.py::Widget.
        """,
    )
    assert [(o.citation.text, o.citation.kind, o.resolved) for o in outcomes] == [
        ("widgets.py::__all__", "dunder", True),
        ("widgets.py::Widget.__init_subclass__", "dunder", True),
        ("widgets.py::Widget.__post_init__", "dunder", False),
    ]


def test_a_citation_wrapped_after_the_double_colon_is_joined(tree):
    outcomes = _cite(
        tree,
        """\
        # See ``django_strawberry_framework/widgets.py::
        #   Widget.render`` and ``widgets.py::``
        #   ``missing_symbol`` for the contract.
        """,
    )
    assert [(o.citation.line, o.citation.text, o.resolved) for o in outcomes] == [
        (1, "django_strawberry_framework/widgets.py::Widget.render", True),
        (2, "widgets.py::missing_symbol", False),
    ]


def test_a_citation_wrapped_inside_its_path_is_joined_once(tree):
    outcomes = _cite(
        tree,
        """\
        # the helper in django_strawberry_framework/
        #   widgets.py::build is shared.
        """,
    )
    assert [(o.citation.line, o.citation.text) for o in outcomes] == [
        (1, "django_strawberry_framework/widgets.py::build"),
    ]
    assert outcomes[0].resolved


def test_iter_citations_keeps_its_tuple_shape(tree):
    text = "# widgets.py::build and widgets.py::\n#   LIMIT\n"
    assert list(check_citations.iter_citations(text)) == [
        (1, "widgets.py", "build"),
        (1, "widgets.py", "LIMIT"),
    ]


def test_default_run_gates_the_corpus_and_board(tree, capsys):
    _write(tree, "tests/test_citer.py", "# widgets.py::build\n")
    _write(tree, "KANBAN.md", "planned `later.py::Thing`, real `widgets.py::Widget`\n")
    assert check_citations.main([]) == 0
    assert capsys.readouterr().out == (
        "OK: 3 citations resolve (1 in 2 .py files, 2 in KANBAN.md).\n"
    )
    _write(tree, "examples/broken.py", "# widgets.py::gone\n")
    assert check_citations.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("FAIL: 1 unresolvable citation(s) of 4 checked")
    assert "examples/broken.py:1: cites `widgets.py::gone`" in out


def test_paths_checks_only_the_named_files(tree, capsys):
    _write(tree, "tests/test_good.py", "# widgets.py::build widgets.py::LIMIT\n")
    _write(tree, "tests/test_bad.py", "# widgets.py::gone\n")
    _write(tree, "docs/notes.md", "cites `widgets.py::Widget` and `nowhere.py::X`\n")

    assert check_citations.main(["--paths", "tests/test_good.py"]) == 0
    assert capsys.readouterr().out == "OK: 2 citations resolve (2 in 1 named file(s)).\n"

    assert check_citations.main(["--paths", "docs/notes.md"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("FAIL: 1 unresolvable citation(s) of 2 checked (2 in 1 named file(s))")
    assert "nowhere.py::X` -- no such file" in out


def test_paths_refuses_a_missing_file(tree):
    with pytest.raises(check_citations.CitationCheckError, match="no such file"):
        check_citations.main(["--paths", "tests/absent.py"])


def test_json_reports_every_citation_with_its_verdict(tree, capsys):
    _write(tree, "tests/test_citer.py", "# widgets.py::build widgets.py::Widget.gone\n")
    assert check_citations.main(["--paths", "tests/test_citer.py", "--json"]) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err.startswith("FAIL: 1 unresolvable citation(s) of 2 checked")
    assert (payload["checked"], payload["violations"]) == (2, 1)
    ok, bad = payload["citations"]
    assert ok["file"] == "tests/test_citer.py"
    assert (ok["symbol"], ok["kind"], ok["resolved"]) == ("build", "symbol", True)
    assert ok["target"] == "django_strawberry_framework/widgets.py"
    assert (bad["resolved"], bad["violation"], bad["target"]) == (False, True, None)
    assert bad["now_lives_in"] == []


def test_json_hint_names_where_a_moved_symbol_now_lives(tree, capsys):
    _write(tree, "tests/helpers.py", "def relocated():\n    pass\n")
    _write(tree, "tests/test_citer.py", "# widgets.py::relocated\n")
    check_citations.main(["--paths", "tests/test_citer.py", "--json"])
    (record,) = json.loads(capsys.readouterr().out)["citations"]
    assert record["now_lives_in"] == ["tests/helpers.py"]


def test_substrings_are_off_by_default(tree, capsys):
    _write(tree, "tests/test_citer.py", '# widgets.py::build #"not in the body"\n')
    assert check_citations.main(["--paths", "tests/test_citer.py"]) == 0
    assert capsys.readouterr().out == "OK: 1 citations resolve (1 in 1 named file(s)).\n"


def test_substring_pinpoints_resolve_inside_the_symbol_or_the_file(tree):
    _write(tree, "docs/guide.md", "## Coverage rule\nText.\n")
    outcomes = _cite(
        tree,
        """\
        # widgets.py::build #"scratch_total = count * 2"
        # widgets.py::Widget.render #"scratch_total = count * 2"
        # widgets.py #"LIMIT = 3"
        # docs/guide.md #"Coverage rule"
        # docs/guide.md #"Retired heading"
        # widgets.py::build #"return"
        """,
    )
    pinpoints = [o for o in outcomes if o.citation.kind == "substring"]
    assert [(o.citation.line, o.resolved) for o in pinpoints] == [
        (1, True),
        (2, False),
        (3, True),
        (4, True),
        (5, False),
        (6, True),
    ]
    outside, missing = pinpoints[1], pinpoints[4]
    assert outside.hint == ("django_strawberry_framework/widgets.py::build",)
    assert missing.hint == ()
    assert pinpoints[5].warning is not None
    assert all(o.warning is None for o in pinpoints[:5])


def test_substrings_flag_fails_the_run_and_warns_on_ambiguity(tree, capsys):
    _write(
        tree,
        "tests/test_citer.py",
        '# widgets.py::build #"return"\n# widgets.py::build #"retired text"\n',
    )
    assert check_citations.main(["--paths", "tests/test_citer.py", "--substrings"]) == 1
    out = capsys.readouterr().out
    assert out.startswith(
        "FAIL: 1 unresolvable citation(s) of 4 checked "
        "(4 in 1 named file(s); 2 of them substring pinpoints):",
    )
    assert 'widgets.py::build #"retired text"` -- the quoted text does not occur' in out
    assert "WARN: 1 ambiguous pinpoint(s):" in out


def test_cited_by_marks_gated_and_ungated_citers(tree, capsys):
    _write(tree, "tests/test_citer.py", "# widgets.py::Widget.render widgets.py::build\n")
    _write(tree, "KANBAN.md", "board cites `widgets.py::Widget`\n")
    _write(tree, "docs/design.md", "design cites `widgets.py::Widget.size`\n")
    _write(tree, "docs/builder/bld-050-x.md", "cycle cites `widgets.py::Widget`\n")
    _write(tree, "docs/review/rev-widgets.comments.md", "cites `widgets.py::Widget`\n")
    _write(tree, "docs/SPECS/spec-001-x.md", "archive cites `widgets.py::Widget`\n")
    _write(tree, "tests/test_pin.py", '# widgets.py #"size: int = 1"\n')

    target = "django_strawberry_framework/widgets.py::Widget"
    assert check_citations.main(["--cited-by", target]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[:-1] == [
        "tests/test_citer.py:1: `widgets.py::Widget.render` [gated] resolved (symbol)",
        'tests/test_pin.py:1: `widgets.py #"size: int = 1"` [ungated] resolved (substring)',
        "KANBAN.md:1: `widgets.py::Widget` [gated] resolved (symbol)",
        "docs/design.md:1: `widgets.py::Widget.size` [ungated] resolved (symbol)",
    ]
    assert lines[-1].startswith(
        f"4 citing site(s) of `{target}` (2 gated, 2 ungated, 0 unresolved)",
    )


def test_cited_by_json_carries_the_gated_flag(tree, capsys):
    _write(tree, "tests/test_citer.py", "# widgets.py::build\n")
    _write(tree, "docs/design.md", "cites `widgets.py::LIMIT`\n")
    check_citations.main(["--cited-by", "django_strawberry_framework/widgets.py", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert [(row["file"], row["gated"]) for row in payload["citers"]] == [
        ("tests/test_citer.py", True),
        ("docs/design.md", False),
    ]
    assert captured.err.startswith("2 citing site(s)")


def test_cited_by_matches_a_deleted_target_by_its_spelled_path(tree, capsys):
    _write(tree, "tests/test_citer.py", "# django_strawberry_framework/gone.py::Thing\n")
    check_citations.main(["--cited-by", "django_strawberry_framework/gone.py::Thing"])
    out = capsys.readouterr().out
    assert "tests/test_citer.py:1: `django_strawberry_framework/gone.py::Thing` [gated] " in out
    assert "(1 gated, 0 ungated, 1 unresolved)" in out


def test_cited_by_refuses_a_malformed_symbol(tree):
    with pytest.raises(check_citations.CitationCheckError, match="dotted symbol"):
        check_citations.main(["--cited-by", "widgets.py::1bad"])
