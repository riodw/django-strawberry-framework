"""Script tests for the spec terms-CSV glossary gate.

Repo tooling: these rows pin ``scripts/check_spec_glossary.py``'s one-row-per-anchor rule
and its exit codes. A CLI that reads spec, CSV and glossary text has no ``/graphql/`` wire
shape, so there is no live sibling in ``examples/fakeshop/test_query/``.

Every row writes its spec, CSV and glossary under ``tmp_path``, so no row reads the real
repository.
"""

from pathlib import Path

import pytest

from scripts import check_spec_glossary

GLOSSARY = "## `DjangoType`\n\nBody.\n\n## Relay Node integration\n\nBody.\n"
SPEC = (
    "Uses [`DjangoType`][glossary-djangotype] and [Relay][glossary-relay-node-integration].\n"
    "\n"
    "<!-- LINK DEFINITIONS -->\n"
    "\n"
    "<!-- docs/ -->\n"
    "[glossary-djangotype]: GLOSSARY.md#djangotype\n"
    "[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration\n"
)


def _run(tmp_path: Path, csv_body: str) -> int:
    """Write the fixture trio under ``tmp_path`` and run the gate on it."""
    spec = tmp_path / "spec-099-example-0_0_9.md"
    _ = spec.write_text(SPEC, encoding="utf-8")
    _ = (tmp_path / "spec-099-example-0_0_9-terms.csv").write_text(
        "term,anchor,notes\n" + csv_body,
        encoding="utf-8",
    )
    glossary = tmp_path / "GLOSSARY.md"
    _ = glossary.write_text(GLOSSARY, encoding="utf-8")
    return check_spec_glossary.main(
        [
            "--spec",
            str(spec),
            "--glossary",
            str(glossary),
        ],
    )


def test_one_row_per_anchor_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_body = "`DjangoType`,djangotype,\nRelay Node integration,relay-node-integration,\n"

    assert _run(tmp_path, csv_body) == 0
    assert "OK: 2 terms" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("csv_body", "repeats", "kept"),
    [
        pytest.param(
            "`DjangoType`,djangotype,\n"
            "Relay Node integration,relay-node-integration,\n"
            "`GlobalID`,relay-node-integration,\n",
            ["`GlobalID` (anchor: relay-node-integration)"],
            ["Relay Node integration (anchor"],
            id="adjacent-repeat",
        ),
        pytest.param(
            "Relay Node integration,relay-node-integration,\n"
            "`DjangoType`,djangotype,\n"
            "Relay Node integration,relay-node-integration,second note\n",
            ["Relay Node integration (anchor: relay-node-integration)"],
            ["`DjangoType` (anchor"],
            id="same-term-repeated-after-another-row",
        ),
        pytest.param(
            "`DjangoType`,djangotype,\n"
            "`DjangoTypes`,djangotype,\n"
            "Relay Node integration,relay-node-integration,\n"
            "`GlobalID`,relay-node-integration,\n",
            ["`DjangoTypes` (anchor: djangotype)", "`GlobalID` (anchor: relay-node-integration)"],
            ["`DjangoType` (anchor", "Relay Node integration (anchor"],
            id="two-anchors-each-repeated",
        ),
    ],
)
def test_a_second_row_for_one_anchor_fails_naming_it(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    csv_body: str,
    repeats: list[str],
    kept: list[str],
) -> None:
    assert _run(tmp_path, csv_body) == 1
    out = capsys.readouterr().out
    assert "Rows repeating an anchor in" in out
    for row in repeats:
        assert row in out
    for row in kept:
        assert row not in out
