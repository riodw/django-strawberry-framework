"""Script tests for the explicit-``Any`` gate in ``scripts/check_any.py``.

Repo tooling: these rows pin what the census counts as a use of ``typing.Any``
(every import spelling, string annotations at any nesting depth, ``cast`` and
``TypeVar`` arguments, runtime values) and what it does not (the import itself,
a docstring, an unrelated name ``Any``); the site each use is attributed to; the
verdict against an allowlist (exact match, a new site, a count above or below
the entry, an entry whose site is gone); and the CLI on a scratch package. The
shipped ``ALLOWED_ANY`` is checked for well-formed, unique, reasoned entries,
never for its verdict on the live tree: the gate's own run owns that. A CLI that
reads source files has no ``/graphql/`` wire shape, so there is no live sibling
in ``examples/fakeshop/test_query/``.
"""

import re
import textwrap

import pytest

from scripts import check_any


def _uses(source):
    """The census of one module's ``source``."""
    return check_any.module_uses(textwrap.dedent(source))


def _sites(source):
    """The site names of one module's uses, in census order."""
    return [site for site, _line in _uses(source)]


@pytest.mark.parametrize(
    "source",
    [
        "from typing import Any\nx: Any = 1\n",
        "from typing import Any as Anything\nx: Anything = 1\n",
        "import typing\nx: typing.Any = 1\n",
        "import typing as t\nx: t.Any = 1\n",
        "from typing_extensions import Any\nx: Any = 1\n",
        "import typing_extensions\nx: typing_extensions.Any = 1\n",
    ],
)
def test_every_import_spelling_of_any_is_one_use(source):
    """``Any`` under each import form, alias and module alias, counts once."""
    assert _sites(source) == ["x"]


@pytest.mark.parametrize(
    "source",
    [
        'from typing import Any\nx: "dict[str, Any]" = {}\n',
        'from typing import Any\nx: list["Any"] = []\n',
        "from typing import Any\nx: list[\"dict[str, 'Any']\"] = []\n",
        'from typing import Any, cast\ny = cast("list[Any]", [])\n',
        'from typing import Any, TypeVar\nT = TypeVar("T", bound="list[Any]")\n',
        'from typing import Any\ndef f(a: "Any") -> None: ...\n',
    ],
)
def test_string_annotations_count_at_any_nesting_depth(source):
    """A string type expression is parsed, and a string inside it is parsed again."""
    assert len(_uses(source)) == 1


def test_a_runtime_value_use_counts():
    """``Any`` handed around as a value is still a use."""
    assert _sites("from typing import Any\ndef f():\n    return Any\n") == ["f"]


@pytest.mark.parametrize(
    "source",
    [
        "from typing import Any\n",
        'from typing import Any\n"""Any value at all."""\n',
        'from typing import Any\ndef f():\n    """Returns Any value."""\n',
        "class Any:\n    pass\nx: Any = Any()\n",
        'from typing import Any\nx = "Any"\n',
    ],
)
def test_imports_docstrings_plain_strings_and_unrelated_names_do_not_count(source):
    """The import statement, prose, a plain string and a local ``Any`` class are not uses."""
    assert _uses(source) == []


def test_uses_are_attributed_to_their_enclosing_symbol():
    """Defs and classes nest; module and class scope add the name they bind."""
    source = """
        from typing import TYPE_CHECKING, Any

        if TYPE_CHECKING:
            Alias = list[Any]

        class Base(list[Any]):
            attr: Any = None

            def method(self, value: Any) -> Any:
                local: Any = value

                def inner(*args: Any) -> None: ...

                return local

        list[Any]
    """

    assert _sites(source) == [
        "<module>",
        "Alias",
        "Base",
        "Base.attr",
        "Base.method",
        "Base.method",
        "Base.method",
        "Base.method.inner",
    ]


def test_each_use_carries_its_line():
    """Lines let the failure report point at every use of an unallowed site."""
    assert _uses("from typing import Any\n\nx: Any\ny: list[Any]\n") == [("x", 3), ("y", 4)]


