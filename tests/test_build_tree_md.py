"""Tests for TREE renderer planned descriptions, replacements, and source discovery."""

from types import SimpleNamespace

from scripts.build_tree_md import (
    FAKESHOP_APP_NAMES,
    REPO_ROOT,
    PlannedPath,
    TargetNode,
    _planned_paths_from_rows,
    remove_target_replacements,
    render_fakeshop_project_tree,
    render_target_tree,
)


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

    assert planned.description == "planned by TODO-BETA-099-0.9.9 - `SomethingNew`"


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


def test_fakeshop_project_tree_discovers_root_helpers_and_every_app() -> None:
    rendered = "\n".join(render_fakeshop_project_tree(REPO_ROOT / "examples" / "fakeshop"))

    for filename in (
        "graphql_client.py",
        "manage.py",
        "schema_reload.py",
        "strategy_schemas.py",
    ):
        assert filename in rendered
    for app_name in FAKESHOP_APP_NAMES:
        assert f"{app_name}/" in rendered
    for app_source in ("constraints.py", "filters_genre.py", "serializers.py"):
        assert app_source in rendered


def test_fakeshop_project_tree_excludes_app_local_tests() -> None:
    rendered = "\n".join(render_fakeshop_project_tree(REPO_ROOT / "examples" / "fakeshop"))

    # App sources render...
    assert "signals.py" in rendered
    assert "factories.py" in rendered
    # ...but each app's own tests/ tree does not (it is rendered separately).
    for app_local_test in ("test_signals.py", "test_import_spec_terms.py"):
        assert app_local_test not in rendered
