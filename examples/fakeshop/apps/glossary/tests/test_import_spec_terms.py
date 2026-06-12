"""Glossary import command tests for DONE-card spec term extraction."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

from apps.glossary import factories as gf
from apps.glossary import models as glossary_models
from apps.kanban import factories as kf
from apps.kanban import models as kanban_models


def _write_terms_csv(repo_root: Path, spec_path: str, rows: list[tuple[str, str, str]]) -> None:
    """Write a companion terms CSV under a temporary repo root."""
    path = repo_root / Path(spec_path).with_name(f"{Path(spec_path).stem}-terms.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["term", "anchor", "notes"])
        writer.writerows(rows)


def _make_done_card_with_spec(spec_path: str, *, initial_term=None) -> kanban_models.Card:
    """Create a done card with the minimum links required by the model lifecycle."""
    card = kf.make_card(status=kf.make_status("todo"))
    kf.make_spec_doc(
        card=card,
        name=Path(spec_path).stem,
        url=f"https://github.com/example/{spec_path}",
    )
    kf.make_card_glossary_term(card=card, term=initial_term or gf.make_glossary_term())
    card.status = kf.make_status("done")
    card.save(update_fields=["status"])
    card.refresh_from_db()
    return card


@pytest.mark.django_db
def test_import_spec_terms_reconciles_done_card_csv_to_db(tmp_path):
    spec_path = "docs/SPECS/spec-099-example-0_0_9.md"
    djangotype = gf.make_glossary_term(
        title="`DjangoType`",
        title_sort="djangotype",
        anchor="djangotype",
    )
    filterset = gf.make_glossary_term(
        title="`FilterSet`",
        title_sort="filterset",
        anchor="filterset",
    )
    stale = gf.make_glossary_term(title="`Stale`", title_sort="stale", anchor="stale")
    card = _make_done_card_with_spec(spec_path, initial_term=stale)
    _write_terms_csv(
        tmp_path,
        spec_path,
        [
            ("DjangoType", djangotype.anchor, "Primary type surface."),
            ("FilterSet", filterset.anchor, "Filtering sidecar."),
        ],
    )

    call_command("import_spec_terms", "--repo-root", str(tmp_path), stdout=StringIO())

    mentions = glossary_models.GlossarySpecMention.objects.filter(spec_path=spec_path).order_by(
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

    call_command(
        "import_spec_terms",
        "--repo-root",
        str(tmp_path),
        "--check",
        stdout=StringIO(),
    )


@pytest.mark.django_db
def test_import_spec_terms_check_rejects_mismatched_done_card_links(tmp_path):
    spec_path = "docs/SPECS/spec-099-example-0_0_9.md"
    gf.make_glossary_term(title="`DjangoType`", title_sort="djangotype", anchor="djangotype")
    stale = gf.make_glossary_term(title="`Stale`", title_sort="stale", anchor="stale")
    _make_done_card_with_spec(spec_path, initial_term=stale)
    _write_terms_csv(tmp_path, spec_path, [("DjangoType", "djangotype", "")])

    with pytest.raises(CommandError, match="do not match"):
        call_command(
            "import_spec_terms",
            "--repo-root",
            str(tmp_path),
            "--check",
            stdout=StringIO(),
        )


@pytest.mark.django_db
def test_import_spec_terms_requires_csv_for_every_done_card(tmp_path):
    _make_done_card_with_spec("docs/SPECS/spec-099-example-0_0_9.md")

    with pytest.raises(CommandError, match="Missing terms CSV"):
        call_command("import_spec_terms", "--repo-root", str(tmp_path), stdout=StringIO())
