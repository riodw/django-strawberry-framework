"""Package-init tests pinning the ``utils`` package's re-export surface.

``django_strawberry_framework/utils/__init__.py`` re-exports a short spelling for
seven submodule names. Two things have to be pinned, because each fails silently:
the SET (a name added here is a public-surface widening, one removed strands
every consumer using the short spelling) and the IDENTITY (a re-export that
rebinds rather than forwards would let the package root and the owning submodule
drift into two different objects under one name).
"""

from django_strawberry_framework import utils
from django_strawberry_framework.utils import relations as relations_module
from django_strawberry_framework.utils import strings as strings_module
from django_strawberry_framework.utils import typing as typing_module


def test_utils_package_reexport_surface_is_pinned():
    """The short-spelling surface is exactly these seven names, in ``__all__`` order."""
    assert utils.__all__ == (
        "RelationKind",
        "is_many_side_relation_kind",
        "pascal_case",
        "relation_kind",
        "snake_case",
        "unwrap_graphql_type",
        "unwrap_return_type",
    )


def test_every_reexported_name_is_the_owning_submodules_object():
    """Each re-export forwards; none of them is a second definition under the same name."""
    assert utils.RelationKind is relations_module.RelationKind
    assert utils.is_many_side_relation_kind is relations_module.is_many_side_relation_kind
    assert utils.relation_kind is relations_module.relation_kind
    assert utils.pascal_case is strings_module.pascal_case
    assert utils.snake_case is strings_module.snake_case
    assert utils.unwrap_graphql_type is typing_module.unwrap_graphql_type
    assert utils.unwrap_return_type is typing_module.unwrap_return_type


def test_every_reexported_name_is_actually_reachable_on_the_package():
    """``__all__`` cannot list a name the package does not bind (a broken star-import)."""
    for name in utils.__all__:
        assert hasattr(utils, name), name
