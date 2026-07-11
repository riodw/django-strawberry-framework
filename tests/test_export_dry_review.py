"""Focused tests for the standalone DRY review toolkit."""

from pathlib import Path

from docs.dry import export_dry_review as dry


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_extract_dry_handles_commonmark_fences_and_normalized_headings(
    tmp_path: Path,
) -> None:
    artifact = _write(
        tmp_path / "closed-0_0_1.md",
        """\
# Closed work ###

~~~markdown
## DRY analysis
- fenced decoy
~~~

## DRY analysis ###

+ Reuse the parser.
* Share the validator.
- [x] Preserve an existing checkbox.

### Detail

- Include child-section findings.

## Later

- Do not include this.
""",
    )

    assert dry._extract_dry(artifact) == (
        "Closed work",
        [
            "- [ ] Reuse the parser.",
            "- [ ] Share the validator.",
            "- [x] Preserve an existing checkbox.",
            "",
            "### Detail",
            "",
            "- [ ] Include child-section findings.",
        ],
    )


def test_legacy_plan_cli_is_compatible_and_refuses_accidental_overwrite(
    tmp_path: Path,
) -> None:
    source = tmp_path / "review"
    _write(
        source / "closed-0_0_1.md",
        """\
# Closed work

## DRY analysis

- Reuse the parser.
""",
    )
    output = tmp_path / "dry-0_0_1.md"
    arguments = [
        "--source-dir",
        str(source),
        "--output",
        str(output),
        "--generated-date",
        "2026-01-02",
    ]

    assert dry.main(arguments) == 0
    report = output.read_text(encoding="utf-8")
    assert "# DRY consolidation plan: 0.0.1" in report
    assert "Generated: 2026-01-02" in report
    assert "- [ ] Reuse the parser." in report
    assert dry.main(arguments) == 2
    assert dry.main([*arguments, "--force"]) == 0


def _audit_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    target = _write(
        tmp_path / "pkg" / "target.py",
        '''\
"""Target module."""

TOKEN = "a deliberately repeated literal"

@dataclass
class Widget:
    """Render one value."""

    def render(self, value: int) -> int:
        return value + 1


def shared(
    value: int,
    message: str = "a deliberately repeated literal",
) -> int:
    result = value + 1
    return result
''',
    )
    _write(
        tmp_path / "pkg" / "other.py",
        """\
MESSAGE = "a deliberately repeated literal"


def copied(value: int) -> int:
    result = value + 1
    return result
""",
    )
    _write(
        tmp_path / "pkg" / "consumer.py",
        """\
from pkg.target import Widget, shared

widget = Widget()
answer = shared(widget.render(1))
""",
    )
    bad = _write(tmp_path / "pkg" / "bad.py", "def broken(:\n")
    _write(
        tmp_path / "pkg" / "skip" / "secret.py",
        "NEVER_READ = 'forbidden evidence'\ndef broken(:\n",
    )
    context = _write(
        tmp_path / "spec.md",
        "The SPECIAL_CONCEPT must reuse the shared lifecycle.\n",
    )
    return target, bad, context


