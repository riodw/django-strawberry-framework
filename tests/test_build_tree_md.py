"""Tests for TREE renderer planned descriptions, replacements, and source discovery.

Repo tooling: these rows pin ``scripts/build_tree_md.py`` planned-path
annotations, target-layout replacements, and fakeshop source discovery, which
run at render time against the working tree and an in-process card snapshot.
A live ``/graphql/`` request has no wire shape for TREE.md markdown, a
curated planned-path sentence, or a filesystem inventory the renderer walks,
so none of these rows can move. There is no live sibling in
``examples/fakeshop/test_query/``.
"""

import re
from types import SimpleNamespace

import pytest

from scripts.build_tree_md import (
    PLANNED_PATH_DESCRIPTIONS,
    REPO_ROOT,
    PlannedPath,
    TargetNode,
    TreeRenderError,
    _planned_paths_from_rows,
    fakeshop_app_names,
    remove_target_replacements,
    render_fakeshop_project_tree,
    render_target_tree,
)

_FAKESHOP_PROJECT = REPO_ROOT / "examples" / "fakeshop"
_FAKESHOP_APP_NAMES = fakeshop_app_names(_FAKESHOP_PROJECT / "apps")
_CURATED_PLANNED_DESCRIPTIONS = tuple(PLANNED_PATH_DESCRIPTIONS.items())
_FAKESHOP_TREE_SOURCE_FILES = (
    "graphql_client.py",
    "manage.py",
    "schema_reload.py",
    "strategy_schemas.py",
    "constraints.py",
    "filters_genre.py",
    "serializers.py",
    "signals.py",
    "factories.py",
)
_FAKESHOP_APP_LOCAL_TESTS = ("test_signals.py", "test_import_spec_terms.py")


def _card(
    number: int,
    key: str,
    card_id: str,
    title: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        number=number,
        card_id=card_id,
        title=title,
        status=SimpleNamespace(key=key),
    )


def _row(path: str, *, is_directory: bool, cards: list) -> SimpleNamespace:
    return SimpleNamespace(
        path=path,
        is_directory=is_directory,
        cards=SimpleNamespace(all=lambda cards=cards: list(cards)),
    )


@pytest.fixture(scope="module")
def rendered_fakeshop_project_tree() -> str:
    return "\n".join(render_fakeshop_project_tree(_FAKESHOP_PROJECT))


def test_planned_path_uses_branch_specific_description() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/fieldset/",
        is_directory=True,
        card_id="TODO-BETA-046-0.1.1",
        card_title="`FieldSet`",
    )

    assert planned.description == (
        "planned by TODO-BETA-046-0.1.1 - FieldSet computed fields, resolver overrides, "
        "field permissions, and optimizer dependencies."
    )


def test_planned_path_falls_back_to_card_title_without_curated_description() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/not_curated/",
        is_directory=True,
        card_id="TODO-BETA-099-0.9.9",
        card_title="`SomethingNew`",
    )

    assert planned.description == "planned by TODO-BETA-099-0.9.9 - `SomethingNew`."


def test_planned_path_title_fallback_is_normalized_not_double_terminated() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/not_curated/",
        is_directory=True,
        card_id="TODO-BETA-099-0.9.9",
        card_title="Already a sentence.  ",
    )

    assert planned.description == "planned by TODO-BETA-099-0.9.9 - Already a sentence."


def test_planned_path_rejects_a_two_sentence_title_like_any_summary() -> None:
    planned = PlannedPath(
        path="django_strawberry_framework/not_curated/",
        is_directory=True,
        card_id="TODO-BETA-099-0.9.9",
        card_title="First sentence. Second sentence",
    )

    with pytest.raises(TreeRenderError, match="ONE sentence"):
        _ = planned.description


def test_curated_planned_descriptions_are_present() -> None:
    """The curated planned-path descriptions mapping is non-empty."""
    assert len(PLANNED_PATH_DESCRIPTIONS) > 0


