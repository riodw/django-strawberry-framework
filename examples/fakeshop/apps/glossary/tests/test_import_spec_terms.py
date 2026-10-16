"""Glossary import command tests for DONE-card spec term extraction."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

from apps.glossary import factories as gf
from apps.glossary import models as glossary_models
from apps.kanban import factories as kf
from apps.kanban import models as kanban_models

SPEC_PATH = "docs/SPECS/spec-099-example-0_0_9.md"
FIRST_SPEC = "docs/SPECS/spec-098-first-0_0_9.md"
SECOND_SPEC = "docs/SPECS/spec-099-second-0_0_9.md"
UNTOUCHED = datetime(2000, 1, 1, tzinfo=timezone.utc)

Row = tuple[str, str, str]


def _write_terms_csv(
    repo_root: Path,
    spec_path: str,
    rows: list[Row],
    *,
    appx: bool = False,
) -> None:
    """Write a companion terms CSV under a temporary repo root.

    ``appx=True`` uses the archived layout (the spec directory's ``appx/``
    subfolder) instead of writing the companion beside the spec.
    """
    name = f"{Path(spec_path).stem}-terms.csv"
    parent = repo_root / Path(spec_path).parent
    path = parent / "appx" / name if appx else parent / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["term", "anchor", "notes"])
        writer.writerows(rows)


def _make_done_card_with_spec(
    spec_path: str,
    *,
    initial_term: glossary_models.GlossaryTerm | None = None,
    name: str | None = None,
) -> kanban_models.Card:
    """Create a done card with the minimum links required by the model lifecycle.

    ``name`` overrides the ``SpecDoc.name`` (unique) derived from the path's stem.
    """
    card = kf.make_card(status=kf.make_status("todo"))
    kf.make_spec_doc(
        card=card,
        name=name or Path(spec_path).stem,
        path=spec_path,
    )
    kf.make_card_glossary_term(card=card, term=initial_term or gf.make_glossary_term())
    # The kanban status state machine forbids a direct todo -> done move; bridge
    # through wip (todo -> wip -> done) so every step is a legal transition.
    card.status = kf.make_status("wip")
    card.save(update_fields=["status"])
    card.status = kf.make_status("done")
    card.save(update_fields=["status"])
    card.refresh_from_db()
    return card


def _terms(*anchors: str) -> list[glossary_models.GlossaryTerm]:
    """Create one ``GlossaryTerm`` per anchor."""
    return [
        gf.make_glossary_term(title=f"`{anchor}`", title_sort=anchor, anchor=anchor)
        for anchor in anchors
    ]


def _run(repo_root: Path, *flags: str) -> str:
    """Run ``import_spec_terms`` against ``repo_root`` and return its stdout."""
    out = StringIO()
    call_command("import_spec_terms", "--repo-root", str(repo_root), *flags, stdout=out)
    return out.getvalue()


def _check(repo_root: Path) -> None:
    """Run ``import_spec_terms --check`` against ``repo_root``."""
    _ = _run(repo_root, "--check")


def _sync(repo_root: Path) -> str:
    """Run the writing ``import_spec_terms`` against ``repo_root``."""
    return _run(repo_root)


def _check_failure(repo_root: Path) -> str:
    """Return the message of the ``CommandError`` a failing ``--check`` raises."""
    with pytest.raises(CommandError) as raised:
        _check(repo_root)
    return str(raised.value)


def _snapshot() -> tuple[list[tuple[object, ...]], list[tuple[object, ...]]]:
    """Return every mention and link row, every column the command reads or writes."""
    mentions = list(
        glossary_models.GlossarySpecMention.objects.order_by("pk").values_list(
            "pk",
            "spec_path",
            "term_id",
            "term_text",
            "notes",
            "order",
            "updated_date",
        ),
    )
    links = list(
        kanban_models.CardGlossaryTerm.objects.order_by("pk").values_list(
            "pk",
            "card_id",
            "term_id",
            "raw_text",
            "order",
            "updated_date",
        ),
    )
    return mentions, links


def _age_every_row() -> None:
    """Stamp every mention and link with ``UNTOUCHED`` so a later write is visible."""
    _ = glossary_models.GlossarySpecMention.objects.update(updated_date=UNTOUCHED)
    _ = kanban_models.CardGlossaryTerm.objects.update(updated_date=UNTOUCHED)


@pytest.mark.django_db
def test_import_spec_terms_reconciles_done_card_csv_to_db(tmp_path: Path) -> None:
    djangotype, filterset, stale = _terms("djangotype", "filterset", "stale")
    card = _make_done_card_with_spec(SPEC_PATH, initial_term=stale)
    _write_terms_csv(
        tmp_path,
        SPEC_PATH,
        [
            ("DjangoType", djangotype.anchor, "Primary type surface."),
            ("FilterSet", filterset.anchor, "Filtering sidecar."),
        ],
    )

    _ = _sync(tmp_path)

    mentions = glossary_models.GlossarySpecMention.objects.filter(spec_path=SPEC_PATH).order_by(
        "order",
    )
    assert [(mention.term.anchor, mention.term_text, mention.notes) for mention in mentions] == [
        ("djangotype", "DjangoType", "Primary type surface."),
        ("filterset", "FilterSet", "Filtering sidecar."),
    ]
    links = card.glossary_links.order_by("order")
    assert [(link.term.anchor, link.raw_text, link.order) for link in links] == [
        ("djangotype", "DjangoType", 0),
        ("filterset", "FilterSet", 1),
    ]
    assert not card.glossary_links.filter(term=stale).exists()

    _check(tmp_path)


@pytest.mark.django_db
def test_import_spec_terms_check_rejects_mismatched_done_card_links(tmp_path: Path) -> None:
    _, stale = _terms("djangotype", "stale")
    _make_done_card_with_spec(SPEC_PATH, initial_term=stale)
    _write_terms_csv(tmp_path, SPEC_PATH, [("DjangoType", "djangotype", "")])

    with pytest.raises(CommandError, match="CardGlossaryTerm extra stale"):
        _check(tmp_path)


@pytest.mark.django_db
def test_import_spec_terms_reads_archived_companion_from_appx(tmp_path: Path) -> None:
    _ = _terms("djangotype")
    card = _make_done_card_with_spec(SPEC_PATH)
    _write_terms_csv(
        tmp_path,
        SPEC_PATH,
        [("DjangoType", "djangotype", "Primary type surface.")],
        appx=True,
    )

    _ = _sync(tmp_path)

    mentions = glossary_models.GlossarySpecMention.objects.filter(spec_path=SPEC_PATH)
    assert [(mention.term.anchor, mention.term_text) for mention in mentions] == [
        ("djangotype", "DjangoType"),
    ]
    assert [link.term.anchor for link in card.glossary_links.all()] == ["djangotype"]

    _check(tmp_path)


@pytest.mark.django_db
def test_import_spec_terms_requires_csv_for_every_done_card(tmp_path: Path) -> None:
    _make_done_card_with_spec(SPEC_PATH)

    with pytest.raises(CommandError, match="Missing terms CSV"):
        _ = _sync(tmp_path)


# One column change per row: the CSV before, the CSV after, and the clauses ``--check``
# owes for it. Each row moves exactly one column the writing run sets.
COLUMN_CHANGES = [
    pytest.param(
        [("DjangoType", "djangotype", "Old note."), ("FilterSet", "filterset", "")],
        [("DjangoType", "djangotype", "New note."), ("FilterSet", "filterset", "")],
        ["GlossarySpecMention changed djangotype (notes)"],
        id="notes",
    ),
    pytest.param(
        [("DjangoType", "djangotype", ""), ("FilterSet", "filterset", "")],
        [("Django type", "djangotype", ""), ("FilterSet", "filterset", "")],
        [
            "GlossarySpecMention changed djangotype (term_text)",
            "CardGlossaryTerm changed djangotype (raw_text)",
        ],
        id="term-text",
    ),
    pytest.param(
        [("DjangoType", "djangotype", ""), ("FilterSet", "filterset", "")],
        [("FilterSet", "filterset", ""), ("DjangoType", "djangotype", "")],
        [
            "GlossarySpecMention changed filterset (order), djangotype (order)",
            "CardGlossaryTerm changed filterset (order), djangotype (order)",
        ],
        id="order",
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize(("before", "after", "clauses"), COLUMN_CHANGES)
def test_import_spec_terms_check_names_a_one_column_difference(
    tmp_path: Path,
    before: list[Row],
    after: list[Row],
    clauses: list[str],
) -> None:
    _ = _terms("djangotype", "filterset")
    _make_done_card_with_spec(SPEC_PATH)
    _write_terms_csv(tmp_path, SPEC_PATH, before)
    _ = _sync(tmp_path)
    _write_terms_csv(tmp_path, SPEC_PATH, after)

    message = _check_failure(tmp_path)

    assert "1 glossary sync difference(s)" in message
    for clause in clauses:
        assert clause in message


@pytest.mark.django_db
@pytest.mark.parametrize(("before", "after", "clauses"), COLUMN_CHANGES)
def test_import_spec_terms_writes_a_one_column_difference(
    tmp_path: Path,
    before: list[Row],
    after: list[Row],
    clauses: list[str],
) -> None:
    del clauses
    _ = _terms("djangotype", "filterset")
    card = _make_done_card_with_spec(SPEC_PATH)
    _write_terms_csv(tmp_path, SPEC_PATH, before)
    _ = _sync(tmp_path)
    _write_terms_csv(tmp_path, SPEC_PATH, after)

    assert "1 difference(s) written" in _sync(tmp_path)

    expected = [
        (
            anchor,
            text,
            notes,
            order,
        )
        for order, (text, anchor, notes) in enumerate(after)
    ]
    mentions = glossary_models.GlossarySpecMention.objects.filter(spec_path=SPEC_PATH)
    assert [
        (
            mention.term.anchor,
            mention.term_text,
            mention.notes,
            mention.order,
        )
        for mention in mentions.order_by("order")
    ] == expected
    assert [
        (link.term.anchor, link.raw_text, link.order)
        for link in card.glossary_links.order_by("order")
    ] == [(anchor, text, order) for anchor, text, _, order in expected]
    _check(tmp_path)


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "first_rows",
        "second_rows",
        "first_clause",
        "second_clause",
    ),
    [
        pytest.param(
            [("DjangoType", "djangotype", "")],
            [("DjangoType", "djangotype", "")],
            "CardGlossaryTerm extra first",
            "CardGlossaryTerm extra second",
            id="anchor-sets",
        ),
        pytest.param(
            [("First", "first", "Moved note.")],
            [("Second", "second", "Moved note.")],
            "GlossarySpecMention changed first (notes)",
            "GlossarySpecMention changed second (notes)",
            id="notes",
        ),
    ],
)
def test_import_spec_terms_check_names_every_out_of_sync_card(
    tmp_path: Path,
    first_rows: list[Row],
    second_rows: list[Row],
    first_clause: str,
    second_clause: str,
) -> None:
    _, first, second = _terms("djangotype", "first", "second")
    _make_done_card_with_spec(FIRST_SPEC, initial_term=first)
    _make_done_card_with_spec(SECOND_SPEC, initial_term=second)
    _write_terms_csv(tmp_path, FIRST_SPEC, [("First", "first", "")])
    _write_terms_csv(tmp_path, SECOND_SPEC, [("Second", "second", "")])
    _ = _sync(tmp_path)
    _write_terms_csv(tmp_path, FIRST_SPEC, first_rows)
    _write_terms_csv(tmp_path, SECOND_SPEC, second_rows)

    message = _check_failure(tmp_path)

    assert "2 glossary sync difference(s)" in message
    assert "across 2 done card(s)" in message
    assert f"({FIRST_SPEC}): " in message
    assert first_clause in message
    assert f"({SECOND_SPEC}): " in message
    assert second_clause in message


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("csv_rows", "expected"),
    [
        pytest.param(
            {FIRST_SPEC: None, SECOND_SPEC: None},
            [
                "2 done card(s) cannot be planned",
                "Missing terms CSV",
                "spec-098-first-0_0_9-terms.csv",
                "spec-099-second-0_0_9-terms.csv",
            ],
            id="two-missing-csvs",
        ),
        pytest.param(
            {"notes/spec-097-elsewhere-0_0_9.md": None, SECOND_SPEC: None},
            [
                "2 done card(s) cannot be planned",
                "spec URL has no repo docs/ path",
                "spec-099-second-0_0_9-terms.csv",
            ],
            id="path-outside-docs-beside-a-missing-csv",
        ),
        pytest.param(
            {
                FIRST_SPEC: [
                    ("DjangoType", "djangotype", ""),
                    ("Django type", "djangotype", ""),
                    ("Unknown", "unknown", ""),
                ],
                SECOND_SPEC: [("DjangoType", "djangotype", "")],
            },
            [
                "1 done card(s) cannot be planned",
                "Duplicate glossary anchor 'djangotype'",
                "Missing GlossaryTerm anchor 'unknown'",
            ],
            id="repeated-and-unknown-anchor-in-one-csv",
        ),
        pytest.param(
            {
                FIRST_SPEC: [("Unknown", "unknown", ""), ("Missing", "missing", "")],
                SECOND_SPEC: [("DjangoType", "djangotype", "")],
            },
            [
                "1 done card(s) cannot be planned",
                "Missing GlossaryTerm anchor 'unknown'",
                "Missing GlossaryTerm anchor 'missing'",
            ],
            id="two-unknown-anchors-in-one-csv",
        ),
        pytest.param(
            {FIRST_SPEC: None, SECOND_SPEC: [("DjangoType", "djangotype", "")]},
            [
                "1 done card(s) cannot be planned",
                "1 glossary sync difference(s)",
                "spec-098-first-0_0_9-terms.csv",
                f"({SECOND_SPEC}): GlossarySpecMention missing djangotype",
            ],
            id="planning-error-beside-a-difference",
        ),
    ],
)
def test_import_spec_terms_check_names_every_planning_error(
    tmp_path: Path,
    csv_rows: dict[str, list[Row] | None],
    expected: list[str],
) -> None:
    _ = _terms("djangotype")
    for spec_path, rows in csv_rows.items():
        _make_done_card_with_spec(spec_path)
        if rows is not None:
            _write_terms_csv(tmp_path, spec_path, rows)

    message = _check_failure(tmp_path)

    for fragment in expected:
        assert fragment in message


@pytest.mark.django_db
@pytest.mark.parametrize(
    "broken_rows",
    [
        pytest.param(None, id="missing-csv"),
        pytest.param([("Unknown", "unknown", "")], id="unknown-anchor"),
    ],
)
def test_import_spec_terms_writes_nothing_while_a_card_cannot_be_planned(
    tmp_path: Path,
    broken_rows: list[Row] | None,
) -> None:
    _ = _terms("djangotype")
    _make_done_card_with_spec(FIRST_SPEC)
    _make_done_card_with_spec(SECOND_SPEC)
    if broken_rows is not None:
        _write_terms_csv(tmp_path, FIRST_SPEC, broken_rows)
    _write_terms_csv(tmp_path, SECOND_SPEC, [("DjangoType", "djangotype", "")])
    before = _snapshot()

    with pytest.raises(CommandError, match=r"1 done card\(s\) cannot be planned; nothing written"):
        _ = _sync(tmp_path)

    assert _snapshot() == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "broken_rows",
    [
        pytest.param(None, id="missing-csv"),
        pytest.param([("Unknown", "unknown", "")], id="unknown-anchor"),
    ],
)
def test_import_spec_terms_names_no_orphan_while_a_card_cannot_be_planned(
    tmp_path: Path,
    broken_rows: list[Row] | None,
) -> None:
    _ = _terms("djangotype")
    _make_done_card_with_spec(FIRST_SPEC)
    _make_done_card_with_spec(SECOND_SPEC)
    for spec_path in (FIRST_SPEC, SECOND_SPEC):
        _write_terms_csv(tmp_path, spec_path, [("DjangoType", "djangotype", "")])
    _ = _sync(tmp_path)
    if broken_rows is None:
        (tmp_path / f"{FIRST_SPEC.removesuffix('.md')}-terms.csv").unlink()
    else:
        _write_terms_csv(tmp_path, FIRST_SPEC, broken_rows)

    message = _check_failure(tmp_path)

    assert "1 done card(s) cannot be planned" in message
    assert "glossary sync difference" not in message
    assert "no done card's spec resolves" not in message


# Each row's CSV ``before`` and ``after`` force a write order that meets the
# ``(card, order)`` unique constraint unless every moved and deleted link is parked first.
REORDERS = [
    pytest.param(
        [("Alpha", "alpha", ""), ("Beta", "beta", "")],
        [("Gamma", "gamma", ""), ("Beta", "beta", ""), ("Alpha", "alpha", "")],
        id="insert-and-reverse",
    ),
    pytest.param(
        [("Alpha", "alpha", ""), ("Beta", "beta", "")],
        [("Beta", "beta", ""), ("Alpha", "alpha", "")],
        id="swap",
    ),
    pytest.param(
        [("Alpha", "alpha", ""), ("Beta", "beta", ""), ("Gamma", "gamma", "")],
        [("Gamma", "gamma", ""), ("Alpha", "alpha", "")],
        id="move-into-a-deleted-slot",
    ),
    pytest.param(
        [("Alpha", "alpha", ""), ("Beta", "beta", "")],
        [("Beta", "beta", "")],
        id="move-down-over-a-deleted-link",
    ),
    pytest.param(
        [("Alpha", "alpha", ""), ("Beta", "beta", ""), ("Gamma", "gamma", "")],
        [("Gamma", "gamma", "")],
        id="shrink-to-the-last-link",
    ),
    pytest.param(
        [("Alpha", "alpha", ""), ("Beta", "beta", ""), ("Gamma", "gamma", "")],
        [("Beta", "beta", ""), ("Gamma", "gamma", "")],
        id="drop-the-head",
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize(("before", "after"), REORDERS)
def test_import_spec_terms_reorders_links_past_the_card_order_constraint(
    tmp_path: Path,
    before: list[Row],
    after: list[Row],
) -> None:
    _ = _terms("alpha", "beta", "gamma")
    card = _make_done_card_with_spec(SPEC_PATH)
    _write_terms_csv(tmp_path, SPEC_PATH, before)
    _ = _sync(tmp_path)
    _write_terms_csv(tmp_path, SPEC_PATH, after)

    _ = _sync(tmp_path)

    assert [(link.term.anchor, link.order) for link in card.glossary_links.order_by("order")] == [
        (anchor, order) for order, (_, anchor, _) in enumerate(after)
    ]
    _check(tmp_path)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("after", "rewritten"),
    [
        pytest.param(
            [("Alpha", "alpha", "A."), ("Beta", "beta", "B."), ("Gamma", "gamma", "C.")],
            set[tuple[str, str]](),
            id="unchanged",
        ),
        pytest.param(
            [("Alpha", "alpha", "A."), ("Beta", "beta", "New."), ("Gamma", "gamma", "C.")],
            {("mention", "beta")},
            id="one-note",
        ),
        pytest.param(
            [("Alpha", "alpha", "A."), ("Gamma", "gamma", "C."), ("Beta", "beta", "B.")],
            {
                ("mention", "beta"),
                ("mention", "gamma"),
                ("link", "beta"),
                ("link", "gamma"),
            },
            id="two-rows-swap",
        ),
    ],
)
def test_import_spec_terms_writes_only_the_rows_that_differ(
    tmp_path: Path,
    after: list[Row],
    rewritten: set[tuple[str, str]],
) -> None:
    _ = _terms("alpha", "beta", "gamma")
    card = _make_done_card_with_spec(SPEC_PATH)
    _write_terms_csv(
        tmp_path,
        SPEC_PATH,
        [("Alpha", "alpha", "A."), ("Beta", "beta", "B."), ("Gamma", "gamma", "C.")],
    )
    _ = _sync(tmp_path)
    _age_every_row()
    _write_terms_csv(tmp_path, SPEC_PATH, after)

    _ = _sync(tmp_path)

    restamped = {
        ("mention", mention.term.anchor)
        for mention in glossary_models.GlossarySpecMention.objects.filter(spec_path=SPEC_PATH)
        if mention.updated_date != UNTOUCHED
    } | {
        ("link", link.term.anchor)
        for link in card.glossary_links.all()
        if link.updated_date != UNTOUCHED
    }
    assert restamped == rewritten
    assert "0 difference(s) written" in _sync(tmp_path)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "origin",
    [
        pytest.param("stray", id="stray-row-at-another-path"),
        pytest.param("archive", id="spec-archived-and-repointed"),
    ],
)
def test_import_spec_terms_reaps_mentions_at_a_path_no_done_card_plans(
    tmp_path: Path,
    origin: str,
) -> None:
    live_path = "docs/spec-099-example-0_0_9.md"
    (term,) = _terms("djangotype")
    card = _make_done_card_with_spec(live_path)
    _write_terms_csv(tmp_path, live_path, [("DjangoType", "djangotype", "")])
    _ = _sync(tmp_path)
    if origin == "archive":
        # A spec archive moves the companion to ``appx/`` and repoints the SpecDoc,
        # leaving the mention rows keyed by the pre-archive path.
        (tmp_path / f"{live_path.removesuffix('.md')}-terms.csv").unlink()
        _write_terms_csv(tmp_path, SPEC_PATH, [("DjangoType", "djangotype", "")], appx=True)
        spec = kanban_models.SpecDoc.objects.get(card=card)
        spec.path = SPEC_PATH
        spec.save()
        orphan_path, kept_path = live_path, SPEC_PATH
    else:
        _ = glossary_models.GlossarySpecMention.objects.create(
            spec_path=SPEC_PATH,
            term=term,
            term_text="DjangoType",
        )
        orphan_path, kept_path = SPEC_PATH, live_path

    message = _check_failure(tmp_path)

    assert f"{orphan_path}: GlossarySpecMention extra djangotype" in message
    assert "(no done card's spec resolves to this path)" in message

    _ = _sync(tmp_path)

    assert list(
        glossary_models.GlossarySpecMention.objects.values_list("spec_path", "term__anchor"),
    ) == [(kept_path, "djangotype")]
    _check(tmp_path)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "flag",
    [pytest.param("--check", id="check"), pytest.param("--dry-run", id="dry-run")],
)
@pytest.mark.parametrize(
    "drift",
    [pytest.param("difference", id="difference"), pytest.param("orphan", id="orphan")],
)
def test_import_spec_terms_read_only_modes_write_nothing(
    tmp_path: Path,
    flag: str,
    drift: str,
) -> None:
    (term,) = _terms("djangotype")
    _make_done_card_with_spec(SPEC_PATH)
    _write_terms_csv(tmp_path, SPEC_PATH, [("DjangoType", "djangotype", "Old.")])
    _ = _sync(tmp_path)
    if drift == "difference":
        _write_terms_csv(tmp_path, SPEC_PATH, [("DjangoType", "djangotype", "New.")])
    else:
        _ = glossary_models.GlossarySpecMention.objects.create(
            spec_path="docs/spec-099-example-0_0_9.md",
            term=term,
            term_text="DjangoType",
        )
    before = _snapshot()

    if flag == "--check":
        _ = _check_failure(tmp_path)
    else:
        assert "1 difference(s) to write" in _run(tmp_path, flag)

    assert _snapshot() == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "broken_rows",
    [
        pytest.param(None, id="missing-csv"),
        pytest.param([("Unknown", "unknown", "")], id="unknown-anchor"),
    ],
)
def test_import_spec_terms_dry_run_lists_everything_then_refuses_an_unplannable_card(
    tmp_path: Path,
    broken_rows: list[Row] | None,
) -> None:
    _ = _terms("djangotype")
    _make_done_card_with_spec(FIRST_SPEC)
    _make_done_card_with_spec(SECOND_SPEC)
    if broken_rows is not None:
        _write_terms_csv(tmp_path, FIRST_SPEC, broken_rows)
    _write_terms_csv(tmp_path, SECOND_SPEC, [("DjangoType", "djangotype", "")])
    out = StringIO()
    before = _snapshot()

    with pytest.raises(
        CommandError,
        match=r"1 done card\(s\) cannot be planned; the writing run would write nothing",
    ):
        call_command(
            "import_spec_terms",
            "--repo-root",
            str(tmp_path),
            "--dry-run",
            stdout=out,
        )

    listing = out.getvalue()
    assert "Would import glossary terms for 1 done card(s):" in listing
    assert "1 term(s) from" in listing
    assert "1 done card(s) cannot be planned:" in listing
    assert "spec-098-first-0_0_9" in listing
    assert "1 difference(s) to write:" in listing
    assert f"({SECOND_SPEC}): GlossarySpecMention missing djangotype" in listing
    assert _snapshot() == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("first_path", "layout"),
    [
        pytest.param(SPEC_PATH, "equal", id="equal-stored-paths"),
        pytest.param(
            "docs/spec-099-example-0_0_9.md",
            "archived",
            id="stale-path-resolving-to-the-other",
        ),
    ],
)
def test_import_spec_terms_refuses_two_done_cards_on_one_spec(
    tmp_path: Path,
    first_path: str,
    layout: str,
) -> None:
    _ = _terms("djangotype")
    if layout == "archived":
        # The stale ``docs/`` path resolves by basename to the archived spec file.
        spec_file = tmp_path / SPEC_PATH
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        _ = spec_file.write_text("# spec\n", encoding="utf-8")
    first = _make_done_card_with_spec(first_path, name="spec-099-example-first")
    second = _make_done_card_with_spec(SPEC_PATH, name="spec-099-example-second")
    _write_terms_csv(tmp_path, SPEC_PATH, [("DjangoType", "djangotype", "")])
    before = _snapshot()

    message = _check_failure(tmp_path)

    assert "1 done card(s) cannot be planned" in message
    assert f"Done card {second} resolves to spec {SPEC_PATH}, already planned" in message
    assert f"for done card {first}." in message
    with pytest.raises(CommandError, match="nothing written"):
        _ = _sync(tmp_path)
    assert _snapshot() == before