def test_audit_collects_inventory_references_duplicates_searches_and_failures(
    tmp_path: Path,
) -> None:
    target, _bad, context = _audit_fixture(tmp_path)

    audit = dry.build_audit(
        root=tmp_path,
        targets=[target],
        scan_roots=[Path("pkg")],
        contexts=[context],
        exclude_patterns=("pkg/skip/**",),
        search_terms=("SPECIAL_CONCEPT", "shared"),
        duplicate_min_nodes=4,
        literal_min_length=20,
    )

    assert [symbol.qualified_name for symbol in audit.target_symbols] == [
        "Widget",
        "Widget.render",
        "shared",
    ]
    shared_locator = "pkg/target.py::shared"
    assert any(
        reference.kind == "exact import" and reference.path == Path("pkg/consumer.py")
        for reference in audit.references[shared_locator]
    )
    assert "pkg.target" in audit.reverse_imports
    assert any(
        {record.qualified_name for record in group} == {"shared", "copied"}
        for group in audit.duplicate_groups
    )
    repeated_literals = dict(audit.repeated_literals)
    assert len(repeated_literals["a deliberately repeated literal"]) == 3
    assert audit.searches["SPECIAL_CONCEPT"] == [
        dry.SearchHit(
            Path("spec.md"),
            1,
            "The SPECIAL_CONCEPT must reuse the shared lifecycle.",
        ),
    ]
    assert set(audit.failures) == {Path("pkg/bad.py")}
    assert audit.failures[Path("pkg/bad.py")].startswith("SyntaxError: invalid syntax")
    assert "line 1" in audit.failures[Path("pkg/bad.py")]
    assert Path("pkg/skip") in audit.excluded

    report = dry.render_audit_markdown(
        audit,
        generated_date="2026-01-02",
        maximum_evidence=10,
    )
    assert "pkg/target.py::Widget.render" in report
    assert "decorators: `@dataclass`" in report
    assert "Exact duplicate function bodies" in report
    assert "SPECIAL_CONCEPT" in report
    assert "NEVER_READ" not in report
    assert report == dry.render_audit_markdown(
        audit,
        generated_date="2026-01-02",
        maximum_evidence=10,
    )


def test_audit_marks_target_parse_failure_as_incomplete(tmp_path: Path) -> None:
    target = _write(tmp_path / "broken.py", "def broken(:\n")

    audit = dry.build_audit(
        root=tmp_path,
        targets=[target],
        scan_roots=[target],
        exclude_patterns=(),
    )

    assert audit.target_records == []
    assert Path("broken.py") in audit.target_failures
    assert "**TARGET \N{EM DASH} inventory incomplete**" in dry.render_audit_markdown(
        audit,
        generated_date="2026-01-02",
    )


def test_explicitly_excluded_target_is_rejected(tmp_path: Path) -> None:
    target = _write(tmp_path / "private" / "target.py", "def hidden():\n    return 1\n")

    try:
        dry.build_audit(
            root=tmp_path,
            targets=[target],
            scan_roots=[tmp_path],
            exclude_patterns=("private/**",),
        )
    except ValueError as exc:
        assert "explicit target path matched --exclude" in str(exc)
    else:
        raise AssertionError("an explicitly excluded target must not be read")


def test_check_reports_exact_missing_definitions_and_topics(tmp_path: Path) -> None:
    target, _bad, _context = _audit_fixture(tmp_path)
    incomplete = _write(
        tmp_path / "incomplete.md",
        "Review Widget and shared. Cover SPECIAL_CONCEPT.\n",
    )

    result = dry.check_review(
        root=tmp_path,
        targets=[target],
        review=incomplete,
        required_topics=("SPECIAL_CONCEPT", "missing lifecycle"),
        exclude_patterns=(),
    )

    assert result.symbol_count == 3
    assert [symbol.qualified_name for symbol in result.missing_symbols] == [
        "Widget.render",
    ]
    assert result.missing_topics == ("missing lifecycle",)
    assert (
        dry.main(
            [
                "check",
                "--root",
                str(tmp_path),
                "--target",
                str(target),
                "--review",
                str(incomplete),
                "--require-topic",
                "missing lifecycle",
                "--no-default-excludes",
            ],
        )
        == 1
    )

    complete = _write(
        tmp_path / "complete.md",
        "Review Widget, Widget.render, and shared. Cover SPECIAL_CONCEPT and missing lifecycle.\n",
    )
    assert dry.check_review(
        root=tmp_path,
        targets=[target],
        review=complete,
        required_topics=("SPECIAL_CONCEPT", "missing lifecycle"),
        exclude_patterns=(),
    ).ok


def test_check_rejects_an_excluded_review_before_target_discovery(
    tmp_path: Path,
) -> None:
    review = _write(tmp_path / "private" / "review.md", "Do not read this.\n")

    try:
        dry.check_review(
            root=tmp_path,
            targets=[tmp_path / "missing-target.py"],
            review=review,
            exclude_patterns=("private/**",),
        )
    except ValueError as exc:
        assert "review path matched --exclude and was not read" in str(exc)
    else:
        raise AssertionError("an explicitly excluded review must not be read")