@pytest.mark.parametrize(
    ("path", "summary"),
    _CURATED_PLANNED_DESCRIPTIONS,
    ids=[path.rstrip("/").replace("/", "-") for path, _ in _CURATED_PLANNED_DESCRIPTIONS],
)
def test_curated_planned_description_is_one_sentence(path: str, summary: str) -> None:
    """Each curated planned-path summary is one sentence and wins over the card title."""
    planned = PlannedPath(path=path, is_directory=True, card_id="X-1", card_title="ignored")
    assert planned.description == f"planned by X-1 - {summary}"


def test_planned_rows_skip_paths_that_already_exist_on_disk() -> None:
    shipped = _row(
        "django_strawberry_framework/relay.py",
        is_directory=False,
        cards=[_card(10, "wip", "WIP-10", "already shipped")],
    )
    pending = _row(
        "django_strawberry_framework/fieldset/",
        is_directory=True,
        cards=[
            _card(30, "todo", "TODO-30", "later linker"),
            _card(12, "wip", "WIP-12", "owning card"),
        ],
    )

    planned = _planned_paths_from_rows([shipped, pending])

    assert [entry.path for entry in planned] == ["django_strawberry_framework/fieldset/"]
    assert planned[0].card_id == "WIP-12"


def test_target_replacement_removes_superseded_flat_module() -> None:
    root = TargetNode(
        name="django_strawberry_framework/",
        is_dir=True,
        description="",
        children={
            "permissions.py": TargetNode(
                name="permissions.py",
                is_dir=False,
                description="",
            ),
        },
    )
    planned = PlannedPath(
        path="django_strawberry_framework/permissions/",
        is_directory=True,
        card_id="TODO-BETA-051-0.1.4",
        card_title="redaction",
    )

    remove_target_replacements(root, "django_strawberry_framework/", planned)

    assert "permissions.py" not in root.children


def test_target_tree_replaces_flat_module_with_planned_package(tmp_path) -> None:
    package_dir = tmp_path / "django_strawberry_framework"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text('"""Test package root."""\n')
    (package_dir / "permissions.py").write_text('"""Flat permissions module."""\n')
    planned = PlannedPath(
        path="django_strawberry_framework/permissions/",
        is_directory=True,
        card_id="TODO-BETA-051-0.1.4",
        card_title="redaction",
    )

    rendered = "\n".join(
        render_target_tree(package_dir, "django_strawberry_framework/", [planned]),
    )

    assert "permissions/" in rendered
    assert "permissions.py" not in rendered


@pytest.mark.parametrize("filename", _FAKESHOP_TREE_SOURCE_FILES)
def test_fakeshop_project_tree_includes_source_file(
    filename: str,
    rendered_fakeshop_project_tree: str,
) -> None:
    """Root helpers and app sources the renderer is meant to walk appear in the tree."""
    assert filename in rendered_fakeshop_project_tree


@pytest.mark.parametrize("app_name", _FAKESHOP_APP_NAMES)
def test_fakeshop_project_tree_includes_app(
    app_name: str,
    rendered_fakeshop_project_tree: str,
) -> None:
    """Every filesystem-discovered fakeshop app is a directory in the project tree."""
    assert f"{app_name}/" in rendered_fakeshop_project_tree


def test_discovered_fakeshop_apps_equal_the_installed_local_apps() -> None:
    """The rendered app inventory is the settings' ``apps.*`` list, exactly.

    Read from the settings source rather than a configured Django so the tree
    renderer's discovery is checked against the project's own declaration, and a
    seventh app added to either side without the other fails here.
    """
    settings_text = (_FAKESHOP_PROJECT / "config" / "settings.py").read_text(
        encoding="utf-8",
    )
    installed = tuple(sorted(set(re.findall(r'"apps\.(\w+)\.apps\.', settings_text))))

    assert fakeshop_app_names(_FAKESHOP_PROJECT / "apps") == installed
    assert installed  # the regex must have found the local apps at all


@pytest.mark.parametrize("filename", _FAKESHOP_APP_LOCAL_TESTS)
def test_fakeshop_project_tree_excludes_app_local_test(
    filename: str,
    rendered_fakeshop_project_tree: str,
) -> None:
    """Each app's own tests tree is omitted from the project tree."""
    assert filename not in rendered_fakeshop_project_tree