#: The site separator, kept out of the literals so the citation gate does not read a
#: fixture site as a reference to a real file.
_SEP = "::"
#: A fixture site.
_SITE = f"p.py{_SEP}f"


def _mod_site(name):
    """The site of ``name`` in the scratch package's one module."""
    return f"{check_any.PACKAGE}/sub/mod.py{_SEP}{name}"


def _entry(site, count):
    return check_any.AllowedAny(site, count, "the fixture's reason.")


@pytest.mark.parametrize(
    (
        "found",
        "allowed",
        "failing",
        "stale",
    ),
    [
        (
            {_SITE: [3]},
            [_entry(_SITE, 1)],
            (),
            (),
        ),
        (
            {_SITE: [3]},
            [],
            ((_SITE, 1, 0),),
            (),
        ),
        (
            {_SITE: [3, 4]},
            [_entry(_SITE, 1)],
            ((_SITE, 2, 1),),
            (),
        ),
        (
            {_SITE: [3]},
            [_entry(_SITE, 2)],
            (),
            ((_entry(_SITE, 2), 1),),
        ),
        (
            {},
            [_entry(_SITE, 1)],
            (),
            ((_entry(_SITE, 1), 0),),
        ),
    ],
    ids=[
        "exact",
        "new-site",
        "count-above",
        "count-below",
        "site-gone",
    ],
)
def test_the_verdict_needs_an_exact_count_per_site(
    found,
    allowed,
    failing,
    stale,
):
    """Only an exact per-site count passes; more fails, fewer is a stale entry."""
    verdict = check_any.judge(found, allowed)

    assert verdict.failing == failing
    assert verdict.stale == stale
    assert verdict.passing is (not failing and not stale)


def _package(tmp_path, source):
    """A scratch repository root whose package holds one module with ``source``."""
    package = tmp_path / check_any.PACKAGE
    (package / "sub").mkdir(parents=True)
    (package / "sub" / "mod.py").write_text(textwrap.dedent(source), encoding="utf-8")
    return tmp_path


def test_the_gate_passes_an_allowed_tree_and_fails_an_unallowed_one(tmp_path, monkeypatch, capsys):
    """Exit ``0`` on an exact match, ``1`` with each site, count and line otherwise."""
    root = _package(tmp_path, "from typing import Any\n\ndef f(a: Any) -> Any: ...\n")
    site = _mod_site("f")

    monkeypatch.setattr(check_any, "ALLOWED_ANY", (_entry(site, 2),))
    assert check_any.main([], root=root) == 0
    assert capsys.readouterr().out == "check_any: 2 allowed use(s) of Any at 1 site(s)\n"

    monkeypatch.setattr(check_any, "ALLOWED_ANY", (_entry(site, 1),))
    assert check_any.main([], root=root) == 1
    assert capsys.readouterr().out == f"{site}: 2 use(s) of Any, 1 allowed (lines 3, 3)\n"

    monkeypatch.setattr(check_any, "ALLOWED_ANY", (_entry(site, 3),))
    assert check_any.main([], root=root) == 1
    assert capsys.readouterr().out == (f"{site}: stale allowlist entry, 3 allowed, 2 found\n")


def test_list_prints_every_site_and_never_fails(tmp_path, capsys):
    """``--list`` is the allowlist-authoring view: counts per site, exit ``0``."""
    root = _package(tmp_path, "from typing import Any\n\nx: Any\n\ndef f(a: Any): ...\n")

    assert check_any.main(["--list"], root=root) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [f"  1 {_mod_site('f')}", f"  1 {_mod_site('x')}"]
    assert captured.err == "2 uses at 2 sites\n"


def test_the_shipped_allowlist_is_well_formed():
    """Each entry cites one ``path::Symbol`` once, allows at least one use, and says why."""
    sites = [entry.site for entry in check_any.ALLOWED_ANY]

    assert len(sites) == len(set(sites))
    for entry in check_any.ALLOWED_ANY:
        assert re.fullmatch(rf"{check_any.PACKAGE}/[\w/]+\.py::[\w.]+", entry.site), entry
        assert entry.limit >= 1, entry
        assert entry.reason.strip(), entry
