"""Filter input-class BFS factory.

Layer 5 of the spec-027 six-layer pipeline: the BFS that builds every
reachable Strawberry input class via the named converter
``convert_filter_to_input_annotation``. ``DjangoConnectionField`` reads the
wrapped type's already-resolved ``Meta.filterset_class`` sidecar directly;
auto-generation of a ``FilterSet`` from ``Meta.fields`` without an explicit
class is a standing deferred Non-goal (``spec-027`` Non-goals
#"Auto-generation of `FilterSet`").

The BFS factory consumes resolved ``django-filter`` filter instances --
NOT a parallel ``FILTER_DEFAULTS`` map -- so the runtime filter shape
and the GraphQL input shape stay downstream of one decision site
(spec-027 Decision 4). The finalizer materializes the BFS factory's
built input classes as module globals at finalize time;
this module owns build-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import override

from ..utils.inputs import GeneratedInputArgumentsFactory
from .inputs import _build_input_fields, _build_logic_fields
from .sets import FilterSet

if TYPE_CHECKING:
    from ..types.definition import DjangoTypeDefinition


class FilterArgumentsFactory(GeneratedInputArgumentsFactory[FilterSet]):
    """BFS-build every reachable Strawberry input class for a ``FilterSet``.

    The BFS walk, per-class collision check, idempotent cache, and
    subclass-rejection guard live in
    ``utils/inputs.py::GeneratedInputArgumentsFactory`` (the cookbook's
    ``filter_arguments_factory.py`` BFS algorithm, single-sited with the order
    side); this subclass supplies the filter-family caches and hooks. The two
    class-level caches keep their spec-027 Decision 9 names so
    ``registry.clear()`` and the test suite address them directly:

    - ``input_object_types`` -- class-name -> built input class, shared across
      factory instances so repeated builds of the same filterset converge on
      the same input class.
    - ``_type_filterset_registry`` -- collision detection: a
      ``ConfigurationError`` fires when two distinct filtersets claim the same
      class-derived name.

    The factory does NOT materialize built classes as module globals; that is
    the finalizer's phase-2.5 contract. ``arguments`` returns the built input
    class for the root filterset (per spec-027 Decision 6 subpass 4).

    Subclassing is rejected at class-creation time (the caches are shared
    mutable dicts a subclass would inherit rather than isolate, silently
    cross-contaminating builds); extend by composition (wrap an instance),
    not inheritance.
    """

    input_object_types: ClassVar[dict[str, type[object]]] = {}
    _type_filterset_registry: ClassVar[dict[str, type[FilterSet]]] = {}

    _collision_registry_attr = "_type_filterset_registry"
    _factory_label = "FilterArgumentsFactory"
    _family_label = "FilterSet"
    _rename_noun = "filterset"
    _related_attr = "related_filters"
    _related_target_attr = "filterset"

    @override
    def _build_input_triples(
        self,
        set_cls: type[FilterSet],
        type_name: str,
        owner_definition: DjangoTypeDefinition | None,
    ) -> list[tuple[str, object, dict[str, object]]]:
        """Filter input triples plus the ``and_`` / ``or_`` / ``not_`` operator bag."""
        return [*_build_input_fields(set_cls, owner_definition), *_build_logic_fields(type_name)]
