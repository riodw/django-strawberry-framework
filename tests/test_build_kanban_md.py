"""Tests for KANBAN markdown glossary inlining around existing links.

Repo tooling: these rows pin ``scripts/build_kanban_md.py::GlossaryInliner``,
which runs at render time against an in-process glossary snapshot. A live
``/graphql/`` request has no wire shape for the markdown link a rendered card
carries, so none of these rows can move. There is no live sibling in
``examples/fakeshop/test_query/``.
"""

import pytest

from scripts.build_kanban_md import GLOSSARY_MD_PATH, GlossaryInliner

LINKED = f"[`DjangoListField`]({GLOSSARY_MD_PATH}#djangolistfield)"
BARE_LINKED = f"[DjangoListField]({GLOSSARY_MD_PATH}#djangolistfield)"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(
            "See [`DjangoListField`][list-field].",
            "See [`DjangoListField`][list-field].",
            id="reference-link-label",
        ),
        pytest.param(
            "See [`DjangoListField`][].",
            "See [`DjangoListField`][].",
            id="collapsed-link-label",
        ),
        pytest.param(
            "See [DjangoListField][list-field].",
            "See [DjangoListField][list-field].",
            id="reference-link-bare-title-label",
        ),
        pytest.param(
            "See [`DjangoListField`](docs/README.md).",
            "See [`DjangoListField`](docs/README.md).",
            id="inline-link-label",
        ),
        pytest.param(
            "See [the [DjangoListField] API][field].",
            "See [the [DjangoListField] API][field].",
            id="nested-brackets-in-reference-text",
        ),
        pytest.param(
            "See [the [DjangoListField] API](docs/x.md).",
            "See [the [DjangoListField] API](docs/x.md).",
            id="nested-brackets-in-inline-text",
        ),
        pytest.param(
            r"See [a \] DjangoListField b](docs/x.md).",
            r"See [a \] DjangoListField b](docs/x.md).",
            id="escaped-close-in-link-text",
        ),
        pytest.param(
            "See [a `]` DjangoListField b](docs/x.md).",
            "See [a `]` DjangoListField b](docs/x.md).",
            id="code-span-bracket-in-link-text",
        ),
        pytest.param(
            "See [DjangoListField] today.",
            "See [DjangoListField] today.",
            id="shortcut-reference",
        ),
        pytest.param(
            'See [the API](docs/x.md "see (a) DjangoListField").',
            'See [the API](docs/x.md "see (a) DjangoListField").',
            id="parenthesised-destination",
        ),
        pytest.param(
            'See [the API](docs/x.md "DjangoListField ((a))").',
            'See [the API](docs/x.md "DjangoListField ((a))").',
            id="title-with-nested-parens",
        ),
        pytest.param(
            'See [the API](docs/x(a(b)).md "DjangoListField").',
            'See [the API](docs/x(a(b)).md "DjangoListField").',
            id="destination-with-nested-parens",
        ),
        pytest.param(
            'See [the API](<docs/x (y.md> "DjangoListField").',
            'See [the API](<docs/x (y.md> "DjangoListField").',
            id="angle-destination-unbalanced-paren",
        ),
        pytest.param(
            "See [the API](docs/x.md 'DjangoListField [b] ) c').",
            "See [the API](docs/x.md 'DjangoListField [b] ) c').",
            id="single-quoted-title-with-close-paren",
        ),
        pytest.param(
            'See [the API](docs/x.md "DjangoListField `q") and `z`.',
            'See [the API](docs/x.md "DjangoListField `q") and `z`.',
            id="title-with-lone-backtick",
        ),
        pytest.param(
            'See [the API](docs/x.md "t [ (") then DjangoListField b] later.',
            f'See [the API](docs/x.md "t [ (") then {BARE_LINKED} b] later.',
            id="live-text-after-title-with-brackets",
        ),
        pytest.param(
            'See [the API](docs/x(y.md "DjangoListField") now.',
            f'See [the API](docs/x(y.md "{BARE_LINKED}") now.',
            id="unbalanced-destination-is-not-a-link",
        ),
        pytest.param(
            "[DEFERRED - DjangoListField ships]",
            "[DEFERRED - DjangoListField ships]",
            id="literal-bracket-run",
        ),
        pytest.param(
            "Ship `DjangoListField` next.",
            f"Ship {LINKED} next.",
            id="plain-mention",
        ),
        pytest.param(
            r"See \[DjangoListField\](docs/x.md).",
            rf"See \[{BARE_LINKED}\](docs/x.md).",
            id="escaped-brackets-are-literal",
        ),
    ],
)
def test_inliner_leaves_existing_links_intact(text: str, expected: str) -> None:
    """A term inside any bracket group or link is left alone; a plain mention is linked."""
    inliner = GlossaryInliner([{"title": "`DjangoListField`", "anchor": "djangolistfield"}])
    assert inliner.inline(text) == expected
