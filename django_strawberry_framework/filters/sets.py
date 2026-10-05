"""``FilterSet`` + ``FilterSetMetaclass`` - declaration, validation, and the apply pipeline.

Layers 3 and 4 of the spec-027 six-layer pipeline plus the
Decision-8 named-helper decomposition of `apply_sync` /
`apply_async` / `apply`. The metaclass is a verbatim port of
`django_graphene_filters/filterset.py::FilterSetMetaclass`; `FilterSet`
mixes the cookbook's cycle-safe `get_filters` into a
`django_filters.filterset.BaseFilterSet` subclass per spec-027 Decision 5.

The Decision-4 owner-aware Relay-vs-scalar conditional lives only inside
`filter_for_field` / `filter_for_lookup` to keep the runtime override as
the single source of truth (the factory derives shape from the
resolved filter instances, not from a parallel map).
"""

from __future__ import annotations

import copy
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import cache
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar, Literal, NoReturn, SupportsIndex, TypeVar, cast

import django_filters
from django.db import models
from django.db.models import Exists, Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ManyToManyRel, ManyToOneRel, OneToOneRel
from django_filters import (
    BaseInFilter,
    BaseRangeFilter,
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    DateFilter,
    DateTimeFilter,
    DurationFilter,
    Filter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
    TimeFilter,
    UUIDFilter,
    filterset,
)
from django_filters.conf import settings as _df_settings
from django_filters.exceptions import FieldLookupError
from django_filters.utils import get_model_field, resolve_field, try_dbfield
from graphql import GraphQLError
from strawberry import UNSET
from typing_extensions import override

from ..exceptions import ConfigurationError, _safe_arg_repr
from ..optimizer.predicates import (
    attach_exists,
    correlated_inner_root,
    correlates_related_rows,
    related_rows_exist,
)
from ..registry import registry
from ..sets_mixins import (
    ActiveInputPermissionAttrs,
    ActiveInputPermissionMixin,
    ClassBasedTypeNameMixin,
    SetLifecycleAttrs,
    collect_related_declarations,
    expanded_once,
    require_re_readable_field_declaration,
    should_cache_expansion,
)
from ..types.relay import implements_relay_node
from ..utils.errors import FILTER_INVALID_ERROR_CODE, coded_error_extensions
from ..utils.input_values import (
    DEFAULT_SET_INPUT_TRAVERSAL_DEPTH,
    LEAF,
    LOGIC,
    RELATED,
    SetInputTraversal,
    is_inactive_value,
    iter_active_fields,
    iter_input_items,
    raise_set_traversal_depth_exceeded,
)
from ..utils.inputs import FILTERSET_FIELDS_ALIAS, promote_set_meta_fields
from ..utils.permissions import (
    RelationHop,
    relation_path_gates,
    walk_declared_relation_path,
)
from ..utils.querysets import (
    SyncMisuseError,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    base_queryset,
    model_for,
    relation_path_visibility_types,
    run_in_one_sync_boundary,
)
from ..utils.relations import (
    ClassifiedPath,
    classify_path,
    is_many_side_relation_kind,
    leading_relation_hops,
    path_traverses_to_many,
    relation_kind,
)
from .base import (
    _GLOBALID_RELATION_PK_ATTR,
    ArrayFilter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    IntegerInFilter,
    IntegerRangeFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
    RelationPkFilter,
    RelationPkMultipleFilter,
    _bound_field_name,
    _relation_uses_non_pk_to_field,
)
from .inputs import (
    LOGIC_OPERATORS,
    LOGIC_OPERATORS_BY_PYTHON_ATTR,
    LOGIC_OPERATORS_BY_WIRE,
    LOOKUP_NAME_MAP,
    FilterLookupTable,
    FormKeyedFilter,
    LogicOperatorDescriptor,
    _field_specs,
    filter_lookup_table,
    normalize_input_value,
)

# Python-attr tokens of the logical operator keys (``and_`` / ``or_`` / ``not_``),
# excluded from the active-permission field walk (they recurse separately).
_LOGIC_PYTHON_ATTRS: frozenset[str] = frozenset(op.python_attr for op in LOGIC_OPERATORS)

if TYPE_CHECKING:
    from types import MethodType
    from typing import TypeAlias

    from django.forms import Field as FormField
    from django_filters.filterset import FilterSetOptions

    from ..types.base import DjangoType
    from ..types.definition import DjangoTypeDefinition
    from ..utils.typing import ForeignKeyField, ModelField

    # ``(field_name, target_type, child_filterset, child_input, child_base)`` per active
    # related branch, as ``FilterSet._iter_visibility_steps`` yields it.
    _VisibilityStep: TypeAlias = (
        "tuple[str, type[DjangoType], type[FilterSet], object, models.QuerySet[models.Model]]"
    )
    #: Any forward ``ManyToManyField``, as django-stubs parametrizes it.
    _ManyToManyFieldAny: TypeAlias = models.ManyToManyField[models.Model, models.Model]
else:
    # ``ManyToManyField`` has no ``__class_getitem__`` at runtime: the hint stays the class.
    _ManyToManyFieldAny = models.ManyToManyField

_M = TypeVar("_M", bound=models.Model)


# Process-lifetime memo for ``_lookups_for_field``, keyed by field CLASS.
# A field class's concrete-lookup set is fixed by its registered class lookups
# (Django computes ``Field.get_lookups()`` from the class MRO), so it is stable
# across every instance of that class AND across ``registry.clear()`` (which
# recreates DjangoTypes / FilterSets, never Django's field classes). It
# therefore needs no clear hook -- the keys are Django field classes, not
# package types.
_lookups_for_field_class_cache: dict[type[ModelField], list[str]] = {}

# Every operator-bag lookup attr ``LOOKUP_NAME_MAP`` can generate; a mapping
# whose keys all name one is an operator bag (``FilterSet._operator_bag_items``).
_LOOKUP_PYTHON_ATTRS: frozenset[str] = frozenset(
    python_attr for python_attr, _graphql_name in LOOKUP_NAME_MAP.values()
)


def _lookups_for_field(model_field: ModelField | None) -> list[str]:
    """Return every concrete (non-transform) lookup valid for ``model_field``.

    Backs the per-field ``Meta.fields = {"<field>": "__all__"}`` shorthand
    (``graphene-django`` / cookbook ``filter_fields`` parity). ``django-filter``
    expands only the TOP-LEVEL ``fields = "__all__"``; a per-field ``"__all__"``
    value is passed through verbatim and would otherwise be mis-read as a
    literal lookup expression, so ``FilterSet.get_fields`` expands it through
    this helper.

    Django's ``Field.get_lookups()`` returns both ``Lookup`` and ``Transform``
    registrations. Transforms (``year`` / ``month`` / ``date`` / ``time`` / ...
    on temporal fields, ``unaccent`` on PostgreSQL text) are EXCLUDED: the
    cookbook's ``lookups_for_field`` expands each transform into a nested
    ``<transform>__<sublookup>`` tree consumed by Graphene's tree-shaped input
    builder, but this package's per-field operator-bag input shape (one flat
    ``<Field>FilterInputType`` bag of lookup attributes) has no nested-transform
    form. ``"__all__"`` therefore yields the flat comparison / membership /
    pattern lookups (``exact`` / ``iexact`` / ``contains`` / ``icontains`` /
    ``gt`` / ``lt`` / ``in`` / ``range`` / ``isnull`` / ``regex`` / ...); a
    consumer who wants a transform (e.g. ``created__year``) declares it as an
    explicit lookup expression instead.

    Memoized by ``type(model_field)`` (see ``_lookups_for_field_class_cache``):
    the lookup set is class-determined, so same-typed fields share one crawl.
    A COPY is returned so a caller mutating the list cannot corrupt the cache.
    """
    if model_field is None:
        return []
    field_class = type(model_field)
    cached = _lookups_for_field_class_cache.get(field_class)
    if cached is None:
        cached = [
            lookup_expr
            for lookup_expr, lookup in model_field.get_lookups().items()
            if not issubclass(lookup, models.Transform)
        ]
        _lookups_for_field_class_cache[field_class] = cached
    return list(cached)


# Constructor kwargs that only make sense on django-filter's model-choice
# family (``ModelChoiceFilter`` / ``ModelMultipleChoiceFilter`` backed by
# ``ModelChoiceField`` / ``ModelMultipleChoiceField``). Upstream's relation
# defaults stamp them into ``extra`` (``queryset`` + ``to_field_name`` per
# ``FILTER_FOR_DBFIELD_DEFAULTS``; ``empty_label`` / ``null_label`` /
# ``null_value`` ride along on single-valued relations). The package relation
# replacements (GlobalID and raw-pk) back onto plain ``CharField`` / ``Field`` /
# ``_GlobalIDMultipleChoiceField`` / ``_RelationIdentityListField`` form
# fields, which reject every one of
# these at ``Field.__init__`` -- forwarding them crashes form-field
# construction before any predicate can run.
_MODEL_CHOICE_ONLY_EXTRAS = frozenset(
    {
        "empty_label",
        "null_label",
        "null_value",
        "queryset",
        "to_field_name",
    },
)


# The package primitives a relation key in ``Meta.fields`` is converted to: the
# GlobalID pair for a Relay-node target, the raw-primary-key pair otherwise. A
# relation leaf whose generated filter is one of these is rebuilt by
# ``FilterSet.filter_for_field`` as a ``package_replacement``.
_RELATION_IDENTITY_FILTER_CLASSES: tuple[type[Filter], ...] = (
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    RelationPkFilter,
    RelationPkMultipleFilter,
)


def _strip_model_choice_extras(extra: Mapping[str, object]) -> dict[str, object]:
    """Return ``extra`` without the model-choice-only constructor kwargs.

    Used by both flat relation replacement sites (``FilterSet.filter_for_field``'s
    relation branch and ``FilterSet.filter_for_lookup``'s relation return) when a
    model-choice default is swapped for a GlobalID or raw-pk filter class whose form
    field cannot accept model-choice kwargs. Dropping the model-choice ``queryset``
    membership check is deliberate: it validated existence against the target's
    default manager, which tells a missing row from one ``get_queryset`` hides.
    """
    return {key: value for key, value in extra.items() if key not in _MODEL_CHOICE_ONLY_EXTRAS}


# Package ownership must NOT be
# derived from whatever happens to sit in django-filter's LIVE, mutable, process-shared
# ``filterset.BaseFilterSet.FILTER_DEFAULTS`` at import time. Snapshotting (even
# freezing) that global does not establish who AUTHORED its contents: any consumer,
# reusable app, or init hook that mutated the global -- a ``filter_class`` swap OR an
# ``extra`` provider swap -- BEFORE this module is imported would be frozen into the
# "package" baseline and reclassified as trusted package policy. Import order is
# realistic (installing the app imports the package root, which does NOT import
# ``filters.sets``), so the snapshot cannot be the ownership anchor.
#
# The durable architecture separates THREE concepts:
#
#   1. ``_PUBLIC_PACKAGE_FILTER_DEFAULTS`` -- a package-AUTHORED plain-``dict``
#      generation-policy table that mirrors django-filter 25.2's
#      ``FILTER_FOR_DBFIELD_DEFAULTS`` EXACTLY but is our OWN object graph, built
#      from stable importable django-filter filter CLASSES and PACKAGE-OWNED,
#      module-level ``extra`` provider functions -- never read from the mutable
#      global. It is installed as the public ``FilterSet.FILTER_DEFAULTS``. Being a
#      plain, deepcopyable ``dict`` restores django-filter's inherited consumer
#      customization seam (``copy.deepcopy(cls.FILTER_DEFAULTS)`` /
#      ``dict(cls.FILTER_DEFAULTS)`` / ``[cls][key] = ...``), which the previous
#      nested-``MappingProxyType`` install broke on every Python version.
#      django-filter reads ``FILTER_DEFAULTS`` only through
#      ``dict(cls.FILTER_DEFAULTS)`` (a fresh shallow copy) plus entry ``.get`` and
#      never mutates it (verified in the installed
#      ``django_filters.filterset.BaseFilterSet.filter_for_lookup``), so a plain
#      dict is a faithful drop-in.
#
#   2. ``_PACKAGE_POLICY_BASELINE`` -- a PRIVATE, immutable, NORMALIZED baseline
#      (``MappingProxyType`` of ``_NormalizedPolicyEntry`` records) built from the
#      package's OWN public table, never from the global. It is never installed as a
#      class attr, never exposed, and never deepcopied by consumers, so
#      ``MappingProxyType`` here is correct -- it is the immutable ownership anchor.
#      Because every ``extra`` provider is a package-owned module-level function
#      identity, a ``_NormalizedPolicyEntry`` equality (``==``) is a genuine
#      ownership signal: a pristine selection re-derives the SAME (filter_class,
#      provider) identities, while any consumer entry carries a different
#      ``filter_class`` and/or a different (consumer) provider or ``None``.
#
#   3. Selection provenance -- the ownership oracle
#      (``FilterSet._generation_origin_for_field``) compares the EFFECTIVE selection
#      (``FILTER_DEFAULTS`` merged with ``Meta.filter_overrides``) to the baseline by
#      normalized VALUE, not by object identity. The public dict and the
#      private baseline are DISTINCT object graphs, so object identity between a
#      selected raw entry and a baseline record can never hold; the anchor is a
#      normalized value comparison. This is import-order-immune (the baseline derives
#      from OUR table, never the global), catches ``filter_class`` AND
#      ``extra``-provider overrides (whole entry), and treats a consumer entry whose
#      (filter_class, extra) is byte-equal to the package policy as
#      framework-equivalent (safe -- the generated filter is identical to the
#      package's own).


def _forward_relation_extra(field: ForeignKeyField) -> dict[str, object]:
    """Package-owned mirror of upstream's ``OneToOneField`` / ``ForeignKey`` extra.

    A forward single-valued relation resolves its choice queryset and joins on the
    remote field name (``field.remote_field.field_name``); a nullable relation carries
    the configured empty-choice label. Reading the field attributes exactly as
    upstream's default lambda does keeps generation byte-identical to using
    django-filter's own table.
    """
    return {
        "queryset": filterset.remote_queryset(field),
        "to_field_name": field.remote_field.field_name,
        "null_label": _df_settings.NULL_CHOICE_LABEL if field.null else None,
    }


def _forward_m2m_extra(
    field: _ManyToManyFieldAny,
) -> dict[str, object]:
    """Package-owned mirror of upstream's ``ManyToManyField`` extra (queryset only)."""
    return {"queryset": filterset.remote_queryset(field)}


def _reverse_o2o_extra(field: OneToOneRel) -> dict[str, object]:
    """Package-owned mirror of upstream's ``OneToOneRel`` extra.

    A reverse one-to-one omits ``to_field_name`` (the reverse descriptor has no
    remote field name to join on) but keeps the null label for a nullable relation.
    """
    return {
        # basedpyright: typeshed narrows ``remote_queryset`` to ``Field``; upstream documents and
        # calls it for a ``ForeignObjectRel`` too (``related_model`` + limit choices). It rejects a
        # reverse relation for ``Field``
        "queryset": filterset.remote_queryset(field),  # pyright: ignore[reportArgumentType]
        "null_label": _df_settings.NULL_CHOICE_LABEL if field.null else None,
    }


def _reverse_rel_extra(field: ManyToOneRel | ManyToManyRel) -> dict[str, object]:
    """Package-owned mirror of upstream's ``ManyToOneRel`` / ``ManyToManyRel`` extra."""
    # basedpyright: typeshed narrows ``remote_queryset`` to ``Field`` (see ``_reverse_o2o_extra``);
    # it rejects a reverse relation for ``Field``
    return {"queryset": filterset.remote_queryset(field)}  # pyright: ignore[reportArgumentType]


# The package-AUTHORED public generation-policy table. Mirrors
# django-filter 25.2 ``FILTER_FOR_DBFIELD_DEFAULTS`` exactly, but as OUR OWN plain
# ``dict`` of plain ``dict`` entries referencing stable importable filter classes and
# the package-owned ``extra`` providers above -- NOT a snapshot of the mutable global.
# Installed as ``FilterSet.FILTER_DEFAULTS`` (deepcopyable + customizable, restoring
# django-filter's inherited extension seam).
_PUBLIC_PACKAGE_FILTER_DEFAULTS: dict[type[ModelField], dict[str, object]] = {
    models.AutoField: {"filter_class": NumberFilter},
    models.CharField: {"filter_class": CharFilter},
    models.TextField: {"filter_class": CharFilter},
    models.BooleanField: {"filter_class": BooleanFilter},
    models.DateField: {"filter_class": DateFilter},
    models.DateTimeField: {"filter_class": DateTimeFilter},
    models.TimeField: {"filter_class": TimeFilter},
    models.DurationField: {"filter_class": DurationFilter},
    models.DecimalField: {"filter_class": NumberFilter},
    models.SmallIntegerField: {"filter_class": NumberFilter},
    models.IntegerField: {"filter_class": NumberFilter},
    models.PositiveIntegerField: {"filter_class": NumberFilter},
    models.PositiveSmallIntegerField: {"filter_class": NumberFilter},
    models.FloatField: {"filter_class": NumberFilter},
    models.NullBooleanField: {"filter_class": BooleanFilter},
    models.SlugField: {"filter_class": CharFilter},
    models.EmailField: {"filter_class": CharFilter},
    models.FilePathField: {"filter_class": CharFilter},
    models.URLField: {"filter_class": CharFilter},
    models.GenericIPAddressField: {"filter_class": CharFilter},
    models.CommaSeparatedIntegerField: {"filter_class": CharFilter},
    models.UUIDField: {"filter_class": UUIDFilter},
    # Forward relationships.
    models.OneToOneField: {"filter_class": ModelChoiceFilter, "extra": _forward_relation_extra},
    models.ForeignKey: {"filter_class": ModelChoiceFilter, "extra": _forward_relation_extra},
    models.ManyToManyField: {
        "filter_class": ModelMultipleChoiceFilter,
        "extra": _forward_m2m_extra,
    },
    # Reverse relationships.
    OneToOneRel: {"filter_class": ModelChoiceFilter, "extra": _reverse_o2o_extra},
    ManyToOneRel: {"filter_class": ModelMultipleChoiceFilter, "extra": _reverse_rel_extra},
    ManyToManyRel: {"filter_class": ModelMultipleChoiceFilter, "extra": _reverse_rel_extra},
}


@dataclass(frozen=True)
class _NormalizedPolicyEntry:
    """Immutable normalized record of one generation-policy entry.

    The ownership-bearing content django-filter selects off a ``FILTER_DEFAULTS``
    entry: the ``filter_class`` (a class identity) and the ``extra`` provider (a
    module-level function identity, or ``None``). Two entries are ownership-equal iff
    both members are equal -- so a pristine re-derivation of the package table equals
    the baseline, while any consumer ``filter_class`` swap OR ``extra``-provider swap
    diverges. Frozen, so it is safe as an immutable baseline value.
    """

    filter_class: object = None
    extra: object = None


def _normalize_policy_entry(entry: Mapping[str, object] | None) -> _NormalizedPolicyEntry | None:
    """Return the ``_NormalizedPolicyEntry`` for a raw ``FILTER_DEFAULTS`` entry.

    ``None`` for a missing entry (no policy for the class), so a missing selection on
    one side compares unequal to a present entry on the other. The two ownership
    members (``filter_class`` / ``extra`` provider) are read by key exactly as
    django-filter reads them, so the normalized value captures the whole selection.
    """
    if entry is None:
        return None
    return _NormalizedPolicyEntry(entry.get("filter_class"), entry.get("extra"))


# The PRIVATE, immutable, normalized ownership anchor. Built from the
# package's OWN public table, never from the mutable global, so import order can never
# taint it. Never installed as a class attr and never exposed to consumers, so the
# ``MappingProxyType`` is correct here (unlike the public table, this is never
# deepcopied or customized). The ownership oracle compares the effective selection
# against this by normalized VALUE.
_PACKAGE_POLICY_BASELINE: Mapping[type[ModelField], _NormalizedPolicyEntry | None] = (
    MappingProxyType(
        {
            cls: _normalize_policy_entry(entry)
            for cls, entry in _PUBLIC_PACKAGE_FILTER_DEFAULTS.items()
        },
    )
)


# ======================================================================
# Audited ``django-filter`` release range for the OPTIMIZER.
#
# This gates the row-preserving correlated-``EXISTS`` OPTIMIZATION only -- never
# whether filtering works. The package dependency stays deliberately UNBOUNDED
# (``django-filter>=25.2`` in ``pyproject.toml``) so a consumer application never
# hits a resolution conflict; what is bounded is the range whose generated filter
# families, helper call graphs, form-field construction and relation reads this
# package has actually reviewed and covers with SQL-shape + semantic-parity tests.
#
# On a release OUTSIDE the audited range every leaf is non-routable, so each one
# runs django-filter's ORIGINAL outer-query invocation: identical result rows,
# JOIN + outer ``DISTINCT`` instead of the correlated subquery. Filtering is
# fully functional; only the optimization is declined. That is the fail-closed
# posture -- an unreviewed upstream release can never become eligible silently.
#
# The verdict is computed ONCE at import and read per FilterSet BUILD (see
# ``FilterSet.get_filters``), never per query.
#
# WIDENING THIS RANGE IS AN AUDIT, NOT A VERSION BUMP: the new release must pass
# the existing SQL-shape and semantic-parity suite (the generated default table,
# every registered family's call graph, dynamic ``in`` / ``range`` construction,
# and the effective relation-target reads) BEFORE the upper bound moves.
#
# Audited today: the 25.x and 26.x families -- the package test suite runs against
# django-filter 25.2 (the locked development / CI version) and 26.1 (the
# Python 3.10 + Django 5.2.16 compatibility-floor cell).
_AUDITED_DJANGO_FILTER_RANGE: tuple[tuple[int, ...], tuple[int, ...]] = ((25, 2), (27,))


def _release_is_audited(raw_version: str) -> bool:
    """Return whether ``raw_version`` falls in the audited optimizer range.

    Takes the version STRING (not the installed module) so the parse and the
    range edges are directly unit-testable without touching global state.

    Parsing FAILS CLOSED. The leading dot-separated numeric segments are read and
    the scan stops at the first non-numeric one, so a development / pre-release
    spelling (``"26.1.dev0"``) compares as its numeric prefix ``(26, 1)``. A
    version with NO leading numeric segment yields an empty prefix, which cannot
    be ``>=`` the lower bound, so an unparseable version is NOT audited.
    ``str.isdecimal`` (not ``isdigit``) is the guard because ``isdigit`` accepts
    characters ``int()`` rejects, which would raise instead of failing closed.
    """
    parsed: list[int] = []
    for segment in raw_version.split("."):
        if not segment.isdecimal():
            break
        parsed.append(int(segment))
    lower, upper = _AUDITED_DJANGO_FILTER_RANGE
    return lower <= tuple(parsed) < upper


# Evaluated ONCE at import: the installed release either is or is not audited for
# the lifetime of the process, so re-deriving it per build (let alone per query)
# would buy nothing. ``FilterSet.get_filters`` reads this constant.
_DJANGO_FILTER_OPTIMIZER_AUDITED: bool = _release_is_audited(
    getattr(django_filters, "__version__", ""),
)


# Private instance-attribute slot the frozen generation-provenance record is
# persisted under (see ``FilterGenerationProvenance``). Kept off the public
# surface so it reads as framework-internal metadata; survives ``copy.deepcopy``
# (django-filter deepcopies ``base_filters`` into per-request ``self.filters``,
# and ``_expand_related_filter`` deepcopies expansion leaves) because it lives in
# the instance ``__dict__`` and the record is an immutable frozen dataclass.
_GENERATION_PROVENANCE_ATTR = "_dst_generation_provenance"

# Origins a filter instance's generation-provenance record can carry. Ordered
# from safest to fail-closed for the candidate-metadata build, which reads the
# record rather than a class allowlist:
#   * ``framework_default``  -- generated by the UNMODIFIED default path in
#     ``FilterSet.filter_for_field`` (upstream default merged with FILTER_DEFAULTS
#     but NOT with a consumer ``Meta.filter_overrides`` entry for the field).
#   * ``package_replacement`` -- a NEW ``GlobalIDFilter`` /
#     ``GlobalIDMultipleChoiceFilter`` the package's own ``filter_for_field``
#     branches constructed; safe because the framework built the instance.
#   * ``declared``           -- a consumer-declared filter attribute (collected
#     into ``declared_filters`` by django-filter's declarative machinery).
#   * ``override_generated``  -- generated through a consumer ``Meta.filter_overrides``
#     entry matching the model field's class MRO.
FilterOrigin = Literal[
    "framework_default",
    "package_replacement",
    "declared",
    "override_generated",
]


@dataclass(frozen=True)
class FilterGenerationProvenance:
    """Immutable record of HOW a filter instance came to exist.

    Stamped on the ACTUAL returned filter instance at its moment of
    generation (``FilterSet.filter_for_field`` and the package's GlobalID
    replacement branches for generated leaves; ``FilterSetMetaclass`` for
    declared leaves). A boolean or exact-class allowlist cannot carry the
    origin distinctions eligibility later needs, because:

    - ``filter_for_field`` receives a ``default`` already pre-merged with
      ``Meta.filter_overrides`` -- a bare flag cannot tell an upstream default
      from a consumer override;
    - the own-PK / Relay-relation branches return NEW instances, so anything
      left on ``default`` never reaches the replacement;
    - upstream synthesizes dynamic ``ConcreteInFilter`` / ``ConcreteRangeFilter``
      subclasses, so exact-class lists drift across versions.

    Fail-closed by construction: a consumer that overrides ``filter_for_field``
    and returns its OWN object produces an instance WITHOUT a framework-stamped
    record (``filter_generation_provenance`` returns ``None``), so it is never
    treated as framework-generated.

    This record proves ORIGIN; it is not, on its own, the routing verdict. A
    consumer that overrides ``filter_for_field``, calls ``super()``, and MUTATES the
    returned instance keeps the framework stamp, but that authorizes nothing:
    routability additionally requires the class to have overridden NO generation seam
    (``filter_for_field`` / ``filter_for_lookup`` / ``FILTER_DEFAULTS`` /
    ``__init__`` -- see ``FilterSet._is_generation_capable``), the leaf to be an
    audited family on a to-many path, and the installed ``django-filter`` release to
    be audited. A super()+mutate subclass is non-capable, so its leaf is never routed
    regardless of what this record says. The whole verdict is assembled once, at build
    time, in ``CandidateFilterMetadata.routable``; this class is not the place a
    total-safety claim is made.

    Fields:

    - ``origin`` -- one of ``FilterOrigin``.
    - ``framework_added_distinct`` -- whether generation machinery stamped
      ``distinct=True`` on this instance because its ORM path crosses a
      many-side hop (the ``path_traverses_to_many`` stamp in
      ``filter_for_field``). Upstream django-filter's own M2M auto-``distinct``
      on a generated leaf is claimed too: on a generated (non-declared) leaf
      every to-many ``distinct`` is machinery-origin, and it is exactly the
      fan-out-compensating flag the row-preserving invocation later suppresses.
      Consumer-origin ``distinct`` can exist only on ``declared`` /
      ``override_generated`` leaves, which are ineligible by origin. The STORED
      bit is provenance/audit only: eligibility and the invocation-time distinct
      suppression both read the instance's live ``.distinct``, never this record.
    - ``expanded_from`` -- expansion breadcrumbs; empty for a non-expanded
      leaf. ``_expand_related_filter`` copies APPEND the child filter's name and
      INHERIT the child's ``origin`` + ``framework_added_distinct`` (an expanded
      copy of a DECLARED child stays ``origin="declared"``). An expanded leaf gets
      no candidate row (``_candidate_metadata_for``); ``FilterSet._expansion_origin``
      reads the breadcrumbs to name the child filter a copy answers for.
    """

    origin: FilterOrigin
    framework_added_distinct: bool = False
    expanded_from: tuple[str, ...] = ()


def filter_generation_provenance(filter_instance: object) -> FilterGenerationProvenance | None:
    """Return the frozen generation-provenance record stamped on ``filter_instance``.

    ``None`` for any instance that was never stamped (a consumer-returned
    filter object, a hand-built filter) -- the fail-closed read every
    provenance consumer routes through instead of touching the private slot.
    """
    return getattr(filter_instance, _GENERATION_PROVENANCE_ATTR, None)


def _stamp_generation_provenance(
    filter_instance: object,
    record: FilterGenerationProvenance,
) -> None:
    """Persist ``record`` on ``filter_instance`` under the private slot."""
    setattr(filter_instance, _GENERATION_PROVENANCE_ATTR, record)


# Provenance origins that mark a leaf as FRAMEWORK-GENERATED: the UNMODIFIED
# default path (``framework_default``) and the package's own GlobalID
# replacement branches (``package_replacement``). Only these leaves, and only
# the ones no ``RelatedFilter`` expansion copied, get a candidate-metadata row
# and are ever fed to the strict ``classify_path``. Declared / ``override_generated`` / unstamped leaves are
# ineligible by construction and get NO row -- fail closed at the consumption
# site, where a name absent from the mapping is a non-candidate.
_FRAMEWORK_GENERATED_ORIGINS: frozenset[FilterOrigin] = frozenset(
    {"framework_default", "package_replacement"},
)


# ======================================================================
# Executable behavior-profile registry -- the SINGLE source of truth for the
# supported generated django-filter families.
#
# A framework-generated many-side leaf is routable through the correlated
# ``EXISTS`` adapter ONLY if its filter class belongs to a family this package has
# AUDITED: whose ``.filter`` call graph, form-field construction and relation reads
# were reviewed against the correlated rewrite and are covered by the SQL-shape and
# semantic-parity suite. Enumerating those families here -- rather than describing
# "the supported generated families" in prose across the plan / glossary /
# dataclass / applicator -- makes the eligibility boundary EXECUTABLE and
# fail-CLOSED: a novel family introduced by a future ``django-filter`` release, or
# by any path that places an unaudited filter class behind a framework origin,
# resolves to NO profile, is marked ineligible by ``_candidate_metadata_for``, is
# therefore never routable, and falls back to django-filter's original outer
# invocation until it is audited and added here.
#
# Family recognition is EXACT-CLASS: a profile is minted from a known generation decision, never
# rediscovered from arbitrary ancestry. An unregistered subclass of an audited
# base is a CONSUMER-owned class whose behavior this package has not reviewed, so
# it receives NO profile -- it stays fully supported and simply runs on the outer
# queryset. The only two recognized shapes are (a) exact audited / package-owned
# classes (registry keys) and (b) django-filter's genuine empty-body dynamic
# ``in`` / ``range`` CSV classes over an exact-audited scalar family, validated
# structurally in ``_family_profile_for``.
#
# A profile is a bare family IDENTITY. There is deliberately no per-family runtime
# read table and no request-time re-verification of a leaf's behavior: routing is
# decided ONCE at build time (see ``CandidateFilterMetadata``), and process-wide
# mutation of django-filter's own classes is out of contract (see
# ``FilterSet._apply_flat_leaves``).
# ======================================================================


@dataclass(frozen=True)
class _FilterFamilyProfile:
    """Immutable IDENTITY of ONE supported generated filter family.

    A bare, hashable family tag -- nothing more. The exact-class registry
    (``_FILTER_FAMILY_REGISTRY``) maps each supported class to its profile and
    ``_family_profile_for`` returns it; ``None`` from that lookup is the fail-closed
    signal ``_candidate_metadata_for`` consumes to mark a leaf ineligible.

    It carries NO per-family read inventory and no executable behavior description. The
    profile answers exactly one question -- "is this leaf's class one of the audited
    generated families?" -- which is the eligibility half of the build-time routing
    verdict (``CandidateFilterMetadata``). A module-level singleton per family, so
    identity comparison is meaningful in tests and the set of families is closed.
    """

    name: str


# Behavior-family identities. Families with identical effective behavior MAY share one
# profile object (e.g. scalar and dynamic-CSV sequence lookups): the profile answers only
# "is this an audited generated family?", and both members are audited, so sharing never
# widens what is routable.
_SCALAR_LOOKUP_PROFILE = _FilterFamilyProfile("scalar_lookup")
_SEQUENCE_LOOKUP_PROFILE = _FilterFamilyProfile("sequence_lookup")
_CHOICE_PROFILE = _FilterFamilyProfile("choice")
_MODEL_CHOICE_PROFILE = _FilterFamilyProfile("model_choice")
_MULTIPLE_CHOICE_PROFILE = _FilterFamilyProfile("multiple_choice")
_MODEL_MULTIPLE_CHOICE_PROFILE = _FilterFamilyProfile("model_multiple_choice")
_GLOBALID_PROFILE = _FilterFamilyProfile("globalid")
_GLOBALID_MULTIPLE_PROFILE = _FilterFamilyProfile("globalid_multiple")
_RELATION_PK_PROFILE = _FilterFamilyProfile("relation_pk")
_RELATION_PK_MULTIPLE_PROFILE = _FilterFamilyProfile("relation_pk_multiple")

# Every distinct family identity, in a stable order -- the CLOSED set a registered class or
# a structurally-recognized dynamic CSV class may resolve to. The structurally-recognized
# dynamic ``in`` / ``range`` CSV classes resolve to ``_SEQUENCE_LOOKUP_PROFILE``, already in
# this tuple.
_ALL_FAMILY_PROFILES: tuple[_FilterFamilyProfile, ...] = (
    _SCALAR_LOOKUP_PROFILE,
    _SEQUENCE_LOOKUP_PROFILE,
    _CHOICE_PROFILE,
    _MODEL_CHOICE_PROFILE,
    _MULTIPLE_CHOICE_PROFILE,
    _MODEL_MULTIPLE_CHOICE_PROFILE,
    _GLOBALID_PROFILE,
    _GLOBALID_MULTIPLE_PROFILE,
    _RELATION_PK_PROFILE,
    _RELATION_PK_MULTIPLE_PROFILE,
)


# Exact-class supported-family -> profile registry. Resolution is by EXACT type
# (``_family_profile_for`` never walks the MRO), so mapping ORDER is cosmetic. ``Filter``
# itself is DELIBERATELY absent (an exact bare ``Filter`` is not a supported family), and
# so are ``BaseInFilter`` / ``BaseRangeFilter``: their ONLY job was to feed the retired
# MRO walk for django-filter's dynamic ``in`` / ``range`` CSV classes; that job now
# belongs to the structural validator in ``_family_profile_for``, which references those
# two bases directly. An arbitrary subclass of any key below is NOT audited (it may
# override ``.filter`` or add state this package never reviewed) and therefore resolves
# to NO profile.
_FILTER_FAMILY_REGISTRY: Mapping[type[object], _FilterFamilyProfile] = MappingProxyType(
    {
        # Package Relay-GlobalID relation families.
        GlobalIDMultipleChoiceFilter: _GLOBALID_MULTIPLE_PROFILE,
        GlobalIDFilter: _GLOBALID_PROFILE,
        # Package raw-primary-key relation families (the non-Relay target siblings).
        RelationPkMultipleFilter: _RELATION_PK_MULTIPLE_PROFILE,
        RelationPkFilter: _RELATION_PK_PROFILE,
        # Package typed sequence / integer families. Their effective ``.filter``
        # (including a consumer ``method=`` install that swaps in a custom
        # ``FilterMethod``) is signed by the core descriptor pair; a set ``method``
        # also makes the leaf ineligible outright. These are STATIC package classes
        # (they carry their own ``.filter`` etc.), so they are matched by exact key
        # here -- they would FAIL the empty-body dynamic-CSV check and MUST be caught
        # before it.
        IntegerInFilter: _SEQUENCE_LOOKUP_PROFILE,
        IntegerRangeFilter: _SEQUENCE_LOOKUP_PROFILE,
        ListFilter: _SEQUENCE_LOOKUP_PROFILE,
        ArrayFilter: _SEQUENCE_LOOKUP_PROFILE,
        RangeFilter: _SEQUENCE_LOOKUP_PROFILE,
        # Model-choice families and their choice bases, each an exact key with its own
        # profile (a ``ModelChoiceFilter`` reads a ``to_field`` a bare ``ChoiceFilter``
        # does not, so they are distinct entries -- exact match keeps them separate).
        ModelMultipleChoiceFilter: _MODEL_MULTIPLE_CHOICE_PROFILE,
        ModelChoiceFilter: _MODEL_CHOICE_PROFILE,
        MultipleChoiceFilter: _MULTIPLE_CHOICE_PROFILE,
        ChoiceFilter: _CHOICE_PROFILE,
        # Plain-lookup scalar Filter families, each enumerated by class (they share
        # only ``Filter`` as a base, which must never be a key). A scalar key here is
        # also the audited scalar base the dynamic-CSV validator accepts as the SECOND
        # base of a genuine ``ConcreteInFilter`` / ``ConcreteRangeFilter``.
        CharFilter: _SCALAR_LOOKUP_PROFILE,
        NumberFilter: _SCALAR_LOOKUP_PROFILE,
        BooleanFilter: _SCALAR_LOOKUP_PROFILE,
        DateFilter: _SCALAR_LOOKUP_PROFILE,
        DateTimeFilter: _SCALAR_LOOKUP_PROFILE,
        TimeFilter: _SCALAR_LOOKUP_PROFILE,
        DurationFilter: _SCALAR_LOOKUP_PROFILE,
        UUIDFilter: _SCALAR_LOOKUP_PROFILE,
    },
)


# The exact own-attribute-name set of a GENUINE empty-body dynamic CSV class. django-filter
# builds ``ConcreteInFilter`` / ``ConcreteRangeFilter`` with a ``class ... : pass`` statement,
# so such a class's OWN ``vars`` carry only the interpreter's structural dunders (``__doc__`` /
# ``__module__`` always; ``__firstlineno__`` / ``__static_attributes__`` on 3.13+). This
# reference is computed ONCE from a ``pass``-body ``class`` statement over ``Filter`` (which,
# like every scalar family, provides ``__dict__`` / ``__weakref__``, so a subclass inherits
# rather than owns them) -- matching how a real dynamic class is built. Comparing against it
# tracks the RUNNING interpreter's structural dunders instead of hardcoding a version-coupled
# allowlist, so any body member that adds state or behavior -- dunder-named (``__evil_state__``,
# an overridden ``__getattribute__`` / ``__init_subclass__``, ``__slots__``) OR not
# (``reverse``, ``filter``) -- surfaces as an extra own name and fails the check closed
# (a dunder-named member must not slip through).
class _EmptyBodyDynamicCsvReference(Filter):
    pass


_EMPTY_BODY_DYNAMIC_CSV_ATTRS: frozenset[str] = frozenset(vars(_EmptyBodyDynamicCsvReference))


def _dynamic_csv_profile_for(klass: type[object]) -> _FilterFamilyProfile | None:
    """Return the sequence profile IFF ``klass`` is a genuine dynamic ``in``/``range`` CSV class.

    django-filter builds ``class ConcreteInFilter(BaseInFilter, <scalar>): pass`` (and the
    ``BaseRangeFilter`` variant) per consumer ``in`` / ``range`` lookup on a scalar field
    -- a NEW class object each call, so it can never be a ``_FILTER_FAMILY_REGISTRY`` key,
    yet it is genuine framework machinery and must still route. Rather than trust every
    descendant of ``BaseInFilter`` / ``BaseRangeFilter`` (the retired MRO walk -- an open
    ancestry allowlist), this validates the EXACT MRO and class body, so anything a
    future django-filter release or a consumer adds fails closed:

    - ``klass.__bases__`` is exactly a 2-tuple whose FIRST element IS ``BaseInFilter`` or
      ``BaseRangeFilter`` (a genuine dynamic class has exactly ``(BaseInFilter, <scalar>)``);
    - the SECOND base (the ``<scalar>``) is itself an EXACT key in
      ``_FILTER_FAMILY_REGISTRY`` -- an audited scalar family, never an unaudited one; and
    - the dynamic class introduces NO own body beyond the interpreter's structural dunders:
      the NAME set of ``vars(klass)`` equals ``_EMPTY_BODY_DYNAMIC_CSV_ATTRS`` (the own-name
      set of a ``pass``-body reference built the same way) EXACTLY. A genuine dynamic class is
      a ``class ... : pass`` (only structural dunders in its own ``vars``); ANY added member --
      whether non-dunder (``reverse``, ``filter``) OR dunder-named state/behavior
      (``__evil_state__``, an overridden ``__getattribute__`` / ``__init_subclass__``,
      ``__slots__``) -- surfaces as an extra own name and fails closed. An exact-set compare
      (not a "startswith/endswith ``__``" test) is what keeps dunder-named members from
      slipping through, and deriving the reference from a live ``pass``-body class keeps the
      check immune to per-version structural dunders instead of hardcoding an allowlist.

    A consumer hand-crafting this exact empty-body shape over an audited scalar is
    behaviorally identical to a package-generated one (pure CSV-of-scalar semantics, no
    added state), so granting it the sequence profile is safe -- and it cannot route
    anyway unless the ownership oracle independently marks it framework-origin.
    """
    bases = klass.__bases__
    if len(bases) != 2:
        return None
    csv_base, scalar_base = bases
    if csv_base is not BaseInFilter and csv_base is not BaseRangeFilter:
        return None
    if scalar_base not in _FILTER_FAMILY_REGISTRY:
        return None
    if frozenset(vars(klass)) != _EMPTY_BODY_DYNAMIC_CSV_ATTRS:
        return None
    return _SEQUENCE_LOOKUP_PROFILE


def _family_profile_for(filter_instance: object) -> _FilterFamilyProfile | None:
    """Return the behavior profile of ``filter_instance``'s supported filter family.

    Resolution is fail-closed and never rediscovered from arbitrary ancestry:

    1. EXACT match first -- ``_FILTER_FAMILY_REGISTRY[type(filter_instance)]``. No MRO
       walk, so an unregistered subclass of an audited base is NOT accepted through its
       ancestor: a consumer subclass may override ``.filter`` or add state this package
       has never reviewed against the correlated rewrite.
    2. Otherwise, structurally-validated dynamic-CSV recognition -- django-filter's genuine
       empty-body ``ConcreteInFilter`` / ``ConcreteRangeFilter`` over an exact-audited
       scalar family resolves to ``_SEQUENCE_LOOKUP_PROFILE`` (see
       ``_dynamic_csv_profile_for``); anything that adds a method, descriptor, or
       state-bearing attribute fails closed.
    3. Otherwise ``None``.

    ``None`` is the fail-closed signal ``_candidate_metadata_for`` consumes: no profile ->
    the leaf is ineligible, so it is never routable and runs django-filter's original
    outer invocation. Upgrading django-filter therefore cannot add a routable default
    class merely through inheritance.
    """
    profile = _FILTER_FAMILY_REGISTRY.get(type(filter_instance))
    if profile is not None:
        return profile
    return _dynamic_csv_profile_for(type(filter_instance))


@dataclass(frozen=True)
class CandidateFilterMetadata:
    """Frozen row-preserving-candidate metadata for ONE direct framework-generated leaf.

    Built inside the atomic expansion snapshot (``ExpansionSnapshot``) for every
    framework-generated leaf a ``FilterSet`` generates itself; the flat-leaf
    applicator (``FilterSet._apply_flat_leaves``) reads ``routable`` to decide
    whether a ``cleaned_data`` name takes the correlated-``EXISTS`` path, for
    every leaf that walks no declared ``RelatedFilter`` hop (a walking leaf takes
    the branch path whatever its row says; ``FilterSet._flat_leaf_walk``). A leaf
    whose provenance origin is not framework-generated (declared /
    ``override_generated`` / unstamped) gets NO row at all -- fail closed, an
    absent name is a non-candidate. Neither does a leaf ``_expand_related_filter``
    copied from a ``RelatedFilter`` target: a plain copy walks its declared hop
    (``FilterSet._flat_leaf_walk``) and a ``ProjectedChildFilter``'s own
    ``filter`` runs the child filter in its set, so both answer through the
    branch (``FilterSet._apply_relation_leaf``) and no row could route either.

    The routing decision is made ONCE, HERE, at build time and frozen. There is no
    request-time re-verification of a leaf's behavior; see ``routable`` below and
    ``FilterSet._apply_flat_leaves`` for why that is the whole contract.

    Fields:

    - ``path_plan`` -- the strict ``ClassifiedPath`` of the leaf's model-field
      ``field_name`` rooted at the owning ``FilterSet._meta.model`` (via
      ``utils/relations.py::classify_path``).
      Because rows exist ONLY for proven framework-generated leaves, this is
      never ``None``; a ``PathResolutionError`` while classifying such a leaf is
      a framework/configuration defect and is allowed to RAISE (never caught).
    - ``provenance`` -- the frozen ``FilterGenerationProvenance`` record stamped
      on the leaf at generation (origin + framework-added-``distinct`` bit +
      expansion breadcrumbs).
    - ``eligible`` -- the LEAF-INTRINSIC half of the verdict: whether THIS leaf's own
      shape admits the row-preserving rewrite. ``True`` requires: a
      framework-generated origin (guaranteed here by construction, since only such
      leaves get a row), the ORM path crosses a many-side hop
      (``path_plan.first_many_index is not None``), the leaf carries no
      consumer ``method``, AND its filter class resolves to an audited supported
      family (``_family_profile_for`` is not ``None``). The last conjunct is the
      executable fail-closed boundary: an unaudited family placed behind a
      framework origin -- e.g. a
      consumer subclass, or a class introduced by a future ``django-filter`` release
      -- has no profile and is ineligible, so it is never routed until it is audited
      and registered in ``_FILTER_FAMILY_REGISTRY``. No consumer-origin ``distinct``
      check is needed: a consumer-origin ``distinct`` can exist only on a
      ``declared`` / ``override_generated`` leaf, which is already ineligible by
      origin and never reaches this record.
    - ``routable`` -- the FROZEN build-time routing verdict, and the ONLY thing the
      applicator consults for a leaf that walks no declared ``RelatedFilter`` hop.
      ``True`` iff ALL of:

      * ``eligible`` (above);
      * the OWNING filterset class, which generated the leaf, is generation-capable
        (``FilterSet._is_generation_capable`` -- it overrode none of
        ``filter_for_field`` / ``filter_for_lookup`` / ``FILTER_DEFAULTS`` /
        ``__init__``); and
      * the installed ``django-filter`` release is inside the audited optimizer range
        (``_DJANGO_FILTER_OPTIMIZER_AUDITED``).

      A row with ``routable is False`` is never routed: unless it walks a declared
      hop, its filter runs django-filter's ORIGINAL outer invocation, unchanged.
      That is the whole
      fail-closed contract -- every SUPPORTED consumer customization seam (a declared
      filter, a custom subclass, ``method=``, ``Meta.filter_overrides``, a shadowed
      ``FILTER_DEFAULTS``, an overridden generation hook, an ``__init__`` that
      replaces or mutates ``self.filters``) is refused HERE, at build time, and keeps
      working exactly as authored -- it simply does not receive the optimization.

    Deliberately NOT modelled: post-build mutation of a live per-request filter
    instance, or of ``django-filter``'s own classes. Process-wide monkeypatching is
    out of contract: code able to replace ``CharFilter.filter`` can equally replace this package's
    own methods, so no in-process signature could make it a trust boundary. This
    package protects the DOCUMENTED extension points above.
    """

    path_plan: ClassifiedPath
    provenance: FilterGenerationProvenance
    eligible: bool
    routable: bool = False


@dataclass(frozen=True)
class ExpansionSnapshot:
    """One immutable snapshot owning BOTH the expanded filters and their metadata.

    Published atomically by ``FilterSet.get_filters`` after a SUCCESSFUL
    expansion build, under the same ``should_cache_expansion`` gate as the
    expansion cache write -- never as a separate pass that could observe an
    unexpanded surface. A build failure publishes nothing (no partial snapshot).

    - ``filters`` -- a read-only ``MappingProxyType`` VIEW of the completed
      expanded-filter ``OrderedDict``. The underlying mutable ``OrderedDict`` is
      the exact object ``get_filters`` returns and is assigned unchanged to
      ``cls._expanded_filters`` / ``cls.base_filters`` (django-filter mutates
      ``base_filters`` and needs a real dict there); the snapshot exposes only
      the read-only view so a snapshot holder cannot mutate the filter half.
    - ``candidates`` -- a read-only ``MappingProxyType`` of filter name ->
      ``CandidateFilterMetadata`` for EVERY direct framework-generated leaf. Names
      of declared / override / unstamped leaves and of ``RelatedFilter``
      expansions are absent.

    The read-only mapping keeps a snapshot HOLDER from rewriting the published
    classification; it is not a claim that the filter objects themselves are frozen.
    ``base_filters`` (and thus each per-request deepcopy) remains mutable by design,
    because django-filter requires that. What makes routing safe is that the verdict
    was computed from the generation record BEFORE publication and is frozen in
    ``CandidateFilterMetadata.routable`` -- not the immutability of any dict, and not
    an inspection of the live instance at request time.

    The snapshot slot is registered in ``FilterSet._lifecycle.extra`` so
    ``registry.clear()`` resets filters and metadata together. It is
    read only from a class's OWN ``__dict__`` (via ``_expansion_snapshot``) so a
    subclass never inherits its parent's classification.
    """

    filters: Mapping[str, Filter]
    candidates: Mapping[str, CandidateFilterMetadata]


def _candidate_metadata_for(
    model: type[models.Model],
    filter_instance: Filter,
) -> CandidateFilterMetadata | None:
    """Return the frozen candidate row for a direct framework-generated leaf, else ``None``.

    ``None`` (no row -- fail closed) for any leaf whose provenance origin is not
    framework-generated: declared, ``override_generated``, or unstamped
    (consumer-returned) instances are NEVER fed to the strict classifier, since
    their ``field_name`` may legitimately be an annotation / method-owned
    non-model path and raising there would break a working declaration. ``None``
    too for a ``RelatedFilter`` expansion (``expanded_from`` breadcrumbs), which
    answers through its branch and never reads a row
    (``CandidateFilterMetadata``).

    For a direct framework-generated leaf the leaf's model-field ``field_name``
    (e.g. ``genres__name`` -- NOT the filter name with its lookup suffix) is
    strictly classified against ``model``. That ``field_name`` was derived
    entirely by the framework through the ``get_model_field``-guarded generation
    path, so a ``PathResolutionError`` there is a genuine
    framework/configuration defect and PROPAGATES (never caught).

    Eligibility is read off the plan + instance per
    ``CandidateFilterMetadata.eligible``: a many-side path, no consumer ``method``,
    AND an audited supported family (``_family_profile_for`` is not ``None``). An
    unaudited / ambiguous family resolves to no profile and is ineligible -- so a
    consumer subclass, or a future ``django-filter`` release that places a novel class
    behind a framework origin, fails CLOSED to the outer invocation until it is
    registered.

    This function computes only the leaf-INTRINSIC half. The owning class's
    generation capability and the audited-release check are applied by
    ``FilterSet.get_filters`` when it freezes ``CandidateFilterMetadata.routable``.
    """
    provenance = filter_generation_provenance(filter_instance)
    if provenance is None or provenance.origin not in _FRAMEWORK_GENERATED_ORIGINS:
        return None
    if provenance.expanded_from:
        return None
    path_plan = classify_path(model, _bound_field_name(filter_instance))
    eligible = (
        path_plan.first_many_index is not None
        and getattr(filter_instance, "method", None) is None
        and _family_profile_for(filter_instance) is not None
    )
    return CandidateFilterMetadata(
        path_plan=path_plan,
        provenance=provenance,
        eligible=eligible,
    )


if TYPE_CHECKING:

    class _FilterSetMetaclassBase(filterset.FilterSetMetaclass):
        """The class attributes upstream's metaclass ``__new__`` sets on every class it builds.

        Declared on a type-checking-only base: annotations in the metaclass body itself
        would give it an ``__annotations__`` that shadows every built class's own.
        """

        declared_filters: OrderedDict[str, Filter]
        base_filters: OrderedDict[str, Filter]
        _meta: filterset.FilterSetOptions

else:
    _FilterSetMetaclassBase = filterset.FilterSetMetaclass


class FilterSetMetaclass(_FilterSetMetaclassBase):
    """Discover `RelatedFilter` declarations and bind them to the new class.

    Direct port of `django_graphene_filters/filterset.py::FilterSetMetaclass`.
    Expansion of related filters into per-lookup ORM paths is deferred to
    `FilterSet.get_filters` so circular `RelatedFilter` references
    declared in the same module are legal. ``Meta.filter_fields`` aliasing
    is ``utils/inputs.py::promote_set_meta_fields`` (shared with
    ``OrderSetMetaclass``).
    """

    def __new__(
        cls,
        name: str,
        bases: tuple[type[object], ...],
        attrs: dict[str, object],
    ) -> FilterSetMetaclass:
        """Build the class, collect `RelatedFilter`s, and bind them to the owner."""
        class_items = tuple(attrs.items())

        # ``filter_fields`` is the cookbook / graphene-django synonym for
        # ``Meta.fields``. Write-back is
        # ``utils/inputs.py::promote_set_meta_fields`` so ``OrderSetMetaclass``
        # cannot drift from class-Meta aliasing. The consumer's
        # ``filter_fields`` attribute is left in place. Presence uses
        # ``hasattr`` (inherited Meta attributes count).
        promote_set_meta_fields(attrs.get("Meta"), fields_alias=FILTERSET_FIELDS_ALIAS)

        # Upstream's ``__new__`` is typed to return its own metaclass; ``cls`` built it.
        new_class = cast("FilterSetMetaclass", super().__new__(cls, name, bases, attrs))

        # Collect the ``RelatedFilter`` declarations and bind each to the new
        # class via the shared set-family collector.
        # ``declared_filters`` supplies the django-filter-ordered candidate
        # stream; the shared collector reconciles it against the unmodified class
        # body and direct-base precedence so a tombstone cannot be lost in a
        # diamond hierarchy.
        related_candidates = {
            name
            for name, declaration in new_class.declared_filters.items()
            if isinstance(declaration, RelatedFilter)
        }
        related_filters = collect_related_declarations(
            new_class,
            bases,
            own_items=new_class.declared_filters.items(),
            declaration_type=RelatedFilter,
            collection_attr="related_filters",
            inherit_from_bases=False,
            class_items=class_items,
            base_declarations_attr="declared_filters",
        )
        removed_candidates = related_candidates - related_filters.keys()
        if removed_candidates:
            for field_name in removed_candidates:
                del new_class.declared_filters[field_name]
            # ``django-filter`` computed ``base_filters`` during ``super().__new__``.
            # Rebuild from the now-corrected declaration map through its
            # implementation so model-generated filters remain intact.
            new_class.base_filters = filterset.BaseFilterSet.get_filters.__func__(
                new_class,
            )

        # Stamp consumer-declared filter attributes with a ``declared`` provenance
        # record. ``declared_filters`` is the authoritative declarative collection,
        # these instances never route through ``filter_for_field`` (django-filter's
        # ``get_filters`` copies them in verbatim), and the metaclass runs once per
        # class. The authoritative boundary is declaration OWNERSHIP, not the mere
        # presence of a provenance record:
        #
        # * An OWN declaration -- a ``django_filters.Filter`` (``RelatedFilter`` is
        #   a ``Filter`` subclass) assigned directly in THIS class body -- makes
        #   its filter object consumer-owned REGARDLESS of any provenance it
        #   already carries, so it transitions UNCONDITIONALLY to
        #   ``origin="declared"``. django-filter's declarative machinery lets a
        #   consumer deepcopy/borrow a filter instance obtained from another
        #   filterset's ``base_filters`` (which may still carry a framework
        #   ``framework_default`` / ``package_replacement`` stamp) and assign it
        #   here; keeping the old stamp would let ``_candidate_metadata_for`` /
        #   ``get_filters._build`` re-authorize a now-consumer declaration through
        #   the correlated ``EXISTS`` adapter.
        # * An INHERITED declaration was already stamped ``declared`` by its owning
        #   class's metaclass run, so restamping it is a no-op; the
        #   ``provenance is None`` arm only BACKFILLS an inherited declaration that
        #   somehow lacks a record.
        #
        # Both arms want the same ``declared`` record, so they are one condition.
        #
        # ``new_class.declared_filters`` is the merged MRO map (own + inherited);
        # own-ness is computed from the class body (``class_items``, captured at the
        # top of ``__new__`` before ``super().__new__`` popped the ``Filter``
        # attributes out of ``attrs``), never from whether a private attribute
        # happens to exist.
        own_declared_names = {
            attr_name for attr_name, attr_value in class_items if isinstance(attr_value, Filter)
        }
        for declaration_name, declaration in new_class.declared_filters.items():
            if (
                declaration_name in own_declared_names
                or filter_generation_provenance(declaration) is None
            ):
                _stamp_generation_provenance(
                    declaration,
                    FilterGenerationProvenance(origin="declared"),
                )

        return new_class


@dataclass(frozen=True)
class ChildProjection:
    """Where an owner-bound expanded leaf runs: the child filter set, its filter's name, the branch.

    ``branch`` is the parent's ``RelatedFilter`` attribute the leaf was expanded
    from: the declared hop whose target visibility scopes the child rows and
    whose relation and explicit ``queryset=`` restrict the parent
    (``FilterSet._projection_hop``).
    """

    filterset: type[FilterSet]
    name: str
    branch: str


class ProjectedChildFilter(Filter):
    """A ``RelatedFilter`` expansion of a child filter whose behavior the child filter set owns.

    Rebinding ``field_name`` reproduces a filter only while its behavior is a
    function of the filter object alone (``field_name``, ``lookup_expr``,
    ``exclude``, ``distinct``, the form field its class builds). django-filter
    hangs two behaviors off the OWNING filter set instead: a ``method=`` resolves
    on ``filter.parent`` (a string by attribute lookup; a callable by the model
    its body was written for), and a filter set ``__init__`` override may replace
    or mutate any of ``self.filters`` after the per-request deepcopy. A plain
    copy of such a filter on the parent has no owner: the method resolves on the
    parent class, and the child's ``__init__`` never runs for the copy.

    ``_expand_related_filter`` therefore builds this copy for every owner-bound
    child leaf (``_owner_bound_child``): an instance of the child filter's own
    class (``_projected_class_for``), so input typing, value normalization and
    family recognition see the class they always saw, carrying a
    ``ChildProjection``. Bound to a parent filter set instance, its form field is
    the one a CHILD filter set instance builds for the child filter (one child
    instance per parent instance and child class, ``FilterSet._projection_child``;
    a child ``__init__`` customization and a request-aware callable ``queryset``
    both apply), and ``filter`` runs the child filter inside that instance over
    the branch's visible child rows (the target type's ``get_queryset`` on the
    parent's database, as the nested branch scopes them; spec-027 Decision 8
    step 3), then answers at the parent through the rows the declaration's
    explicit ``queryset=`` admits (``FilterSet._apply_relation_leaf``, the
    application every flat leaf walking a declared hop shares): a positive child
    filter keeps the parents reaching a matching child row, an ``isnull=True``
    one also the parents reaching no visible child row, and an ``exclude=True``
    one the parents its positive twin does not keep (a ``method=`` child filter
    stays positive). A child filter that is
    itself a relation leaf of the child set walks its own hops the same way.
    Each flat leaf stays its own predicate, as every flat leaf does: two
    owner-bound leaves may be satisfied by different child rows.

    Unbound (the class-level template the input builder types at schema build,
    before any parent instance exists), the form field is the child's own
    class-level filter's, exactly what the plain copy answered.
    """

    _projection: ChildProjection
    # The child filter's own class this projected class was built from
    # (``_projected_class_for``); set on each built class, never on this base.
    _projected_from: ClassVar[type[Filter]]

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> tuple[object, ...]:
        """Reduce through the child filter's own class, which pickle can name.

        The projected class is built at runtime, so pickle cannot import it by
        name; the copy rebuilds it from ``_projected_from`` (one class per
        filter class, so the round trip lands on the same class). ``deepcopy``
        reduces the same way.
        """
        return (_new_projected, (self._projected_from,), vars(self))

    def _child(self) -> FilterSet:
        """Return the child filter set instance this leaf runs in, shared per parent instance."""
        # django-filter's ``BaseFilterSet.__init__`` stamps ``filter_.parent = self``
        # on every per-request copy (never on the class-level template); only a
        # package ``FilterSet`` expands a ``RelatedFilter``, so the parent is one.
        parent = cast("FilterSet", getattr(self, "parent"))  # noqa: B009
        return parent._projection_child(self._projection.filterset)

    @property
    @override
    def field(self) -> FormField:
        """The child filter's form field: the child instance's once bound, the child class's before."""
        projection = self._projection
        if getattr(self, "parent", None) is None:
            return projection.filterset.base_filters[projection.name].field
        return self._child().filters[projection.name].field

    @override
    def filter(self, qs: models.QuerySet[_M], value: object) -> models.QuerySet[_M]:
        """Run the child filter over the branch's visible child rows; answer at the parent.

        An inactive child filter (one that returns its input BY IDENTITY)
        leaves the parent unchanged and runs no ``get_queryset``
        (``FilterSet._apply_relation_leaf``).
        """
        # See ``_child`` for the ``parent`` stamp.
        parent = cast("FilterSet", getattr(self, "parent"))  # noqa: B009
        return parent._apply_relation_leaf(qs, self, value)


@cache
def _projected_class_for(filter_cls: type[Filter]) -> type[ProjectedChildFilter]:
    """Return the projected subclass of ``filter_cls``, one per class; a projected class is its own."""
    if issubclass(filter_cls, ProjectedChildFilter):
        return filter_cls
    return cast(
        "type[ProjectedChildFilter]",
        type(
            f"Projected{filter_cls.__name__}",
            (ProjectedChildFilter, filter_cls),
            {"_projected_from": filter_cls},
        ),
    )


def _new_projected(filter_cls: type[Filter]) -> ProjectedChildFilter:
    """Return an empty instance of ``filter_cls``'s projected class (``__reduce_ex__``'s rebuild)."""
    return object.__new__(_projected_class_for(filter_cls))


def _owner_bound_child(child_filterset: type[FilterSet], child_filter: Filter) -> bool:
    """Whether ``child_filter``'s behavior belongs to ``child_filterset``, not to the filter object.

    A ``method=`` filter resolves on, or was written for, its owner; every
    filter of a filter set that overrides ``__init__`` may have been edited by
    it (``FilterSet._customizes_instances``, the seam the optimizer closes for
    the same reason); a projected copy already runs inside its owner and is
    re-projected at the next hop. A ``RelatedFilter`` is a branch, never a flat
    leaf, so it is copied as is.
    """
    if isinstance(child_filter, RelatedFilter):
        return False
    return (
        isinstance(child_filter, ProjectedChildFilter)
        or child_filter.method is not None
        or child_filterset._customizes_instances()
    )


def _restrict_to_related(
    queryset: models.QuerySet[_M],
    relation: str,
    related_rows: models.QuerySet[models.Model],
    via: Sequence[models.QuerySet[models.Model] | None] = (),
) -> models.QuerySet[_M]:
    """Keep the rows of ``queryset`` whose ``relation`` reaches a row of ``related_rows``.

    The restriction is ``optimizer/predicates.py::related_rows_exist``: a
    correlated ``EXISTS`` built from ``related_rows`` (the target side), never a
    join onto ``queryset``, so a parent with N matching children is kept once
    (no duplicate nodes, no corrupted pagination counts) without a
    ``.distinct()`` that would mutate consumer-visible queryset state. It reads
    neither the parent table again nor anything ``queryset`` already applied,
    so each restriction a filter set adds is one semi-join of its own. A nested
    branch and a flat leaf walking the branch both restrict through it, so the
    two spellings answer alike. The subquery compiles on ``queryset``'s
    database alias, the one its intermediate rows are read on too. ``via``
    holds the rows each intermediate model of a ``relation`` spanning several
    relations may pass through (``FilterSet._via_rows``).
    """
    return queryset.filter(_reaches_related(queryset, relation, related_rows, via))


def _reaches_related(
    queryset: models.QuerySet[_M],
    relation: str,
    related_rows: models.QuerySet[models.Model],
    via: Sequence[models.QuerySet[models.Model] | None] = (),
) -> Exists:
    """Return the ``_restrict_to_related`` test itself, for a caller that composes or negates it."""
    return related_rows_exist(queryset.model, relation, related_rows, using=queryset.db, via=via)


def _admitted_rows(
    owner: type[object],
    declared_attr: str,
    related_filter: RelatedFilter,
    child_rows: models.QuerySet[models.Model] | None,
) -> models.QuerySet[models.Model] | None:
    """Return the child rows a declared branch admits: ``child_rows`` within the explicit ``queryset=``.

    ``owner`` declares ``related_filter`` under ``declared_attr``. ``child_rows``
    (the branch's visibility-scoped, possibly filtered rows) is intersected with
    the declaration's explicit ``queryset=``; ``child_rows`` of ``None`` admits
    the explicit queryset alone, and with neither the branch admits no
    restriction (``None``).
    """
    # ``_has_explicit_queryset`` records that ``queryset=`` was passed; the
    # ``ModelChoiceFilter`` contract types it as a queryset.
    explicit = cast(
        "models.QuerySet[models.Model] | None",
        related_filter.extra.get("queryset") if related_filter._has_explicit_queryset else None,
    )
    if child_rows is None:
        return explicit
    if explicit is None:
        return child_rows
    # Django raises an opaque ``TypeError: Cannot combine queries on two
    # different base models`` from ``Query.combine`` if the consumer-supplied
    # ``RelatedFilter(queryset=...)`` is keyed on a different model class than
    # the target filterset's ``_meta.model``. Surface a typed
    # ``ConfigurationError`` naming the filter and both models so a GraphQL
    # consumer gets an actionable message instead of the raw ``TypeError``.
    #
    # The comparison uses ``is`` identity because Django's own
    # ``Query.combine`` does the same (``self.model != rhs.model``) - proxies
    # and multi-table-inheritance children carry distinct ``model``
    # identities even though they share a database table with their concrete
    # parent. Consumers who need to mix proxy / concrete must pass an explicit
    # queryset of the target filterset's exact ``_meta.model`` class.
    if explicit.model is not child_rows.model:
        raise ConfigurationError(
            f"RelatedFilter {owner.__qualname__}.{declared_attr}: "
            f"the explicit ``queryset=`` is keyed on "
            f"{explicit.model.__qualname__} but the target "
            f"filterset is keyed on "
            f"{child_rows.model.__qualname__}. Pass a queryset "
            f"of {child_rows.model.__qualname__} instances to "
            "``RelatedFilter(queryset=...)``; proxy and "
            "multi-table-inheritance children are NOT "
            "accepted because Django's queryset ``&`` "
            "operator rejects mixed model classes.",
        )
    return explicit & child_rows


def _restrict_through_branch(
    queryset: models.QuerySet[_M],
    owner: type[object],
    declared_attr: str,
    related_filter: RelatedFilter,
    child_rows: models.QuerySet[models.Model] | None,
    via: Sequence[models.QuerySet[models.Model] | None] = (),
) -> models.QuerySet[_M]:
    """Keep the rows of ``queryset`` whose branch relation reaches an admitted child row.

    The one restriction a declared ``RelatedFilter`` branch applies to the set
    that declares it (``owner``, under ``declared_attr``), for a nested branch
    and a flat leaf walking the branch alike: ``_admitted_rows`` intersects
    ``child_rows`` with the declaration's explicit ``queryset=``, then
    ``_restrict_to_related`` keeps the parents reaching a row of the result,
    through the ``via`` rows of each intermediate model a multi-relation
    ``field_name`` crosses. With neither ``child_rows`` nor an explicit
    queryset, ``queryset`` is returned unchanged.

    The restriction follows the relation's ORM path (``related_filter.field_name``),
    NOT the declared attribute name. The two diverge whenever a consumer gives a
    ``RelatedFilter`` a friendlier GraphQL name than its ORM accessor (e.g.
    ``visible_shelves = RelatedFilter(ShelfFilter, field_name="shelves")``);
    keying off the declared name would name a non-existent relation and Django
    would raise ``FieldError``.
    """
    admitted = _admitted_rows(owner, declared_attr, related_filter, child_rows)
    if admitted is None:
        return queryset
    return _restrict_to_related(queryset, _bound_field_name(related_filter), admitted, via)


def _relation_key_value(value: object, attname: str) -> object:
    """Read a relation-key leaf's model-choice value as the key column it compares.

    django-filter's model-choice filters clean to model instances (one, a list,
    or a queryset), which a relation lookup normalizes to the key column and a
    plain column lookup rejects; a leaf re-read against the target rows' own key
    column (``FilterSet._leaf_chain``) gets each instance's ``attname`` value
    instead. Every other value (a raw key, a GlobalID) passes unchanged.
    """
    if isinstance(value, models.Model):
        return getattr(value, attname)
    if isinstance(value, (list, tuple, models.QuerySet)):
        return [_relation_key_value(member, attname) for member in iter(value)]
    return value


@dataclass(frozen=True)
class _LeafChain:
    """How an active flat leaf walking relation hops reads the related rows.

    ``terminal`` runs over the visible rows of the last of ``hops`` (over the
    parent's own rows when ``hops`` is empty), already bound to the set whose
    rows those are. ``key_hop`` is the last hop of a forward relation key leaf,
    which ``terminal`` compares on the rows that hold the key: a row it matches
    must also reach a visible row of ``key_hop``. ``key_attname``
    names the target key column a to-many relation key leaf was re-read against
    (``_relation_key_value``).
    """

    hops: tuple[RelationHop, ...]
    terminal: Filter
    key_hop: RelationHop | None = None
    key_attname: str | None = None

    def terminal_value(self, value: object) -> object:
        """The value ``terminal`` receives: ``value``, read as the target key for a to-many key leaf."""
        if self.key_attname is None:
            return value
        return _relation_key_value(value, self.key_attname)


def _hop_model(hop: RelationHop) -> type[models.Model]:
    """Return the model whose rows a resolved hop reaches.

    A declared hop's target set's ``Meta.model``; an undeclared hop's ``model``.
    """
    if hop.declared:
        # A resolved branch target is a ``FilterSet`` declaring ``Meta.model``.
        return cast("type[models.Model]", cast("type[FilterSet]", hop.target)._meta.model)
    # The walk records the model of every undeclared hop it appends.
    return cast("type[models.Model]", hop.model)


def _hop_relation(hop: RelationHop) -> str:
    """Return the ORM path a hop crosses from the model it starts on."""
    if hop.declared:
        return _bound_field_name(cast("RelatedFilter", hop.related_obj))
    return hop.declared_attr


def _hop_source_model(hops: tuple[RelationHop, ...], index: int) -> type[models.Model]:
    """Return the model ``hops[index]`` starts on: its owner set's model, else the previous hop's."""
    owner = hops[index].owner
    if owner is not None:
        return cast("type[models.Model]", cast("type[FilterSet]", owner)._meta.model)
    # Only an undeclared hop following another undeclared hop has no owner.
    return _hop_model(hops[index - 1])


class _UndeclaredHopSet:
    """The filter-set face a walked leaf's terminal reads over an undeclared hop's rows.

    No filter set owns the rows a relation no ``RelatedFilter`` declares reaches,
    so the copy of a leaf that runs over them (``FilterSet._bound_terminal``) is
    bound to this instead of a child filter set instance: ``_meta.model`` is the
    hop's model (a raw-key or integer terminal coerces through it),
    ``_owner_definition`` the definition of the type the rows answer for (a
    GlobalID terminal validates against it) and ``request`` the walking set's.
    """

    def __init__(self, hop: RelationHop, request: object) -> None:
        """Bind the face to ``hop``'s model and target type, with the walking set's request."""
        self._meta = filterset.FilterSetOptions()
        self._meta.model = _hop_model(hop)
        self._owner_definition: DjangoTypeDefinition | None = (
            hop.target_type.__django_strawberry_definition__
            if hop.target_type is not None
            else None
        )
        self.request = request


def _require_relation_path(owner: type[FilterSet], declared_attr: str, f: RelatedFilter) -> None:
    """Refuse a ``RelatedFilter`` whose ``field_name`` is not a path of relations on ``owner``'s model.

    A branch restricts its parent through every segment of its ``field_name``
    (``optimizer/predicates.py::related_rows_exist``), so each segment must be a
    relation Django can join (``utils/relations.py::leading_relation_hops`` covers
    them all): a column (``title__shelf``), a name the model does not carry, or
    a ``GenericForeignKey`` is a declaration error, raised when the expansion is
    built rather than on the first request that supplies the branch. Reads the
    owner's model and the declaration's ``field_name`` only, never the target
    filter set, so a lazily resolved target is unaffected.
    """
    field_name = _bound_field_name(f)
    # Only model-backed sets expand their ``related_filters`` (see ``get_filters``).
    model = cast("type[models.Model]", owner._meta.model)
    hops = leading_relation_hops(model, field_name)
    segments = field_name.split(LOOKUP_SEP)
    if len(hops) < len(segments):
        raise ConfigurationError(
            f"FilterSet {owner.__qualname__}: RelatedFilter {declared_attr!r} has "
            f"field_name {field_name!r}, but {segments[len(hops)]!r} is not a relation "
            f"of the model the path has reached from {model.__qualname__}. A "
            "RelatedFilter's field_name must name a path of relations.",
        )


def _require_correlated_target(
    owner: type[FilterSet],
    declared_attr: str,
    f: RelatedFilter,
) -> None:
    """Refuse a ``RelatedFilter`` whose target set's model is not one its relation's rows correlate as.

    A branch restricts its parent through rows of the target filter set's
    ``Meta.model`` (``FilterSet._branch_visibility_seed`` seeds them,
    ``optimizer/predicates.py::related_rows_exist`` correlates them by the
    relation's own link columns), so that model must be one whose rows the
    relation's last link reads as the rows it reaches
    (``optimizer/predicates.py::correlates_related_rows``): the relation's target,
    a proxy on its table, or a multi-table-inheritance descendant keyed by its
    parent link, and an ancestor only across a forward or many-to-many link
    whose columns it carries. Any other model matches parents whose link value
    merely equals one of its columns (on a reverse link an ancestor's row
    matches itself), so it is a declaration error, raised by the build that
    expands the branch: the target is resolved here, whatever form it was
    declared in (a class, an import path, a factory), so a lazily declared
    target is checked exactly when its leaves are first copied onto the parent.
    The ``None`` placeholder expands nothing and is not checked.
    """
    target = f.filterset
    if target is None:
        return
    field_name = _bound_field_name(f)
    # Only model-backed sets expand their ``related_filters`` (see ``get_filters``).
    model = cast("type[models.Model]", owner._meta.model)
    target_model: type[models.Model] | None = target._meta.model
    if target_model is not None and correlates_related_rows(model, field_name, target_model):
        return
    # ``_require_relation_path`` proved every segment a relation hop.
    reached = leading_relation_hops(model, field_name)[-1].target_model
    keyed_on = (
        f"is keyed on {target_model.__qualname__}"
        if target_model is not None
        else "declares no Meta.model"
    )
    raise ConfigurationError(
        f"FilterSet {owner.__qualname__}: RelatedFilter {declared_attr!r} has field_name "
        f"{field_name!r}, which reaches {reached.__qualname__}, but its target FilterSet "
        f"{target.__qualname__} {keyed_on}. A RelatedFilter's target FilterSet must be "
        f"keyed on {reached.__qualname__}, a proxy of it, or a multi-table-inheritance "
        "child of it (an ancestor only across a forward or many-to-many relation whose "
        "columns it carries).",
    )


def _expand_related_filter(filter_name: str, f: RelatedFilter) -> OrderedDict[str, Filter]:
    """Expand `f` against its target filterset's resolved filters.

    Port of the cookbook's `expand_related_filter`: each child filter is
    deep-copied onto the parent under ``<filter_name>__<child name>`` with
    ``field_name`` rebound to the relation path, so the target filterset's own
    instances are never mutated. A child filter whose behavior the child filter
    set owns (``_owner_bound_child``) is copied as a ``ProjectedChildFilter``
    instead, since a rebind cannot carry a ``method=`` or a child ``__init__``.
    Module-level helper because the expansion has no metaclass state - moving
    it off the metaclass keeps the call site (``get_filters``) free of
    ``cls.__class__.expand_related_filter(cls, ...)`` indirection that obscured
    the function's purpose.
    """
    expanded: OrderedDict[str, Filter] = OrderedDict()
    target_filterset = f.filterset
    if not target_filterset:
        return expanded
    target_filters = target_filterset.get_filters()
    relation = _bound_field_name(f)
    for child_name, field in target_filters.items():
        new_name = f"{filter_name}__{child_name}"
        field_copy = copy.deepcopy(field)
        field_copy.field_name = f"{relation}__{field.field_name}"
        if _owner_bound_child(target_filterset, field):
            field_copy.__class__ = _projected_class_for(type(field_copy))
            projected = cast("ProjectedChildFilter", field_copy)
            projected._projection = ChildProjection(target_filterset, child_name, filter_name)
            # django-filter's ``method`` setter shadows ``filter`` per INSTANCE with a
            # ``FilterMethod`` (the package's list filters install theirs the same
            # way); the copy carried that shadow, which would resolve the method on
            # the parent. The child's own filter, inside the child instance, keeps
            # its shadow; the projection's class-level ``filter`` runs here.
            vars(projected).pop("filter", None)
        # Inherit the CHILD leaf's frozen provenance record and APPEND the child
        # filter's name as an expansion breadcrumb, without mutating the child's
        # record (a new frozen record via ``replace``). Origin +
        # framework_added_distinct are inherited unchanged, so an expanded copy of
        # a DECLARED child stays ``origin="declared"`` and an unstamped child
        # (e.g. a consumer-returned object) yields an unstamped copy -- the
        # deepcopy carried no record and none is added, so it fails closed.
        child_record = filter_generation_provenance(field)
        if child_record is not None:
            _stamp_generation_provenance(
                field_copy,
                replace(child_record, expanded_from=(*child_record.expanded_from, child_name)),
            )
        expanded[new_name] = field_copy
    return expanded


class FilterSet(
    ClassBasedTypeNameMixin,
    ActiveInputPermissionMixin,
    filterset.BaseFilterSet,
    metaclass=FilterSetMetaclass,
):
    """Consumer-facing `FilterSet` foundation.

    Subclasses `django_filters.filterset.BaseFilterSet` directly per
    spec-027 Decision 5; the cookbook's lazy-resolution Layers 3 and 4
    are folded in via `FilterSetMetaclass` and `get_filters`. The
    Decision-8 named helpers decompose `apply_sync` and
    `apply_async` so each step can be exercised in isolation; `apply`
    stays as a thin dispatcher that translates the typed
    `SyncMisuseError` from `apply_type_visibility_sync` into a
    `RuntimeError` consumers can match on.

    `_owner_definition` is the binding seam populated by
    `finalize_django_types` phase 2.5; the slot declared
    `None` and the fallback branch in `filter_for_field` /
    `filter_for_lookup` that consults `registry.primary_for(...)` keeps
    package-internal tests able to exercise the Relay-vs-scalar
    conditional before owner binding lands.
    """

    # The package-AUTHORED public generation-policy table. Installed in place of django-filter's
    # mutable, process-shared ``BaseFilterSet.FILTER_DEFAULTS`` -- but as our OWN
    # plain, deepcopyable ``dict`` (``_PUBLIC_PACKAGE_FILTER_DEFAULTS``), NOT a
    # snapshot of the global -- so package ownership derives from a table this module
    # authored and the inherited django-filter customization seam (``deepcopy`` /
    # ``dict(...)`` / ``[cls][key] = ...``) keeps working. An unmodified subclass
    # inherits this by identity (``_is_generation_capable`` checks it); ownership is
    # decided against the PRIVATE normalized ``_PACKAGE_POLICY_BASELINE`` by value, not
    # against this public object's identity.
    # basedpyright: the stub keys ``FILTER_DEFAULTS`` by ``type[Field]``, but django-filter's own
    # table also keys the reverse relations (``OneToOneRel`` / ``ManyToOneRel`` /
    # ``ManyToManyRel``); it rejects the invariant override with the true wider key
    FILTER_DEFAULTS: ClassVar[dict[type[ModelField], dict[str, object]]] = (  # pyright: ignore[reportIncompatibleVariableOverride]
        _PUBLIC_PACKAGE_FILTER_DEFAULTS
    )

    # Binding seam - populated by `finalize_django_types` phase 2.5.
    _owner_definition: DjangoTypeDefinition | None = None

    # Cache for fully-resolved filters per Layer 4 of Decision 3.
    _expanded_filters = None
    # The immutable expansion snapshot (``ExpansionSnapshot``) owning the
    # expanded filters AND the row-preserving-candidate metadata, published
    # atomically beside ``_expanded_filters`` inside ``get_filters`` under the
    # same ``should_cache_expansion`` gate. Registered in ``_lifecycle.extra``
    # (below) so ``registry.clear()`` resets it together with the filter cache;
    # a free-floating slot would survive the clear that deletes
    # ``_expanded_filters`` and pair stale metadata with a rebuilt
    # ``base_filters``. Read
    # ONLY through ``cls._expansion_snapshot()`` (a class's OWN ``__dict__``) so
    # a subclass never inherits its parent's classification.
    _expanded_snapshot: ClassVar[ExpansionSnapshot | None] = None
    # Each operator-bag lookup's form key, grouped once per ``get_filters()``
    # result (``inputs.py::filter_lookup_table``). The table names the
    # ``get_filters()`` object it was built from and is rebuilt when that
    # object changes, so an inherited or pre-clear table is never read.
    _lookup_table: ClassVar[FilterLookupTable | None] = None
    # Recursion guard around `get_filters` so a self-referential
    # `RelatedFilter` does not blow the stack.
    _is_expanding_filters = False

    # Family binding-state descriptor: the single source for the lifecycle attr
    # names `get_filters` (via `expanded_once`) and `registry.clear()` (via
    # `clear_filter_input_namespace`'s `binding_attrs`) reference, instead of
    # re-spelling the tuple.
    _lifecycle: ClassVar[SetLifecycleAttrs] = SetLifecycleAttrs(
        owner="_owner_definition",
        cache="_expanded_filters",
        guard="_is_expanding_filters",
        # The candidate-metadata snapshot rides the same clear as the filter
        # cache so filters + metadata reset together.
        extra=("_expanded_snapshot",),
    )

    # Family permission-facade config: the single source ``ActiveInputPermissionMixin``
    # reads instead of re-spelling related_attr / UNSET / logic keys on every
    # thin wrapper. Shared with ``OrderSet`` through the mixin; apply pipelines
    # stay family-owned.
    _permission: ClassVar[ActiveInputPermissionAttrs] = ActiveInputPermissionAttrs(
        family_label="FilterSet",
        target_attr="filterset",
        traversal=SetInputTraversal(
            field_specs=_field_specs,
            related_attr="related_filters",
            logic_keys=_LOGIC_PYTHON_ATTRS,
            unset_sentinel=UNSET,
        ),
    )

    # Logical-branch (`and` / `or` / `not`) recursion-depth cap. Declared
    # as a `ClassVar` so a consumer with a legitimate deeper-nesting case
    # (machine-generated queries, faceted search) can subclass and raise
    # the cap without monkey-patching a module constant. Eight levels
    # covers every realistic consumer-driven graph; beyond it a typed
    # `ConfigurationError` surfaces the misuse at the source instead of a
    # Python `RecursionError`.
    _MAX_LOGIC_DEPTH: ClassVar[int] = DEFAULT_SET_INPUT_TRAVERSAL_DEPTH

    # Depth hand-off channel for the tree-form logic recursion. Set on a
    # sibling instance by `_q_for_branch` so `filter_queryset` can read
    # the counter back across django-filter's `.qs` boundary (which we do
    # not own and cannot thread kwargs through). Declared here so the
    # attribute is discoverable to static analysis / `__slots__` / typing
    # and the default is explicit on every instance.
    _logic_depth: int = 0

    # Resolver-``info`` hand-off channel, threaded the same way as
    # `_logic_depth`: set by `apply_sync` / `apply_async` on the top-level
    # instance and by `_q_for_branch` on each sibling so nested logical
    # branches can re-derive their `RelatedFilter` visibility across the
    # `.qs` boundary. `None` for instances built outside the apply pipeline
    # (they carry no related branches to re-derive).
    _apply_info: object = None

    # Pre-derived nested-branch visibility map. Populated by ``apply_async``
    # via ``_collect_nested_visibility_querysets_async``, which walks every
    # ``and`` / ``or`` / ``not`` arm BEFORE the top-level ``.qs`` read and
    # awaits each branch's target ``get_queryset``. ``_q_for_branch`` then
    # looks up by ``id(child_input)`` instead of calling the sync derive,
    # which would raise ``SyncMisuseError`` mid-``.qs`` if the target type's
    # ``get_queryset`` is async-only. ``None`` for instances built by
    # ``apply_sync`` or outside the apply pipeline (sync path stays sync).
    _nested_qs_by_branch_id: dict[int, dict[str, models.QuerySet[models.Model]]] | None = None

    # The child filter set instances this instance's relation leaves run in at a
    # declared hop's target (a ``ProjectedChildFilter``'s child, a walked leaf's
    # deepest target), one per child class, built on first use by
    # ``_projection_child``. Per instance, so a request never sees another
    # request's child and each ``_q_for_branch`` sibling builds its own.
    _projection_children: dict[type[FilterSet], FilterSet] | None = None

    # Visibility-scoped target rows per declared hop a flat relation leaf walks,
    # keyed by ``(id(<RelatedFilter declaration>), <database alias>)``
    # (``_hop_visible_rows``). One map serves the whole request: a hop's
    # visibility does not depend on which leaf or logical arm walks it, so
    # ``_q_for_branch`` hands this instance's map to every sibling it builds.
    # ``apply_async`` pre-fills it (``_derive_flat_hop_visibility_async``) so an
    # async-only ``get_queryset`` never runs inside the sync ``.qs`` read; the
    # sync path derives each entry on first use. ``None`` until first read
    # (``_hop_visibility``).
    _flat_hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]] | None = (
        None
    )

    # ``ClassBasedTypeNameMixin`` naming suffixes. The root input type keeps
    # the mixin's default ``"InputType"`` (``FooFilter`` -> ``FooFilterInputType``);
    # the per-field operator bag overrides to ``"FilterInputType"``
    # (``FooFilter`` + ``Bar`` -> ``FooFilterBarFilterInputType``), matching the
    # names ``inputs.py`` produced inline before the naming rule was shared.
    _field_type_suffix: str = "FilterInputType"

    # ------------------------------------------------------------------
    # Layer 4 - cycle-safe filter expansion (cookbook port).
    # ------------------------------------------------------------------

    @classmethod
    @override
    def get_filters(cls) -> OrderedDict[str, Filter]:
        """Return declared + Meta-derived + related-expanded filters.

        Direct port of `AdvancedFilterSet.get_filters`. Two reasons the
        guard reads `cls.__dict__` directly instead of `getattr`:

        - A subclass must not inherit its parent's completed
          `_expanded_filters` cache via MRO.
        - The metaclass calls `super().__new__()` before stamping
          `related_filters` onto the new class, and the upstream
          `super().__new__()` call triggers `get_filters()`; the
          `__dict__`-based guard prevents the in-flight class from
          caching a half-built result.

        Single-threaded contract:
            ``_is_expanding_filters`` is a class-level reentrancy
            flag, not a thread-local one. Expansion runs during
            ``finalize_django_types()`` (single-threaded by design)
            and once per class for the lifetime of the registry, so
            the flag's read/write is never contended at runtime.
            Parallel test runs that exercise the same FilterSet class
            from different threads can race on the flag - the second
            thread sees ``_is_expanding_filters=True`` and short-
            circuits to ``super().get_filters()``, yielding the
            unexpanded set. Tests that need to call ``get_filters()``
            from multiple threads must serialize the call themselves;
            do not introduce a ``threading.local`` here without first
            confirming a real consumer call path requires it.
        """
        # Capture ``super().get_filters`` HERE (in the classmethod body, where
        # zero-arg ``super()`` resolves ``cls`` + the ``__class__`` cell) rather
        # than inside ``_build`` / ``on_reentry``: the metaclass calls
        # ``get_filters()`` DURING ``FilterSet``'s own creation, before the module
        # global ``FilterSet`` is bound, so a ``super(FilterSet, cls)`` lookup in a
        # nested function would ``NameError`` (and a zero-arg ``super()`` in a
        # no-arg nested function / lambda has no positional to bind).
        get_base = super().get_filters

        # An abstract model has no default manager, which django-filter reads to resolve
        # every generated lookup (and no primary key for ``get_fields`` to add).
        own_model = cls._meta.model
        if own_model is not None and own_model._meta.abstract:
            raise ConfigurationError(
                f"{cls.__name__}: Meta.model {own_model.__name__} is an abstract model; a "
                f"FilterSet needs a concrete model.",
            )

        def _build() -> OrderedDict[str, Filter]:
            all_filters = get_base()
            model = cls._meta.model
            candidates: dict[str, CandidateFilterMetadata] = {}
            if model is not None:
                # During ``FilterSetMetaclass.__new__``, the new class does not
                # own ``related_filters`` yet. Expanding an inherited map here
                # would leak removed relations into django-filter's class-level
                # ``base_filters`` snapshot.
                # The metaclass stores ``related_filters`` from
                # ``sets_mixins.py::collect_related_declarations`` (``RelatedFilter`` only).
                related_filters_val: Mapping[str, RelatedFilter] = cls.__dict__.get(
                    "related_filters",
                    OrderedDict(),
                )
                for filter_name, f in related_filters_val.items():
                    _require_relation_path(cls, filter_name, f)
                    _require_correlated_target(cls, filter_name, f)
                    expanded = _expand_related_filter(filter_name, f)
                    all_filters.update(expanded)
                # Build candidate metadata in THIS same expansion pass, over the
                # fully-expanded surface. Origin is read from the frozen
                # generation-provenance record stamped on each instance at its
                # construction site (never rediscovered from the prefixed name
                # string); ``_candidate_metadata_for`` returns ``None`` -- so no
                # row is added -- for any non-framework-generated leaf (fail
                # closed) and for every ``RelatedFilter`` expansion, strictly
                # classifies the rest, and RAISES on an unresolvable framework
                # leaf (a genuine framework/configuration defect). A row exists
                # ONLY for a proven direct framework-generated leaf; an absent
                # name is a non-candidate at the fail-closed consumption site.
                #
                # The routing verdict is FROZEN here, once per build, onto
                # ``CandidateFilterMetadata.routable`` -- the only thing
                # ``_apply_flat_leaves`` consults. Two build-wide conjuncts are
                # computed once:
                #
                # * ``cls._is_generation_capable()`` -- this class overrode none of
                #   the package generation seams (``filter_for_field`` /
                #   ``filter_for_lookup`` / ``FILTER_DEFAULTS`` / ``__init__``). A
                #   class that overrode any of them stores every row NON-routable,
                #   so its filters run django-filter's original outer invocation
                #   even for a path-eligible leaf. That is the supported-seam
                #   refusal: the customization keeps working, it just does not
                #   receive the optimization.
                # * ``_DJANGO_FILTER_OPTIMIZER_AUDITED`` -- the installed
                #   ``django-filter`` release is inside the audited optimizer range.
                #   On an unaudited release NOTHING is routable, so filtering falls
                #   back wholesale to upstream behavior with identical results.
                capable = cls._is_generation_capable() and _DJANGO_FILTER_OPTIMIZER_AUDITED
                for filter_name, filter_instance in all_filters.items():
                    row = _candidate_metadata_for(model, filter_instance)
                    if row is None:
                        continue
                    candidates[filter_name] = replace(
                        row,
                        routable=capable and row.eligible,
                    )
            # TODO(spec-060 Slice 1): Meta.search_fields - wire
            # `construct_search(all_filters)` from
            # `django_strawberry_framework.filters.inputs.LOOKUP_PREFIXES` here.
            # The prefix map and `construct_search` landed with spec-027
            # Decision 2; spec-060 owns the consumer surface.

            # The two-condition cache-write gate (own `related_filters` +
            # no unresolved string lazy targets) is single-sited in
            # `sets_mixins.should_cache_expansion`. Publish the
            # filters AND the candidate metadata as ONE immutable snapshot,
            # atomically, only after the whole build succeeded: a failure above
            # (e.g. a strict-classification defect) publishes nothing, so stale
            # metadata can never pair with a rebuilt ``base_filters``.
            if should_cache_expansion(
                cls,
                related_attr="related_filters",
                target_slot="_filterset",
            ):
                cls._expanded_filters = all_filters
                cls._expanded_snapshot = ExpansionSnapshot(
                    # The snapshot exposes a READ-ONLY view of the filter map;
                    # the mutable ``all_filters`` is what django-filter needs on
                    # ``base_filters`` / the ``_expanded_filters`` cache.
                    filters=MappingProxyType(all_filters),
                    candidates=MappingProxyType(candidates),
                )
                cls.base_filters = all_filters
            return all_filters

        # The class-level expansion cache + reentry-guard skeleton is shared with
        # `OrderSet.get_fields` through `sets_mixins.expanded_once`.
        # `on_reentry` returns the unexpanded `super().get_filters()`
        # when this class is already mid-expansion, so a self-referential
        # `RelatedFilter` neither blows the stack nor caches a half-built
        # result.
        return expanded_once(
            cls,
            cache_attr=cls._lifecycle.cache,
            guard_attr=cls._lifecycle.guard,
            build=_build,
            on_reentry=get_base,
        )

    @classmethod
    def _expansion_snapshot(cls) -> ExpansionSnapshot | None:
        """Return this class's OWN published expansion snapshot, or ``None``.

        The fail-closed accessor the flat-leaf applicator consumes. Reads from
        ``cls.__dict__`` DIRECTLY -- never ``getattr`` -- so a subclass never
        inherits a parent's snapshot via MRO (mirroring how ``expanded_once``
        isolates the expansion cache). ``None`` when no snapshot has been
        published on THIS class: a filterset instantiated before its lazy
        ``RelatedFilter`` targets resolve (``should_cache_expansion`` skips the
        cache) presents the unexpanded surface and correctly degrades to
        today's behavior, and the adapter treats any name absent from a present
        snapshot's mapping as a non-candidate.
        """
        return cls.__dict__.get("_expanded_snapshot")

    # basedpyright: typeshed types ``get_fields`` as ``dict[str, Field]``; upstream returns an
    # ``OrderedDict`` of field name to lookup list, the shape this override keeps. It rejects the
    # ``OrderedDict[str, object]`` return for ``dict[str, Field]``
    @classmethod
    @override
    def get_fields(cls) -> OrderedDict[str, object]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Expand per-field ``"__all__"`` and narrow the top-level ``"__all__"`` sweep.

        These are two DISTINCT features that happen to share the ``"__all__"``
        spelling; each acts on a different shape of ``cls._meta.fields`` and
        neither restates the other:

        - **Per-field dict-form ``"__all__"`` expansion** (when ``fields`` is a
          DICT and a single field's VALUE is ``"__all__"``, e.g.
          ``{"name": "__all__"}``): ``django-filter`` expands only the
          top-level ``fields = "__all__"`` and passes a per-field ``"__all__"``
          value through verbatim - which is then mis-read as a literal lookup
          expression. We expand each such value to the field's concrete lookups
          via `_lookups_for_field` (transforms excluded; see that helper). This
          is the cookbook / ``graphene-django``
          ``filter_fields = {"field": "__all__"}`` parity.
        - **Top-level ``"__all__"`` sweep narrowing** (when ``fields`` is the
          STRING ``"__all__"`` itself): ``django-filter`` treats the
          PK as a non-filterable column and includes M2M in the ``"__all__"``
          sweep; the package's preferred shape is the opposite (PK is a
          canonical filter; M2M needs an explicit `RelatedFilter`).

        A third duty gates the declaration SHAPE before any consumption:
        ``FilterSetOptions`` stores ``Meta.fields`` verbatim and upstream
        ``get_fields`` consumes it into a fresh ``OrderedDict`` per call, so a
        one-shot iterator expands correctly ONCE and then silently re-expands
        to an EMPTY field map on every later pass -- exactly the divergence the
        lazy-``RelatedFilter`` re-expansion exists to serve
        (``should_cache_expansion`` refuses the first cache write while a
        string target is unresolved, so ``_build`` re-runs). The re-readability
        contract is shared with the order family's ``_expand_meta_fields``
        through ``sets_mixins.py::require_re_readable_field_declaration``,
        applied here before the first consumption so the declaration fails
        closed at class creation.

        The upstream method is named ``get_fields`` (no underscore prefix);
        we override the same name so `super().get_filters()`'s internal call
        routes through both narrowings.
        """
        meta_fields = getattr(cls._meta, "fields", None)
        if meta_fields is not None and not isinstance(meta_fields, str):
            # ``str`` is exempt here (unlike the order family): the top-level
            # ``"__all__"`` shorthand IS a string declaration, and any other
            # string is upstream's to reject.
            require_re_readable_field_declaration(
                cls,
                meta_fields,
                subject="FilterSet",
                accepted=(
                    "'__all__', a lookup-bag dict, or a re-readable collection of field names"
                ),
            )
        # Upstream's field-name-to-lookups map (see the ``override`` note above).
        fields = cast("OrderedDict[str, object]", super().get_fields())
        model = cls._meta.model

        # Per-field ``"__all__"`` expansion (dict form). Runs before the
        # top-level branch below; the two shapes are mutually exclusive
        # (``meta_fields`` is either the ``"__all__"`` string or a dict).
        if model is not None and isinstance(meta_fields, dict):
            for field_name in list(fields):
                if fields[field_name] == "__all__":
                    model_field = get_model_field(model, field_name)
                    lookups = _lookups_for_field(model_field)
                    if cls._is_own_pk_under_relay_owner(model_field):
                        # A Relay node's own PK is a GlobalID over the wire, so
                        # only equality / membership / null are meaningful.
                        # Ordering and pattern lookups (``range`` / ``gt`` /
                        # ``contains`` / ...) have no GlobalID semantics and are
                        # dropped from the generated surface rather than emitted
                        # as corrupt ``String`` inputs.
                        lookups = [lk for lk in lookups if lk in ("exact", "in", "isnull")]
                    fields[field_name] = lookups

        if meta_fields != "__all__":
            return fields

        if model is None:  # pragma: no cover - unreachable defensive guard.
            # ``super().get_fields()`` above already dereferences
            # ``self._meta.model._meta`` for the ``"__all__"`` shorthand and
            # raises ``AttributeError`` when the model is ``None``; control
            # never reaches this guard for that field shape. Kept as a
            # forward-defensive no-op in case the upstream contract changes.
            return fields

        # ADD the PK if upstream excluded it (typically the auto-id column).
        pk_field = model._meta.pk
        if pk_field.name not in fields:
            fields[pk_field.name] = ["exact"]

        # REMOVE every ManyToManyField from the swept dict.
        m2m_names = {
            f.name for f in model._meta.get_fields() if isinstance(f, models.ManyToManyField)
        }
        for name in list(fields):
            if name in m2m_names:
                del fields[name]

        return fields

    # ------------------------------------------------------------------
    # spec-027 Decision 4 owner-aware Relay-vs-scalar conditional.
    # ------------------------------------------------------------------

    # basedpyright: typeshed types ``filter_for_field`` as never ``None``; upstream returns
    # ``None`` for an unrecognized field under ``WARN`` / ``IGNORE`` (see the first branch below).
    # It rejects the ``None`` arm against the ``Filter`` return
    @classmethod
    @override
    def filter_for_field(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        field: ModelField,
        field_name: str,
        lookup_expr: str | None = None,
    ) -> Filter | None:
        """Pick the Relay-aware filter for Relay-Node-shaped relation targets.

        Decision-4 conditional. Resolves the relation target via
        `_owner_definition.related_target_for(field_name)` (the owner
        binding) and falls back to `registry.get(target_model)`
        when the owner has not been bound yet. A target type implementing
        `relay.Node` produces `GlobalIDMultipleChoiceFilter` for
        multi-valued relations (M2M / reverse FK / reverse M2M) and
        `GlobalIDFilter` for single-valued relations (forward FK /
        OneToOne); a non-Relay target, or a model no `DjangoType` exposes,
        produces the raw-primary-key pair `RelationPkMultipleFilter` /
        `RelationPkFilter` on the same cardinality split. Non-relation
        fields defer to the upstream default unchanged.

        Own-PK branch (spec-027 Decision 4): when ``field`` is the
        owning model's primary key AND the owning ``DjangoType`` itself
        implements ``relay.Node``, the field becomes ``GlobalIDFilter`` -
        the OWNER is the Relay node so its PK column is a GlobalID over
        the wire.

        Generated flat leaves whose ORM path crosses a reverse FK or M2M
        relation are marked ``distinct=True`` before any Relay-aware
        replacement. A fan-out JOIN can otherwise return the same parent
        once per matching child, corrupting list rows and connection counts.
        """
        # basedpyright: typeshed narrows ``field`` to ``Field``; upstream ``get_filters`` passes
        # the ``ForeignObjectRel`` of a reverse relation too. It rejects ``ModelField``'s
        # ``ForeignObjectRel`` arm
        default = super().filter_for_field(
            field,  # pyright: ignore[reportArgumentType]
            field_name,
            lookup_expr,
        )
        # basedpyright: ``None`` for an unrecognized field (see the ``override`` note above), so
        # the comparison is live
        if default is None:  # pyright: ignore[reportUnnecessaryComparison]
            # Upstream's unrecognized-field contract. django-filter's
            # ``filter_for_field`` returns ``None`` for a model field with no
            # ``FILTER_DEFAULTS`` entry (``FileField`` / ``ImageField`` /
            # ``BinaryField`` / ...) whenever ``Meta.unknown_field_behavior``
            # is ``WARN`` or ``IGNORE``; upstream ``get_filters`` then skips
            # the leaf. Every branch below dereferences ``default.distinct`` /
            # ``default.field_name`` / ``default.extra``, so continuing on the
            # ``None`` return crashed with a raw ``AttributeError`` on a field
            # type the package deliberately does not filter -- instead of the
            # graceful skip the supported WARN / IGNORE seams promise. Return
            # the ``None`` verbatim: no filter is generated, so no candidate
            # row exists for the leaf (fail closed, upstream-identical).
            return None
        # Resolve ownership BEFORE mutating the returned instance. ``default``
        # arrives pre-merged with ``Meta.filter_overrides``; a consumer-owned
        # filter must remain byte-for-byte unchanged, including its explicit
        # ``distinct=False`` choice. The framework's row-preserving to-many
        # policy is applied only to a proven ``framework_default`` leaf.
        default_origin = cls._generation_origin_for_field(field, lookup_expr)
        generation_shape_capable = (
            getattr(cls.filter_for_field, "__func__", None)
            is cast("MethodType", FilterSet.filter_for_field).__func__
            and getattr(cls.filter_for_lookup, "__func__", None)
            is cast("MethodType", FilterSet.filter_for_lookup).__func__
        )
        effective_origin = default_origin
        # A consumer ``filter_for_lookup`` override owns the wire shape when
        # this package would otherwise apply its identity conversion (the
        # own-PK GlobalID, or a relation key's GlobalID / raw-pk primitive).
        # Scalar overrides intentionally retain the framework-origin stamp: the
        # class capability gate still refuses optimization, while the candidate
        # row remains available for the fail-closed metadata contract.
        lookup_seam_overridden = (
            getattr(cls.filter_for_lookup, "__func__", None)
            is not cast("MethodType", FilterSet.filter_for_lookup).__func__
        )
        identity_policy_field = cls._is_own_pk_under_relay_owner(field) or getattr(
            field,
            "is_relation",
            False,
        )
        if (
            effective_origin == "framework_default"
            and lookup_seam_overridden
            and identity_policy_field
        ):
            effective_origin = "override_generated"
        framework_added_distinct = (
            # basedpyright: generation runs only for a model-backed set; upstream ``get_filters``
            # returns the declared filters alone when ``Meta.model`` is unset. It rejects the
            # ``None`` arm of ``Meta.model``
            path_traverses_to_many(cls._meta.model, field_name)  # pyright: ignore[reportArgumentType]
            and generation_shape_capable
            and effective_origin == "framework_default"
        )
        requires_distinct = default.distinct or framework_added_distinct
        if framework_added_distinct or effective_origin == "framework_default":
            default.distinct = requires_distinct

        def _stamp(instance: object, origin: FilterOrigin) -> None:
            # Every generation site on this method stamps the SAME
            # ``framework_added_distinct`` bit (fixed for this (field, lookup) pair);
            # only ``origin`` and the target instance vary. A single closure removes the
            # copy-paste so a future branch cannot stamp an inconsistent bit onto a
            # replacement instance.
            _stamp_generation_provenance(
                instance,
                FilterGenerationProvenance(
                    origin=origin,
                    framework_added_distinct=framework_added_distinct,
                ),
            )

        _stamp(default, effective_origin)
        if not generation_shape_capable or effective_origin != "framework_default":
            return default
        if cls._is_own_pk_under_relay_owner(field):
            # The owner's own PK is a GlobalID over the wire. Honor the
            # lookup cardinality: an ``in`` lookup consumes a LIST of
            # GlobalIDs (multi-choice), every other lookup a single one.
            # Without this split ``id: {in: [...]}`` collapsed to a single
            # ``GlobalIDFilter`` and silently dropped to a scalar input.
            # ``isnull`` is a Boolean predicate, not a GlobalID, so pass the
            # upstream filter through unchanged.
            if default.lookup_expr == "isnull":
                return default
            own_pk_filter_class = (
                GlobalIDMultipleChoiceFilter if default.lookup_expr == "in" else GlobalIDFilter
            )
            # ``**default.extra`` is safe to forward even to
            # ``GlobalIDMultipleChoiceFilter``: ``default`` is the upstream
            # SCALAR filter for the PK column (a NumberFilter-shaped default),
            # so ``.extra`` carries no ``queryset=`` and no incompatible
            # ``ModelChoiceField`` kwargs. ``GlobalIDMultipleChoiceFilter``
            # backs onto ``_GlobalIDMultipleChoiceField`` (a plain
            # ``MultipleChoiceField``, NOT a model-backed field), which needs
            # no ``queryset`` and accepts an empty ``choices`` set, so the
            # forwarded extras can never leave it under-configured.
            own_pk_replacement = own_pk_filter_class(
                field_name=default.field_name,
                lookup_expr=default.lookup_expr,
                distinct=requires_distinct,
                **default.extra,
            )
            _stamp(own_pk_replacement, "package_replacement")
            return own_pk_replacement
        if not getattr(field, "is_relation", False) or not isinstance(
            default,
            _RELATION_IDENTITY_FILTER_CLASSES,
        ):
            # A non-relation leaf, or a relation null test: ``filter_for_lookup``
            # kept the upstream ``BooleanField`` default for ``isnull``, mirroring the
            # own-PK ``isnull`` pass-through above, so ``default`` is correctly shaped
            # and already stamped ``framework_default``. No ``__pk`` marker applies --
            # a Boolean never reads it. The Boolean leaf stays eligible for the
            # correlated-``EXISTS`` adapter exactly like any to-many ``isnull`` (the
            # adapter compiles the null semantics inside the pk-correlated inner root,
            # row-preservingly).
            return default
        # Preserve the lookup-aware class ``filter_for_lookup`` already chose rather
        # than independently reselecting by cardinality.
        # ``super().filter_for_field`` builds ``default`` from the class OUR
        # ``filter_for_lookup`` returned for this (field, lookup) pair, so
        # ``type(default)`` is already the correct identity primitive: the
        # list-shaped class for an ``in`` lookup (a forward FK ``in`` is list-shaped
        # over the wire) and the cardinality-selected class for every other lookup,
        # a GlobalID one for a Relay-node target and a raw-pk one otherwise.
        # Re-selecting by cardinality alone dropped a forward-FK ``in`` back to the
        # scalar class and rejected the list.
        # basedpyright: ``default.extra`` holds the constructor kwargs upstream built ``default``
        # from, forwarded verbatim; it rejects ``object`` kwargs for typed ``Filter`` params
        identity_replacement = type(default)(
            field_name=default.field_name,
            lookup_expr=default.lookup_expr,
            distinct=requires_distinct,
            **_strip_model_choice_extras(default.extra),  # pyright: ignore[reportArgumentType]
        )
        _stamp(identity_replacement, "package_replacement")
        # A forward relation whose link targets NON-pk columns (a ``to_field``
        # FK/O2O, a ``ForeignObject`` off the pk) stores and joins on those columns,
        # but a Relay GlobalID and a raw-pk leaf both carry the target's PK. Set the
        # BOOLEAN pk-qualification flag so the filter DERIVES the
        # ``<relation>__pk`` path from its LIVE ``field_name`` at filter time (see
        # ``base.py::_relation_uses_non_pk_to_field`` / ``_GLOBALID_RELATION_PK_ATTR``).
        # A boolean (not a frozen absolute path) survives ``_expand_related_filter``'s
        # deepcopy + ``field_name`` rebase, so an expanded leaf compiles against the
        # rebased relation path instead of a stale absolute ``"<relation>__pk"``. The
        # common FK-to-pk / M2M / reverse case is not marked and keeps the raw
        # ``{field_name__lookup_expr: node_id}`` predicate byte-identical.
        if _relation_uses_non_pk_to_field(field):
            setattr(identity_replacement, _GLOBALID_RELATION_PK_ATTR, True)
        return identity_replacement

    @classmethod
    def _generation_origin_for_field(
        cls,
        field: ModelField,
        lookup_expr: str | None,
    ) -> FilterOrigin:
        """Return ``override_generated`` vs ``framework_default`` for a generated leaf.

        Keyed on the RESOLVED output field -- the SAME field django-filter's
        ``BaseFilterSet.filter_for_lookup`` selects the filter class off -- so the
        origin oracle cannot drift from the actual selection. django-filter first
        resolves the lookup's transforms + terminal lookup via ``resolve_field``,
        then walks the resolved field class's MRO against
        ``FILTER_DEFAULTS`` merged with ``cls._meta.filter_overrides``; for an
        ``isnull`` lookup it SWAPS the selection field to ``models.BooleanField``.
        This method mirrors that exact resolution:

        1. ``resolve_field(field, lookup_expr or "exact")`` (matching upstream's
           ``DEFAULT_LOOKUP_EXPR`` fallback). An invalid lookup raises
           ``FieldLookupError`` upstream before any filter is generated, so a leaf
           that fails resolution was never generated and could never be an
           eligible candidate; it fails closed to ``override_generated`` (an
           unresolvable lookup was never generated, so it must not be treated as
           an eligible framework leaf).
        2. The selection class is the resolved output field's class -- except for
           ``isnull``, which upstream re-selects against ``models.BooleanField``.
        3. Select the ``FILTER_DEFAULTS``-plus-``filter_overrides`` entry EXACTLY as
           ``super().filter_for_lookup`` does -- one ``try_dbfield`` MRO walk over
           ``dict(cls.FILTER_DEFAULTS)`` updated with ``cls._meta.filter_overrides``
           (merge order preserved, so a more-derived ``FILTER_DEFAULTS`` entry shadows
           a less-derived override) -- then NORMALIZE that selected entry
           (``_normalize_policy_entry``) and compare it BY VALUE against the normalized
           ``_PACKAGE_POLICY_BASELINE`` selection: the PRIVATE, immutable, package-owned
           baseline derived from ``_PUBLIC_PACKAGE_FILTER_DEFAULTS``, NOT django-filter's
           mutable, shared ``BaseFilterSet.FILTER_DEFAULTS`` and NOT the public table's
           object identity. The public table and the
           private baseline are DISTINCT object graphs, so object identity could never
           hold between a selected raw entry and a baseline record; the ownership anchor
           is a normalized VALUE comparison of the ownership-bearing members
           (``filter_class`` + the ``extra`` provider identity). A pristine selection
           re-derives the SAME (filter_class, provider) pair the baseline holds, so it is
           ``framework_default``; a consumer seam that genuinely governs the selection --
           a ``Meta.filter_overrides`` entry that wins the merged walk OR a class-level
           ``FILTER_DEFAULTS`` shadow that replaced the entry -- carries a different
           ``filter_class`` and/or a different (consumer) ``extra`` provider, so its
           normalized value diverges and it is ``override_generated``. Whole-entry
           normalization catches an ``extra``-only override (restricted queryset,
           ``to_field_name``, requiredness), not just a ``filter_class`` change. This is
           import-order-immune: the baseline derives from OUR table, so a consumer
           mutation of django-filter's global before this module was imported cannot
           taint it.

        This is the SINGLE ownership oracle both ``filter_for_lookup`` (which
        decides whether to convert a Relay-node relation to a package GlobalID
        primitive) and ``filter_for_field`` (which reads the resulting stamp) route
        through, so a consumer-selected relation override is never independently
        rediscovered or silently reclassified. Resolving on the
        output field (not the unresolved model field) also handles ``isnull``: a
        leaf whose model field is e.g. a ``TextField`` is selected by a
        ``BooleanField`` override upstream, and this oracle agrees.
        """
        try:
            # basedpyright: typeshed narrows ``field`` to ``Field``; upstream resolves a
            # ``ForeignObjectRel`` the same way. It rejects the ``ForeignObjectRel`` arm
            resolved_field, lookup_type = resolve_field(
                field,  # pyright: ignore[reportArgumentType]
                lookup_expr or "exact",
            )
        except FieldLookupError:
            return "override_generated"
        selection_cls = models.BooleanField if lookup_type == "isnull" else type(resolved_field)
        # Replicate django-filter's EXACT class selection so the oracle cannot drift
        # from it in EITHER direction. ``BaseFilterSet.filter_for_lookup`` builds
        # ``DEFAULTS = dict(cls.FILTER_DEFAULTS)``, then ``DEFAULTS.update(
        # cls._meta.filter_overrides)``, then runs ONE ``try_dbfield`` MRO walk over the
        # MERGED map for the selection class. Merge order is load-bearing: because the
        # walk returns the FIRST (most-derived) class on the MRO present in the map, a
        # more-derived entry contributed by ``FILTER_DEFAULTS`` SHADOWS a less-derived
        # ``filter_overrides`` entry -- e.g. a ``OneToOneField`` selection keeps the
        # base ``OneToOneField`` default even when ``filter_overrides`` supplies a
        # ``ForeignKey`` entry, since ``OneToOneField`` is nearer on the MRO than its
        # ``ForeignKey`` base. Walking ``filter_overrides`` ALONE would mis-select
        # that shadowed override and mis-classify the leaf
        # ``override_generated`` -- declining a legitimate Relay conversion (wire-shape
        # regression) and dropping a genuine framework leaf from routing (false-closed).
        #
        # Comparing the merged SELECTION by NORMALIZED VALUE against the private,
        # package-owned ``_PACKAGE_POLICY_BASELINE`` selection subsumes BOTH
        # consumer-selection seams in one check:
        #   * ``Meta.filter_overrides`` -- when an override entry ACTUALLY governs the
        #     selection class (upstream would select it), the merged walk returns that
        #     override entry; its normalized (filter_class, extra) pair differs from the
        #     baseline record -> ``override_generated``.
        #   * a class-level ``FILTER_DEFAULTS`` shadow -- a subclass
        #     that reassigns ``FILTER_DEFAULTS`` changes the whole generation policy; its
        #     REPLACED entry normalizes to a different value -> ``override_generated``,
        #     while an untouched shallow ``{**FilterSet.FILTER_DEFAULTS, Field: {...}}``
        #     copy carries the SAME (filter_class, provider) pair for every unchanged
        #     class, so those normalize equal to the baseline and stay
        #     ``framework_default``.
        # The baseline is derived from the package's OWN ``_PUBLIC_PACKAGE_FILTER_DEFAULTS``
        # table (never from django-filter's mutable global), and the comparison is by
        # VALUE, so import order cannot taint it and the public table and baseline being
        # distinct object graphs does not matter: a pristine selection re-derives
        # the baseline's (filter_class, provider) pair. The compared members are the
        # single ownership-bearing values django-filter selects (its ``filter_class`` AND
        # its ``extra`` provider -- a restricted relation queryset, a ``to_field_name``,
        # requiredness), so an ``extra``-only override is caught, not just a
        # ``filter_class`` change.
        overrides = getattr(cls._meta, "filter_overrides", None)
        merged_defaults = dict(cls.FILTER_DEFAULTS)
        if overrides:
            merged_defaults.update(overrides)
        # ``try_dbfield`` returns the first non-empty ``fn(cls)`` result or None, so each read
        # is one of its mapping's values.
        selected_entry: Mapping[str, object] | None
        base_norm: _NormalizedPolicyEntry | None
        # basedpyright: typeshed types ``try_dbfield``'s ``fn`` as taking a field instance;
        # upstream calls it with each CLASS on ``field_class``'s MRO. It rejects a class-keyed
        # ``dict.get`` as ``fn`` in both calls
        selected_entry = try_dbfield(merged_defaults.get, selection_cls)  # pyright: ignore[reportArgumentType]
        selected_norm = _normalize_policy_entry(selected_entry)
        base_norm = try_dbfield(_PACKAGE_POLICY_BASELINE.get, selection_cls)  # pyright: ignore[reportArgumentType]
        if selected_norm != base_norm:
            return "override_generated"
        return "framework_default"

    @classmethod
    def _is_generation_capable(cls) -> bool:
        """Return True iff this class has NOT overridden the package generation seams.

        The class-level half of the fail-closed routing verdict
        (``CandidateFilterMetadata.routable``): a leaf is routable ONLY when the class
        that built it is proven to generate filters through the package's own,
        unmodified machinery. Each check closes one DOCUMENTED django-filter
        customization seam through which a consumer could otherwise route its own
        filter semantics into the correlated ``EXISTS`` adapter. A class that trips
        any of them keeps working exactly as authored -- its filters simply run
        django-filter's original outer invocation instead of being rewritten:

        * ``filter_for_field`` override -- the ``super()``-and-mutate seam: a
          consumer subclass that calls ``super().filter_for_field(...)`` and then
          mutates the framework-stamped instance would keep the stamp; comparing
          the underlying function identity against ``FilterSet.filter_for_field``
          rejects any such subclass wholesale.
        * ``filter_for_lookup`` override -- the custom-generated-class seam: a
          consumer returning its OWN generated filter class from
          ``filter_for_lookup`` (before the package wrapper stamps it) is not
          package-generated.
        * ``FILTER_DEFAULTS`` override -- the class-level generation hook: a
          consumer shadowing ``FILTER_DEFAULTS`` changes which filter classes the
          default path selects; an unmodified subclass inherits the package-authored
          public ``_PUBLIC_PACKAGE_FILTER_DEFAULTS`` table by identity, so any class
          that reassigned ``FILTER_DEFAULTS`` is non-capable and
          nothing it generates is routable. Comparing against the package-authored
          public table (not django-filter's mutable ``BaseFilterSet.FILTER_DEFAULTS``,
          and not a snapshot of it) means capability tracks whether the class still
          uses the exact table this module authored. Value-level ownership of an
          individual entry is a separate concern handled by
          ``_generation_origin_for_field`` against the private normalized baseline;
          this identity check is the coarse whole-table-replacement gate.
        * ``__init__`` override (``_customizes_instances``) -- the standard place a
          consumer replaces or mutates ``self.filters`` per request. A subclass that
          defines its own ``__init__`` can swap a generated leaf for its own filter
          object AFTER the per-request deepcopy. Since routing is decided at BUILD
          time, this seam is closed at build: such a class is non-capable, so none of
          its leaves is routable and the swapped-in filter runs on the outer queryset.

        ``FilterSet`` is referenced by name (not ``super()`` / ``__class__``)
        because this runs after class definition, when the module global is
        bound. ``filterset`` is the imported ``django_filters.filterset``.
        """
        return (
            getattr(cls.filter_for_field, "__func__", None)
            is cast("MethodType", FilterSet.filter_for_field).__func__
            and getattr(cls.filter_for_lookup, "__func__", None)
            is cast("MethodType", FilterSet.filter_for_lookup).__func__
            and cls.FILTER_DEFAULTS is _PUBLIC_PACKAGE_FILTER_DEFAULTS
            and not cls._customizes_instances()
        )

    def _projection_child(self, filterset_cls: type[FilterSet]) -> FilterSet:
        """Return the ``filterset_cls`` instance this instance's relation leaves run in.

        Built on first use and shared by every projected leaf of this instance
        expanded from ``filterset_cls`` and every walked leaf whose deepest hop
        targets it: django-filter's form reads every projected filter's
        ``.field``, so a per-leaf child would deep-copy the child's filters and
        rerun its ``__init__`` once per leaf per request. The child is unbound
        (no form data; only its filters run), seeded with the child model's base
        rows on this instance's database (an active leaf runs over the hop's
        visible rows instead; ``_apply_relation_leaf``), and carries this
        instance's request, so a request-aware
        callable ``queryset`` and the child ``__init__`` see the same request the
        parent does.
        """
        children = self._projection_children
        if children is None:
            children = self._projection_children = {}
        child = children.get(filterset_cls)
        if child is None:
            # A ``RelatedFilter`` target always declares ``Meta.model``
            # (``_iter_visibility_steps`` trusts the same).
            child_model = cast("type[models.Model]", filterset_cls._meta.model)
            # Never ``None`` on an instance (see ``ProjectedChildFilter.filter``).
            parent_qs = cast("models.QuerySet[models.Model]", self.queryset)
            child = filterset_cls(
                queryset=base_queryset(child_model, using=parent_qs.db),
                request=self.request,
            )
            children[filterset_cls] = child
        return child

    @classmethod
    def _customizes_instances(cls) -> bool:
        """Return True iff this class overrides ``__init__``, the per-request edit seam.

        ``BaseFilterSet.__init__`` deep-copies ``base_filters`` into ``self.filters``;
        a subclass ``__init__`` is where a consumer replaces or mutates those
        instances (a validator appended to one filter's form field, a filter
        swapped for another). The class-level filters therefore do not describe
        what such a class's instances run, which is why the optimizer declines
        to route its leaves (``_is_generation_capable``) and why
        ``_expand_related_filter`` projects them through a child instance rather
        than rebinding a copy (``_owner_bound_child``). ``__init__`` is compared
        by identity: an unmodified subclass inherits ``FilterSet.__init__``
        (``FilterSet`` defines none, so this is ``filterset.BaseFilterSet.__init__``).
        """
        return cls.__init__ is not FilterSet.__init__

    # basedpyright: typeshed types ``filter_for_lookup``'s class as never ``None``; upstream
    # returns ``(None, {})`` for a field with no ``FILTER_DEFAULTS`` entry. It rejects the ``None``
    # class arm against ``type[Filter]``
    @classmethod
    @override
    def filter_for_lookup(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        field: ModelField,
        lookup_type: str,
    ) -> tuple[type[Filter] | None, dict[str, object]]:
        """Mirror `filter_for_field`'s Relay-vs-scalar conditional per-lookup.

        Non-relation fields defer to the upstream pair-return shape unless
        the field is the owner's own PK and the owner is Relay-Node-shaped
        (own-PK branch per spec-027 Decision 4). For relation fields a
        Relay-Node-shaped target maps to a ``(GlobalIDFilter, params)``
        pair (or ``GlobalIDMultipleChoiceFilter`` for multi-valued
        relations); a non-Relay target, or a model no ``DjangoType``
        exposes, maps to the raw-primary-key pair (``RelationPkFilter`` /
        ``RelationPkMultipleFilter``) on the same split.

        Ownership is decided FIRST: a consumer-selected relation override
        (``Meta.filter_overrides`` or a shadowed ``FILTER_DEFAULTS``) is
        returned unchanged and is NEVER subject to the wire-shape policy --
        its class may intentionally implement a nonstandard lookup. The
        exhaustive lookup classification below applies ONLY to a PROVEN
        framework default (``_generation_origin_for_field(...) ==
        "framework_default"``)::

            exact  -> scalar / list identity class by cardinality
            in     -> list identity class (a list of GlobalIDs or primary keys)
            isnull -> upstream BooleanFilter (a null test is never an identity)
            other  -> ConfigurationError at generation time

        An identity carries no ordering / pattern / range semantics, so any
        lookup outside ``{exact, in, isnull}`` on a framework-owned relation
        key is a corrupt wire shape rejected here at build time -- never
        a resolver-time Django ``FieldError`` -- mirroring the own-PK branch
        above. Raising in this classmethod also covers
        ``filter_for_field``: ``super().filter_for_field`` calls
        ``cls.filter_for_lookup``, so the raise propagates before any leaf is
        built.
        """
        # basedpyright: typeshed narrows ``field`` to ``Field`` (see ``filter_for_field``); it
        # rejects ``ModelField``'s ``ForeignObjectRel`` arm
        default_class, params = super().filter_for_lookup(
            field,  # pyright: ignore[reportArgumentType]
            lookup_type,
        )
        if cls._is_own_pk_under_relay_owner(field):
            if cls._generation_origin_for_field(field, lookup_type) != "framework_default":
                return default_class, params
            # Own-PK GlobalID. A Relay node's wire id supports only equality
            # (``exact`` -> a single GlobalID), membership (``in`` -> a list of
            # GlobalIDs), and null (``isnull`` -> the upstream Boolean; a
            # GlobalID cannot represent ``true``). Any other lookup has no
            # GlobalID ordering / pattern semantics. This guard is
            # authoritative once the owner is bound (finalizer phase 2.5):
            # ``_is_own_pk_under_relay_owner`` keys off ``cls._owner_definition``,
            # which is ``None`` during class creation, so the check is inert
            # then and becomes authoritative at finalize (not only the
            # ``get_fields`` ``"__all__"`` narrowing). An explicit
            # ``Meta.fields`` list that names an unsupported lookup is rejected
            # here so it cannot silently generate a corrupt GlobalID-shaped
            # input.
            if lookup_type == "in":
                return GlobalIDMultipleChoiceFilter, params
            if lookup_type == "isnull":
                return default_class, params
            if lookup_type == "exact":
                return GlobalIDFilter, params
            field_name = getattr(field, "name", "<pk>")
            raise ConfigurationError(
                f"{cls.__name__}: lookup {lookup_type!r} is not supported on the "
                f"Relay node's own primary key {field_name!r}; a GlobalID supports "
                "only 'exact', 'in', and 'isnull'. Remove it from Meta.fields.",
            )
        if not field.is_relation:
            if lookup_type == "in" and isinstance(field, models.IntegerField):
                # An element-binding integer ``__in`` routes through IntegerInFilter:
                # it drops out-of-range members (an out-of-range value overflows the
                # backend at bind) and matches NOTHING when a non-empty list fully
                # drops, instead of django-filter's empty-value skip that would widen
                # a restrictive ``in`` to no constraint. Own-PK Relay ``in``
                # is handled above (GlobalIDMultipleChoiceFilter); a non-integer column
                # carries no binding-range limit so it keeps the upstream filter.
                return IntegerInFilter, params
            if lookup_type == "range" and isinstance(field, models.IntegerField):
                # A bound-binding integer ``__range`` routes through IntegerRangeFilter:
                # a raw ``BETWEEN a AND b`` binds BOTH bounds directly, so an out-of-range
                # bound overflows the backend at bind exactly as an ``__in`` member does.
                # The reroute decomposes the range into Django's range-aware ``gte`` /
                # ``lte`` lookups (which resolve an out-of-range bound before binding), so
                # a 64-bit ``BigInt`` bound past the column range never reaches the backend
                # as a raw ``OverflowError``. Sibling of the ``in`` reroute above.
                return IntegerRangeFilter, params
            return default_class, params
        # Resolve OWNERSHIP before any identity transformation. A consumer that
        # selected its OWN relation filter -- via ``Meta.filter_overrides`` or a
        # shadowed class-level ``FILTER_DEFAULTS`` -- owns the wire shape under the
        # plan's byte-for-byte rule; the framework must NOT silently replace that
        # selection with a package primitive. ``super().filter_for_lookup`` already
        # returned the consumer's class in ``default_class``, so returning it
        # unchanged both preserves the consumer's filter AND keeps the leaf
        # consumer-origin (the ``_generation_origin_for_field`` oracle stamps
        # ``override_generated`` on ``filter_for_field``'s ``default``, so it is
        # ineligible). Only the proven framework default is converted below.
        if cls._generation_origin_for_field(field, lookup_type) != "framework_default":
            return default_class, params
        if lookup_type == "isnull":
            # A null test is a Boolean predicate, never an identity, regardless of
            # relation cardinality. ``super().filter_for_lookup`` already selected the
            # ``BooleanField`` default for ``isnull``; converting it would emit an
            # identity-shaped input for a null test (a LIST input on the multi-valued
            # side) that raises at bind. Mirror the own-PK ``isnull`` pass-through;
            # the branches below convert only the equality (``exact``) and membership
            # (``in``) wire shapes.
            return default_class, params
        # The identity a relation key filters by: a GlobalID when the owner-aware
        # target type is a Relay node, otherwise the raw target primary key. The raw
        # pair also covers a target model no ``DjangoType`` exposes, and replaces
        # django-filter's model-choice default, whose ``ModelChoiceField`` would
        # validate existence against the target's default manager (an existence
        # oracle for rows ``get_queryset`` hides) and has no GraphQL input shape.
        target_type = cls._resolve_relation_target_type(field, getattr(field, "name", None))
        relay_target = target_type is not None and implements_relay_node(target_type)
        many_side = is_many_side_relation_kind(relation_kind(field))
        if lookup_type == "in":
            # A relation ``in`` lookup consumes a LIST of identities, so it keeps the
            # list-shaped primitive regardless of relation cardinality -- a forward,
            # single-valued FK ``in`` is still list-shaped over the wire. This mirrors
            # the own-PK ``in`` branch above; a cardinality-only reselection dropped a
            # forward-FK ``in`` back to the scalar class and rejected the list.
            list_class = GlobalIDMultipleChoiceFilter if relay_target else RelationPkMultipleFilter
            return list_class, _strip_model_choice_extras(params)
        if lookup_type == "exact":
            # Equality on one identity, cardinality-selected: the scalar class for a
            # forward FK / O2O / reverse O2O, the list class for a many-side relation.
            if relay_target:
                return cls._relay_filter_class_for_field(field), _strip_model_choice_extras(params)
            pk_class = RelationPkMultipleFilter if many_side else RelationPkFilter
            return pk_class, _strip_model_choice_extras(params)
        # Exhaustive classification: a PROVEN framework-default relation key
        # supports ONLY ``exact`` / ``in`` / ``isnull`` (handled above). Any other
        # lookup -- pattern (``icontains``), ordering (``gt`` / ``lt``), range --
        # has no identity semantics, so converting it emits an input that fails only
        # when the query executes (a Django ``FieldError`` such as "Unsupported
        # lookup 'icontains' for ForeignKey"). Reject it here at generation time,
        # mirroring the own-PK branch above. This also fails ``filter_for_field``
        # closed: ``super().filter_for_field`` calls this classmethod, so the raise
        # propagates before a corrupt leaf is built.
        field_name = getattr(field, "name", "<relation>")
        identity = "a GlobalID" if relay_target else "the related row's primary key"
        raise ConfigurationError(
            f"{cls.__name__}: lookup {lookup_type!r} is not supported on the "
            f"relation key {field_name!r} in Meta.fields; a relation key filters by "
            f"{identity} and supports only 'exact', 'in', and 'isnull'. Filter on the "
            "related row's own fields through a RelatedFilter instead.",
        )

    @classmethod
    def _is_own_pk_under_relay_owner(cls, field: object) -> bool:
        """Return True iff ``field`` is the owning model's PK and owner is Relay.

        Own-PK branch per spec-027 Decision 4: when a ``FilterSet``
        whose owning ``DjangoType`` implements ``relay.Node`` filters on
        its own primary key, the wire shape is a Relay GlobalID - so the
        filter for that PK is ``GlobalIDFilter`` rather than the scalar
        upstream default. Resolves only when ``_owner_definition`` is
        bound (finalizer phase-2.5 binding) so package-internal tests
        that run pre-binding keep the upstream shape.
        """
        owner = cls._owner_definition
        if owner is None:
            return False
        if getattr(field, "is_relation", False):
            return False
        # django-filter's metaclass stores ``_meta = FilterSetOptions(...)`` on every filterset.
        meta: FilterSetOptions | None = getattr(cls, "_meta", None)
        model: type[models.Model] | None = getattr(meta, "model", None)
        if model is None:
            return False
        pk = getattr(model._meta, "pk", None)
        if pk is None or field is not pk:
            return False
        # ``DjangoTypeDefinition.origin`` is the registered ``DjangoType`` class.
        owner_type: type[DjangoType] | None = getattr(owner, "origin", None)
        return owner_type is not None and implements_relay_node(owner_type)

    @staticmethod
    def _relay_filter_class_for_field(
        field: ModelField,
    ) -> type[GlobalIDFilter] | type[GlobalIDMultipleChoiceFilter]:
        """Pick the Relay-aware filter class matching the relation cardinality.

        Multi-valued relations (`ManyToManyField`, reverse FK
        `ManyToOneRel`, reverse M2M `ManyToManyRel`) - every Django
        relation field that sets `many_to_many=True` or `one_to_many=True`
        - map to `GlobalIDMultipleChoiceFilter`; single-valued relations
        (forward `ForeignKey` / `OneToOneField` and reverse `OneToOneRel`)
        map to `GlobalIDFilter`. This mirrors `django-filter`'s upstream
        choice between `ModelChoiceFilter` and `ModelMultipleChoiceFilter`
        and matches Decision 4's parity-floor split between the two
        Relay-aware primitives.

        The many-side test is the shared cardinality classifier in
        ``utils/relations.py`` (``is_many_side_relation_kind(relation_kind(field))``),
        the same call the optimizer walker, the order set family, and the
        relation resolvers route through, so the "rendered as a GraphQL list"
        decision cannot drift between the filter family and its siblings.
        """
        if is_many_side_relation_kind(relation_kind(field)):
            return GlobalIDMultipleChoiceFilter
        return GlobalIDFilter

    @classmethod
    def _resolve_relation_target_type(
        cls,
        field: object,
        field_name: str | None,
    ) -> type[DjangoType] | None:
        """Look up the registered target `DjangoType` for a relation field.

        Consults `_owner_definition.related_target_for(...)` when the
        finalizer phase-2.5 binding has landed; otherwise falls back to
        `registry.get(field.related_model)`. The caller
        (`filter_for_lookup`) passes relation fields only; a field with no
        `related_model` resolves to `None`.
        """
        owner = cls._owner_definition
        if owner is not None and field_name is not None:
            # Owner-aware path (finalizer phase-2.5 binding has landed): resolve
            # the target `DjangoType` through `owner.related_target_for(...)`.
            # The pair's first member is a `DjangoTypeDefinition`, whose
            # registered `DjangoType` class is its `.origin` attribute --
            # NOT `.type` / `.type_cls`, which the definition never
            # exposes (a stale read there silently returned `None` and
            # dropped every owner-aware resolution to the registry
            # fallback). Mirrors `_is_own_pk_under_relay_owner` /
            # `_target_type_for_related_filter`, which both read `.origin`.
            resolved: Callable[[object], tuple[DjangoTypeDefinition, ModelField] | None] | None
            resolved = getattr(owner, "related_target_for", None)
            if callable(resolved):
                pair = resolved(field_name)
                if pair is not None:
                    target_definition, _ = pair
                    return getattr(target_definition, "origin", None)
        related_model = getattr(field, "related_model", None)
        if related_model is None:
            return None
        # ``registry.get`` owns the primary-first precedence (its first
        # return state IS the declared primary; the lone-type fallback is
        # the common shape today) - do not re-derive it by composing
        # ``primary_for`` / ``get`` here.
        return registry.get(related_model)

    # ------------------------------------------------------------------
    # spec-027 Decision 8 apply pipeline.
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_input_items(input_value: object) -> list[tuple[str, object]] | None:
        """Walk a dict or Strawberry-input dataclass into ``(name, value)`` pairs.

        Thin delegate to ``utils/input_values.py::iter_input_items`` (the
        package owner; ``utils/permissions.py`` re-exports the same symbol for
        historical import paths). Returns ``None`` for an input that is neither
        a dict nor a Strawberry-input dataclass, ``[]`` for a walkable-but-empty
        input.
        """
        return iter_input_items(input_value)

    @classmethod
    def _iter_logic_branches(
        cls,
        input_value: object,
    ) -> Iterator[tuple[LogicOperatorDescriptor, list[object]]]:
        """Iterate active logical branches and their child filter-input elements.

        Single authoritative iterator for all runtime logical-tree traversals
        (async visibility derive, permission recursion, and query Q composition).
        For each operator in ``LOGIC_OPERATORS``:
        - Extracts the branch value across Python attribute and wire key names.
        - Validates container and element shapes fail-closed.
        - Filters inactive (``None`` / ``UNSET``) elements.
        - Yields ``(operator, active_children)`` for non-empty branches.
        """
        if is_inactive_value(input_value, unset_sentinel=UNSET):
            return
        for op in LOGIC_OPERATORS:
            branch_value = cls._extract_branch_value(input_value, op.python_attr)
            if branch_value is None:
                branch_value = cls._extract_branch_value(input_value, op.wire_name)
            if branch_value is None or is_inactive_value(branch_value, unset_sentinel=UNSET):
                continue
            cls._validate_logic_branch_shape(op.wire_name, branch_value)
            if op.is_sequence:
                # ``_validate_logic_branch_shape`` refused anything but a list or tuple
                # for a sequence operator.
                elements = cast("list[object] | tuple[object, ...]", branch_value)
                children = [
                    child
                    for child in elements
                    if not is_inactive_value(child, unset_sentinel=UNSET)
                ]
            else:
                children = (
                    [branch_value]
                    if not is_inactive_value(branch_value, unset_sentinel=UNSET)
                    else []
                )
            if children:
                yield op, children

    @classmethod
    def _validate_logic_branch_shape(cls, wire_key: str, value: object) -> None:
        """Reject a malformed logical container before it silently no-ops.

        Sequence operators (``and`` / ``or``) carry a LIST of filter inputs;
        single-element operators (``not``) carry a SINGLE filter input. GraphQL
        input coercion guarantees these shapes, but the public ``apply_sync`` /
        ``apply_async`` raw-dict API accepts anything a consumer hands it. Two
        malformations are rejected:

        * **Wrong CONTAINER.** A mapping supplied where a list is expected --
          ``{"or": {"name": {"exact": "x"}}}`` -- would otherwise be iterated
          as its string KEYS: the nested clause is never seen, so its
          ``check_*`` gate never fires AND its predicate is dropped, silently
          widening the branch to an identity query.
        * **Wrong ELEMENT.** ``not: "name"``, ``or: ["name"]``, ``and: [42]`` --
          a scalar where a filter input belongs. ``_q_for_branch`` normalizes
          each element through ``iter_input_items``, which returns ``None`` for
          a non-mapping / non-dataclass; the branch then contributes an empty
          ``Q()`` (match-all under ``not``) and, critically, ``check_*`` gates
          never traverse into it -- the SAME permission + filter bypass one
          level down.

        Both are a permission + filter bypass, so fail loud with a typed
        ``ConfigurationError`` instead. A filter input is a mapping or a
        Strawberry-input dataclass -- exactly ``iter_input_items(x) is not None``.

        An inactive value (``None`` / ``UNSET``) is a no-op branch everywhere it
        is read (``tree_data.get(key) or []`` / ``if not_branch is not None``, and
        the per-element inactive skip in ``_evaluate_logic_tree``), so it is
        accepted here -- both as the whole branch value and as a list element --
        rather than treated as a shape error.
        """
        if is_inactive_value(value, unset_sentinel=UNSET):
            return
        op = LOGIC_OPERATORS_BY_WIRE.get(wire_key)
        is_sequence = isinstance(value, (list, tuple))
        if op is not None and not op.is_sequence:
            if is_sequence:
                raise ConfigurationError(
                    f"FilterSet {cls.__qualname__}: logical branch {wire_key!r} takes a "
                    f"single filter input, got a {type(value).__name__}. Wrap the "
                    f"clause as '{wire_key}: {{...}}', not a list.",
                )
            cls._validate_logic_element_shape(wire_key, value)
            return
        if not is_sequence:
            raise ConfigurationError(
                f"FilterSet {cls.__qualname__}: logical branch {wire_key!r} takes a "
                f"list of filter inputs, got a {type(value).__name__}. Wrap the "
                f"clauses as '{wire_key}: [{{...}}]'.",
            )
        # basedpyright: ``is_sequence`` held, but the aliased ``isinstance`` narrows ``value`` only
        # to ``list[Unknown] | tuple[Unknown, ...]``; the cast types its elements ``object``.
        for element in cast("list[object] | tuple[object, ...]", value):
            cls._validate_logic_element_shape(wire_key, element)

    @classmethod
    def _validate_logic_element_shape(cls, wire_key: str, element: object) -> None:
        """Reject a non-filter-input element of a logical branch (report Defect 4).

        A filter input is a mapping or a Strawberry-input dataclass --
        ``iter_input_items`` returns a walkable pair list for those and ``None``
        for anything else (a scalar, a bare string). An inactive element
        (``None`` / ``UNSET``) is a legitimate no-op arm skipped downstream, so it
        is accepted. Anything else -- ``"name"``, ``42`` -- is a malformed clause
        that would silently drop its predicate AND skip its ``check_*`` gate, so it
        raises a typed ``ConfigurationError``.
        """
        if is_inactive_value(element, unset_sentinel=UNSET):
            return
        if iter_input_items(element) is None:
            raise ConfigurationError(
                f"FilterSet {cls.__qualname__}: logical branch {wire_key!r} takes "
                f"filter inputs, got a {type(element).__name__} ({_safe_arg_repr(element)}). Each "
                "clause must be a mapping or filter-input object, not a scalar.",
            )

    @classmethod
    def _normalize_input(cls, input_value: object) -> dict[str, object]:
        """Translate a Strawberry input dataclass into `django-filter` form data.

        Per-primitive value normalization: each scalar attr passes
        through ``normalize_input_value`` so ``relay.GlobalID`` ->
        ``node_id``, Strawberry enum -> ``.value``, and
        ``filters.base.RangeFilter`` -> positional ``{name}_0`` /
        ``{name}_1`` keys all land in ``data`` correctly (``RangeFilter``
        is not imported here -- the symbol lives in ``filters.base`` and
        is referenced for shape-documentation; the actual range patch
        comes back from ``inputs.py::_normalize_range_value``). Related-
        branch keys (the
        ``shelves`` / ``books`` / etc. names declared via
        ``RelatedFilter``) are STRIPPED from the form-data dict before
        the parent's form sees it -- ``django-filter``'s form only owns
        the leaf lookup keys for the parent filterset, and any nested
        dict in those positions would fail validation. ``_apply_related_constraints``
        handles those branches separately, restricting the parent through each
        branch's correlated ``EXISTS`` earlier in the apply pipeline.

        GlobalID type-name validation happens at queryset-evaluation
        time inside ``GlobalIDFilter.filter`` /
        ``GlobalIDMultipleChoiceFilter.filter``, which read the owner
        via ``filter_instance.parent._owner_definition``. The owner is
        therefore not threaded as a parameter here.

        Leaf form keys come from ``inputs.py::filter_lookup_table``, the one
        place each operator-bag lookup's form key is decided
        (``_leaf_form_entries``); nothing here re-derives a key from
        ``(field, lookup)``.

        Fail-loud input contracts (each raises the typed
        ``ConfigurationError`` instead of silently dropping predicates
        and skipping ``check_*`` gates -- the same permission + filter
        bypass ``_validate_logic_branch_shape`` rejects for logical
        elements):

        * a NON-walkable top-level input (scalar / list / arbitrary
          object) raises instead of normalizing to ``{}``;
        * a field or lookup the lookup table does not hold raises instead
          of being written as a form key django-filter ignores;
        * a dict value that survives ``normalize_input_value`` on a
          NON-range filter raises via ``_require_range_patch_filter`` --
          the dict patch shape is reserved for the positional range
          patch, and any other dict would be splatted into unknown
          form-data keys the form silently ignores (the
          explicit-filter-applies-nothing failure mode).
        """
        if is_inactive_value(input_value, unset_sentinel=UNSET):
            return {}
        items = cls._iter_input_items(input_value)
        if items is None:
            # A non-walkable input (scalar / list / arbitrary object) would
            # contribute ZERO predicates AND fire ZERO ``check_*`` gates,
            # so the caller receives the UNFILTERED queryset while believing
            # the declared filter ran. ``_validate_logic_element_shape``
            # already fails loud for exactly this shape one level down (a
            # scalar arm of an ``and`` / ``or`` branch); the top of the
            # request is the same bypass and gets the same verdict. A wire
            # input can never land here (the generated input class types it),
            # so what arrives is always a hand-built input -- a direct
            # ``apply_sync`` / ``filter`` call, or a related branch of a
            # hand-built mapping -- and it must not be answered with rows.
            raise ConfigurationError(
                f"FilterSet {cls.__qualname__}: the filter input must be a "
                f"mapping or a filter-input object, got a "
                f"{type(input_value).__name__} ({_safe_arg_repr(input_value)}). "
                "A non-walkable input would silently drop every predicate and "
                "skip every check_* permission gate.",
            )

        lookups_by_attr = (
            filter_lookup_table(cls).by_input_attr if cls._meta.model is not None else {}
        )

        # The dataclass-vs-dict walk, the ``None`` / ``UNSET`` active-input skip,
        # the ``_field_specs`` lookup, and the leaf / related / logic
        # classification are the shared traversal mechanics owned by
        # ``utils/input_values.py::iter_active_fields``, driven by the family's
        # ONE canonical traversal config derived from ``_permission`` (the same
        # derivation the permission walkers classify through). Each yielded
        # ``ActiveField`` is dispatched here by ``kind``: ``LOGIC`` copies
        # the raw sub-tree under its ``django-filter`` wire key, ``RELATED`` is
        # stripped (owned by ``_apply_related_constraints``, since the parent form
        # cannot validate a nested-dict shape), and ``LEAF`` normalizes each
        # active lookup under the form key the lookup table holds for it.
        data: dict[str, object] = {}
        for field in iter_active_fields(cls, input_value, cls._input_traversal()):
            if field.kind == LOGIC:
                wire_key = LOGIC_OPERATORS_BY_PYTHON_ATTR[field.python_attr].wire_name
                cls._validate_logic_branch_shape(wire_key, field.raw_value)
                data[wire_key] = field.raw_value
                continue
            if field.kind == RELATED:
                # Related branches travel through `_apply_related_constraints`,
                # not the parent form.
                continue
            for form_key, filter_instance, value in cls._leaf_form_entries(
                lookups_by_attr,
                field.python_attr,
                field.raw_value,
            ):
                normalized = normalize_input_value(filter_instance, value, field_name=form_key)
                if isinstance(normalized, dict):
                    # Range-filter patch: positional form keys for one lookup.
                    cls._require_range_patch_filter(filter_instance, form_key, value)
                    data.update(normalized)
                else:
                    # An element-binding integer ``__in`` is range-coerced (and
                    # empty-aware) by ``IntegerInFilter`` at filter time, not here
                    # (``filter_for_lookup`` routes it there), so the normalized
                    # list passes straight through.
                    data[form_key] = normalized
        return data

    @classmethod
    def _leaf_form_entries(
        cls,
        lookups_by_attr: Mapping[str, Mapping[str, FormKeyedFilter]],
        python_attr: str,
        raw_value: object,
    ) -> list[tuple[str, Filter, object]]:
        """Return ``(form key, filter, value)`` for each active lookup of one leaf field.

        Per spec-027 Decision 3 Layer 5 a leaf field carries a per-field operator
        bag (``exact`` / ``i_contains`` / ``in_`` / ...). Each bag lookup's form
        key was decided once, when ``inputs.py::filter_lookup_table`` grouped the
        head, so the generated input and the form data never disagree. A scalar
        value is shorthand for the head's ``exact`` lookup, or for its only
        lookup. A field or lookup the table does not hold raises: it can only
        come from a hand-built mapping, and writing it as an unknown form key
        would apply nothing.
        """
        lookups = lookups_by_attr.get(python_attr)
        if lookups is None:
            raise ConfigurationError(
                f"FilterSet {cls.__qualname__}: {python_attr!r} is not a filter input "
                "field; it would apply nothing.",
            )
        bag_items = cls._operator_bag_items(raw_value)
        if bag_items is None:
            entry = lookups.get("exact")
            if entry is None and len(lookups) == 1:
                entry = next(iter(lookups.values()))
            if entry is None:
                raise ConfigurationError(
                    f"FilterSet {cls.__qualname__}: filter input field {python_attr!r} "
                    f"has no exact lookup to take a bare value (lookups: "
                    f"{sorted(lookups)!r}); pass an operator bag.",
                )
            return [(entry[0], entry[1], raw_value)]
        entries: list[tuple[str, Filter, object]] = []
        for lookup_attr, lookup_value in bag_items:
            # A Strawberry input dataclass defaults every unsupplied lookup to
            # ``UNSET`` rather than ``None``, so a partially supplied bag
            # (``title: { exact: UNSET, icontains: "foo" }``) skips the rest.
            if is_inactive_value(lookup_value, unset_sentinel=UNSET):
                continue
            entry = lookups.get(lookup_attr)
            if entry is None:
                raise ConfigurationError(
                    f"FilterSet {cls.__qualname__}: filter input field {python_attr!r} "
                    f"has no {lookup_attr!r} lookup (lookups: {sorted(lookups)!r}); it "
                    "would apply nothing.",
                )
            entries.append((entry[0], entry[1], lookup_value))
        return entries

    @classmethod
    def _require_range_patch_filter(
        cls,
        filter_instance: Filter,
        form_key: str,
        lookup_value: object,
    ) -> None:
        """Fail loud when a NON-range filter's normalized value is a dict patch.

        ``normalize_input_value`` returns a ``dict`` patch for exactly one
        legitimate shape: the range family's positional
        ``{<field>_0, <field>_1}`` patch. A dict coming back from any OTHER
        filter class means the raw value was itself a dict-shaped garbage
        value that the catch-all normalization passed through verbatim --
        a partial operator bag with unknown keys
        (``{"name": {"nope": "x"}}``), a wire-spelled lookup the python-attr
        sniff missed (``{"name": {"in": [...]}}``), or a dict parked under a
        known lookup key (``exact: {"k": "v"}``). Merging such a dict via
        ``data.update(...)`` SPLATS its keys into the form data as unknown
        fields django-filter's form silently ignores: the field association
        is lost, the consumer's explicit filter applies NOTHING, and the
        request returns unfiltered rows -- the same
        explicit-filter-applies-nothing failure the dict-bag walker exists to
        close. Only range-kind filters legitimately consume a multi-key patch,
        so only they may merge.

        No generated input annotation for a non-range filter accepts an
        object, so a dict here never comes off the wire: it is always a
        malformed programmatic input (the mapping form of ``apply_sync`` /
        ``filter``), which is why rejecting it cannot break a typed query.
        """
        if isinstance(filter_instance, (RangeFilter, django_filters.RangeFilter)):
            return
        raise ConfigurationError(
            f"FilterSet {cls.__qualname__}: filter {form_key!r} received a dict "
            f"value ({_safe_arg_repr(lookup_value)}) but "
            f"{type(filter_instance).__name__} consumes a single scalar form "
            "key. A dict value here would be splatted into unknown form-data "
            "keys the form silently ignores, dropping the filter. Pass the "
            "schema value shape for this filter (a scalar, a list, or a range "
            "{start, end} input on a RangeFilter primitive).",
        )

    @staticmethod
    def _operator_bag_items(raw_value: object) -> list[tuple[str, object]] | None:
        """Return the ``(lookup_attr, value)`` pairs of a per-field operator bag.

        ``_build_input_fields`` wraps each scalar field's lookups in a
        nested ``<Field>FilterInputType`` dataclass. The normalizer
        detects that shape via ``__dataclass_fields__`` (the same sniff
        ``_normalize_input`` uses to walk Strawberry input dataclasses); we sniff
        ``__dataclass_fields__`` instead of testing ``isinstance(..., dataclass)``
        because Strawberry's ``@strawberry.input`` decorator stamps real
        ``dataclass`` machinery on the class -- ``dataclasses.is_dataclass``
        would also match, but the attribute sniff is faster and matches
        the shape upstream uses to introspect input classes.
        ``RelatedFilter`` boundary values are handled separately via
        ``_apply_related_constraints`` so this helper does NOT see them.
        Returns ``None`` for scalar inputs that are not operator bags.
        """
        if isinstance(
            raw_value,
            (
                str,
                bytes,
                int,
                float,
                bool,
            ),
        ):
            return None
        if isinstance(
            raw_value,
            (
                list,
                tuple,
                set,
                frozenset,
            ),
        ):
            return None
        # A dict reaches a direct ``apply_*`` caller in two shapes that
        # must NOT be conflated:
        #   * an operator bag - ``{"i_contains": "x", "gt": 3}`` - whose
        #     keys are per-field lookup attrs; this is the shape that, when
        #     passed as a dict, must not fall through to the scalar branch,
        #     where ``normalize_input_value`` would splat the raw dict into
        #     the form data as unknown keys the form silently ignores (an
        #     explicit filter that applies nothing);
        #   * a multi-key filter VALUE - a ``RangeFilter``'s
        #     ``{"start": 1, "end": 5}`` - whose keys are NOT lookup attrs
        #     and which the scalar branch must hand to
        #     ``normalize_input_value`` so it produces the positional
        #     ``{<field>_0, <field>_1}`` patch.
        # Disambiguate by the keys: a dict is an operator bag only when
        # EVERY key names a known lookup attr (``_LOOKUP_PYTHON_ATTRS``
        # - ``start`` / ``end`` are absent). Strawberry-input dataclass
        # bags (the schema-driven path) always delegate unchanged.
        if isinstance(raw_value, dict):
            if raw_value and all(key in _LOOKUP_PYTHON_ATTRS for key in raw_value):
                return list(raw_value.items())
            return None
        return FilterSet._iter_input_items(raw_value)

    @classmethod
    @override
    def _permission_fallback_path(cls, python_attr: str) -> str:
        """Gate a field with no ``FieldSpec`` on the path its generated field would gate on.

        A direct mapping keyed by a head's own spelling (``books__title``), or
        built before the input class, reads the head's gate path from
        ``inputs.py::filter_lookup_table``; a key naming no head gates on itself
        (``_normalize_input`` then rejects it).
        """
        if cls._meta.model is None:
            return python_attr
        return filter_lookup_table(cls).gate_paths.get(python_attr, python_attr)

    @classmethod
    def _iter_visibility_steps(
        cls,
        input_value: object,
        parent_db: str | None = None,
    ) -> Iterator[_VisibilityStep]:
        """Yield the pre-await state each visibility derive method needs.

        Returns ``(field_name, target_type, child_filterset, child_input,
        child_base)`` for every active related branch. A branch whose
        ``target_type`` or ``child_filterset`` cannot be resolved raises
        ``ConfigurationError`` (``_branch_visibility_seed``, the resolution
        flat leaves walking the branch share) instead of being skipped: the branch is
        ACTIVE (the consumer supplied input for it), so skipping would
        drop the constraint entirely and silently return unfiltered
        parent rows - a filter the consumer believes is applied doing
        nothing. The same misconfiguration is also caught earlier, at
        finalize time, by ``_bind_filtersets`` subpass 2.5 for every
        schema-wired filterset; this runtime guard covers direct
        ``apply_sync`` / ``apply_async`` callers that never finalize.
        Composes with ``_iter_active_related_branches`` (per-branch yield
        shape) so the two iterators chain naturally without materializing
        intermediate lists.

        ``child_base`` is pinned to ``parent_db`` (the alias of the parent
        queryset being filtered) via ``.using(...)`` so the child's
        ``get_queryset`` visibility hook sees the SAME database as the parent
        request -- matching the cascade-permission path
        (``permissions.py`` builds its base with
        ``._default_manager.using(queryset.db).all()``). Without it a sharded
        parent (e.g. ``shard_b``) would run the child hook against the default
        alias, so an alias-sensitive hook applies the wrong shard's policy
        (report Defect 3). ``None`` leaves the router default in place for the
        single-database case and for direct callers who do not thread an alias.
        """
        for field_name, declaration, child_input in cls._iter_active_related_branches(
            input_value,
        ):
            # ``related_filters`` holds only the ``RelatedFilter`` declarations the
            # metaclass collected (``sets_mixins.py::collect_related_declarations``).
            target_type, child_filterset, child_base = cls._branch_visibility_seed(
                field_name,
                cast("RelatedFilter", declaration),
                parent_db,
            )
            yield field_name, target_type, child_filterset, child_input, child_base

    @classmethod
    def _branch_visibility_seed(
        cls,
        field_name: str,
        related_filter: RelatedFilter,
        parent_db: str | None,
    ) -> tuple[type[DjangoType], type[FilterSet], models.QuerySet[models.Model]]:
        """Resolve an active branch's target type, child filterset and unscoped base rows.

        The one resolution of the ``DjangoType`` whose ``get_queryset`` scopes a
        declared ``RelatedFilter`` branch (``field_name`` on ``cls``), shared by
        the nested branch (``_iter_visibility_steps``) and every flat leaf
        walking the branch (``_hop_visible_rows``). The branch is ACTIVE (the
        consumer supplied input for it, nested or flat), so a target that cannot
        be resolved raises ``ConfigurationError`` instead of being skipped:
        skipping would drop the visibility scoping and silently return rows the
        target type hides.
        """
        target_type = cls._target_type_for_related_filter(related_filter)
        child_filterset = related_filter.filterset
        if target_type is None or child_filterset is None:
            child_model = getattr(getattr(child_filterset, "_meta", None), "model", None)
            target_label = getattr(child_model, "__qualname__", "<unresolved>")
            reason = (
                f"no DjangoType is registered for its target model {target_label}"
                if child_filterset is not None
                else "its target FilterSet could not be resolved"
            )
            raise ConfigurationError(
                f"FilterSet {cls.__qualname__}: related filter branch "
                f"{field_name!r} is active in the filter input (nested, or walked by a "
                f"flat leaf) but {reason}. "
                "The branch's visibility scoping runs the target type's "
                "get_queryset (spec-027 Decision 8 step 3); skipping it would "
                "silently return unfiltered rows. Register a DjangoType for "
                "the target model or remove the RelatedFilter.",
            )
        # Trusted, not checked here: a branch's child filterset declares
        # ``Meta.model`` (a model-less child would fail inside ``base_queryset``).
        child_model = cast("type[models.Model]", child_filterset._meta.model)
        return target_type, child_filterset, base_queryset(child_model, using=parent_db)

    @classmethod
    def _derive_related_visibility_querysets_sync(
        cls,
        input_value: object,
        info: object,
        *,
        parent_db: str | None = None,
        _depth: int = 0,
    ) -> dict[str, models.QuerySet[models.Model]]:
        """Run each active branch's target ``get_queryset(...)`` then recurse.

        Reuses ``django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync``
        - the existing helper handles the sync-misuse detection and
        raises ``SyncMisuseError`` (a ``ConfigurationError`` and
        ``RuntimeError`` subclass); ``apply``'s catch-and-rethrow
        translates that into a ``RuntimeError`` consumers can match
        on via the actionable "use apply_async instead" message.

        After the visibility hook runs, the child filterset's
        ``apply_sync`` is invoked against the visibility-scoped queryset
        so nested input clauses (e.g. ``shelves: { code: { iContains:
        "A" } }``) narrow the child queryset BEFORE the parent's
        restriction through the branch is built (spec-027 Decision 8).

        The child ``apply_sync`` runs with ``run_permissions=False``: this
        step only needs the child's filtered, visibility-scoped queryset,
        and the child's ``check_<field>_permission`` gates are fired ONCE by
        the top-level ``_run_permission_checks`` pass, which recurses into
        every active related branch. Letting the derivation's child apply
        ALSO fire them re-runs each nested gate once per enclosing level
        (compounding with related-nesting depth) and breaks the documented
        "the tree-composition/derivation paths deliberately do NOT re-run
        permission checks" contract. Permission methods never mutate the
        queryset, so skipping them here leaves the derived queryset
        identical.

        ``parent_db`` pins each child base to the parent request's database
        alias (report Defect 3); ``_depth`` is the shared traversal budget --
        the child ``apply_sync`` re-enters at ``_depth + 1`` so a
        self-referential ``RelatedFilter`` is capped with a typed error rather
        than recursing into a ``RecursionError`` (report Defect 5).
        """
        result: dict[str, models.QuerySet[models.Model]] = {}
        for (
            field_name,
            target_type,
            child_filterset,
            child_input,
            child_base,
        ) in cls._iter_visibility_steps(input_value, parent_db):
            scoped = apply_type_visibility_sync(target_type, child_base, info)
            result[field_name] = child_filterset.apply_sync(
                child_input,
                scoped,
                info,
                run_permissions=False,
                _depth=_depth + 1,
            )
        return result

    @classmethod
    async def _derive_related_visibility_querysets_async(
        cls,
        input_value: object,
        info: object,
        *,
        parent_db: str | None = None,
        _depth: int = 0,
    ) -> dict[str, models.QuerySet[models.Model]]:
        """Async sibling of `_derive_related_visibility_querysets_sync`.

        Runs the child ``apply_async`` with ``run_permissions=False`` for the
        same reason the sync twin passes ``run_permissions=False`` (see there):
        the top-level ``_run_permission_checks`` pass owns every nested gate,
        so the derivation must not re-fire them. ``parent_db`` (report Defect 3)
        and ``_depth`` (report Defect 5) thread exactly as in the sync twin.
        """
        result: dict[str, models.QuerySet[models.Model]] = {}
        for (
            field_name,
            target_type,
            child_filterset,
            child_input,
            child_base,
        ) in cls._iter_visibility_steps(input_value, parent_db):
            scoped = await apply_type_visibility_async(target_type, child_base, info)
            result[field_name] = await child_filterset.apply_async(
                child_input,
                scoped,
                info,
                run_permissions=False,
                _depth=_depth + 1,
            )
        return result

    @classmethod
    def _raise_logic_depth_exceeded(cls) -> NoReturn:
        """Raise the canonical depth-cap ``ConfigurationError`` for this FilterSet.

        Single source of truth for the consumer-visible message shared by
        ``_collect_nested_visibility_querysets_async``, ``_run_permission_checks``,
        and ``_evaluate_logic_tree`` -- all five sites cap at
        ``cls._MAX_LOGIC_DEPTH`` and surface the identical typed error. The
        sentence and the defensive class-label read are
        ``utils/input_values.py::raise_set_traversal_depth_exceeded``, shared with
        the permission walk's related-branch cap so one budget is never
        enforced in two vocabularies.
        """
        raise_set_traversal_depth_exceeded(
            cls,
            branch="logical-branch",
            input_noun="filter",
            subject="FilterSet",
        )

    @classmethod
    async def _collect_nested_visibility_querysets_async(
        cls,
        input_value: object,
        info: object,
        *,
        parent_db: str | None = None,
        _depth: int = 0,
        flat_hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]]
        | None = None,
    ) -> dict[int, dict[str, models.QuerySet[models.Model]]]:
        """Pre-walk logical branches and derive each branch's visibility map.

        Returns a map keyed by ``id(child_input)`` -- the same Python object
        identity ``_q_for_branch`` will later receive from
        ``_evaluate_logic_tree`` (preserved by ``_normalize_input``, which
        copies the child dicts verbatim into ``self.data``). ``apply_async``
        calls this BEFORE the top-level ``.qs`` read; ``_q_for_branch``
        consults the stash via the sibling instance's
        ``_nested_qs_by_branch_id`` and skips the sync derive that would
        otherwise raise ``SyncMisuseError`` mid-``.qs`` when a nested
        branch's target ``get_queryset`` is async-only.

        Both the Strawberry-side keys (``and_`` / ``or_`` / ``not_``) and
        the normalized wire-side keys (``and`` / ``or`` / ``not``) are
        walked via ``_extract_branch_value`` so a consumer who hands a
        pre-normalized dict still gets pre-derived maps; the walker
        recurses so deeper nesting (``or: [{or: [...]}]``) also lands in
        the stash before the sync ``_q_for_branch`` ever runs.

        Logical-branch nesting under ``apply_async`` is capped by the same
        ``_MAX_LOGIC_DEPTH`` guard ``_evaluate_logic_tree`` enforces -- a
        pre-walk that exceeds the cap signals the same consumer-side
        misuse and surfaces the same typed ``ConfigurationError`` here
        rather than waiting for the sync recursion to discover it.

        ``flat_hop_visibility``, when given, also receives the awaited target
        visibility of every hop a supplied flat leaf of each arm walks
        (``_derive_flat_hop_visibility_async``), so this one walk of the
        logical arms pre-derives both kinds of relational scoping.
        """
        result: dict[int, dict[str, models.QuerySet[models.Model]]] = {}
        if is_inactive_value(input_value, unset_sentinel=UNSET):
            return result
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()
        # Walk each logical sub-branch via ``_iter_logic_branches``. Each
        # child_input gets its OWN visibility derive plus a recursive walk so
        # deeply-nested branches all carry pre-derived maps before the sync
        # ``_q_for_branch`` ever runs.
        for _op, children in cls._iter_logic_branches(input_value):
            for child_input in children:
                result[id(child_input)] = await cls._derive_related_visibility_querysets_async(
                    child_input,
                    info,
                    parent_db=parent_db,
                    _depth=_depth,
                )
                if flat_hop_visibility is not None:
                    await cls._derive_flat_hop_visibility_async(
                        child_input,
                        info,
                        flat_hop_visibility,
                        parent_db=parent_db,
                    )
                # Recurse so deeper nesting (``or: [{or: [...]}]``) also
                # lands in the stash.
                nested = await cls._collect_nested_visibility_querysets_async(
                    child_input,
                    info,
                    parent_db=parent_db,
                    _depth=_depth + 1,
                    flat_hop_visibility=flat_hop_visibility,
                )
                result.update(nested)
        return result

    @staticmethod
    def _target_type_for_related_filter(related_filter: RelatedFilter) -> type[DjangoType] | None:
        """Resolve the `DjangoType` whose ``get_queryset()`` scopes the branch.

        Prefer the child filterset's *bound owner* - the type the consumer
        explicitly wired via ``Meta.filterset_class`` (``_owner_definition``,
        bound at finalizer phase 2.5) - over a model-only registry lookup. When a
        child model has more than one registered ``DjangoType`` and the child
        filterset is bound to a non-primary one, a model-only lookup resolves the
        *primary* type and runs ITS ``get_queryset()`` against the non-primary's
        filterset, scoping the related branch by the wrong visibility hook (a
        silent row-leak). ``definition.origin`` is the same ``DjangoType`` class
        the registry stores (``types/base.py`` registers ``cls`` with
        ``origin=cls``), so both branches hand ``apply_type_visibility_*`` an object
        exposing ``get_queryset``.

        This mirrors ``_resolve_relation_target_type`` (already owner-aware); the
        registry lookup is the fallback for the unbound / single-type-per-model
        case.
        """
        child_filterset = related_filter.filterset
        # ``FilterSet._owner_definition`` is the finalizer-bound ``DjangoTypeDefinition`` slot,
        # whose ``origin`` is the ``DjangoType``.
        child_owner: DjangoTypeDefinition | None = getattr(
            child_filterset,
            "_owner_definition",
            None,
        )
        owner_type: type[DjangoType] | None = (
            getattr(child_owner, "origin", None) if child_owner is not None else None
        )
        if owner_type is not None:
            return owner_type
        # django-filter's metaclass stores ``_meta = FilterSetOptions(...)`` on every filterset.
        child_meta: FilterSetOptions | None = getattr(child_filterset, "_meta", None)
        child_model: type[models.Model] | None = getattr(child_meta, "model", None)
        if child_model is None:
            return None
        # ``registry.get`` owns the primary-first precedence; see
        # ``_resolve_relation_target_type`` for the same collapse.
        return registry.get(child_model)

    @classmethod
    @override
    def _check_permission_depth(cls, _depth: int) -> None:
        """Cap logical-branch nesting at ``_MAX_LOGIC_DEPTH``."""
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()

    @classmethod
    @override
    def _run_logic_permission_checks(
        cls,
        input_value: object,
        request: object,
        /,
        *,
        _fired: dict[type[object], set[str]],
        _bare: ActiveInputPermissionMixin,
        _depth: int,
    ) -> None:
        """Recurse into logical operator branches so nested clauses stay gated.

        Filter-only: the order family has no operator bag. Same ``cls`` reuses
        ``_bare`` and the shared ``_fired`` map.
        """
        for _op, children in cls._iter_logic_branches(input_value):
            for child_input in children:
                cls._run_permission_checks(
                    child_input,
                    request,
                    _fired=_fired,
                    _bare=_bare,
                    _depth=_depth + 1,
                )

    def check_permissions(self, request: object, requested_fields: set[str] | None = None) -> None:
        """Backward-compatible thin delegate to `_run_permission_checks`.

        Cookbook callers reach for the bound-method form; the active-input
        normalization happens in `_run_permission_checks` so both entry
        points share one source of truth.
        """
        # When the cookbook caller has already normalized to a set of
        # field-path strings, walk it directly so behavior matches the
        # cookbook's contract for explicit callers.
        if requested_fields:
            for field_path in requested_fields:
                self._invoke_permission_method(self, field_path, request)
            return
        # No explicit set supplied - fall through to the active-input
        # variant. `_run_permission_checks` is a classmethod; route the
        # currently-bound form data (already a dict) through it.
        type(self)._run_permission_checks(self.data or {}, request)

    @classmethod
    def _validate_form_or_raise(cls, filterset_instance: FilterSet) -> None:
        """Raise `GraphQLError` with the canonical extensions payload.

        Decision 8 step 6 - `BaseFilterSet.qs` silently
        falls through to `filter_queryset` when the form has errors, so
        the explicit `is_valid()` call here is what turns a malformed
        input into a structured GraphQL response.

        Classmethod-with-self-instance shape: ``apply_sync`` /
        ``apply_async`` / ``_q_for_branch`` all reach this validator via
        ``cls._validate_form_or_raise(filterset_instance)``. The method
        is declared a classmethod so subclasses can override the
        validation policy (e.g. inject custom GraphQL-error metadata)
        without rebinding the instance method on every sibling filterset
        a recursive branch builds; the instance is passed explicitly so
        the override sees both the policy-owning class (``cls``) and the
        actual filterset whose form to validate.
        """
        if filterset_instance.form.is_valid():
            return
        raise GraphQLError(
            "Invalid filter input",
            extensions=coded_error_extensions(
                FILTER_INVALID_ERROR_CODE,
                errors=filterset_instance.form.errors.get_json_data(),
            ),
        )

    # ------------------------------------------------------------------
    # Tree-form logic substrate (`filter_queryset` override).
    # ------------------------------------------------------------------

    @staticmethod
    def _invoke_suppressing_framework_distinct(
        filter_instance: Filter,
        inner_root: models.QuerySet[_M],
        value: object,
    ) -> object:
        """Invoke ``filter_instance.filter`` on a root read only as a row set, distinct-free.

        Two callers hand it such a root: the routed correlated ``EXISTS`` body
        (``_apply_flat_leaves``) and the child rows a declared branch's
        correlated ``EXISTS`` reads (``_filter_child_rows``). A routed candidate's
        ``distinct`` flag is machinery-origin (the fan-out-compensating flag the
        generation path stamps for a to-many path; see
        ``CandidateFilterMetadata``), and ``Query.exists()`` clears the select
        list and ordering but NOT the ``distinct`` flag, so invoking such a
        filter unchanged against the inner root compiles
        ``EXISTS(SELECT DISTINCT 1 ...)``. Inside either root a ``DISTINCT``
        changes no answer (an ``EXISTS`` reads membership) but is not
        performance-inert on every backend (unique / sort planning inside every subquery).
        The flag is therefore suppressed for the duration of the ORIGINAL
        ``filter()`` invocation (which still owns filter/exclude selection, range
        decomposition, GlobalID decoding, and Django ``split_exclude`` semantics).

        The mutation is on the live FilterSet's per-instance deepcopy
        (``self.filters[name]``), never a class-level or base filter. The
        ORIGINAL live value is restored in ``finally`` even when decoding or
        queryset construction raises.
        """
        original_distinct = filter_instance.distinct
        filter_instance.distinct = False
        try:
            return filter_instance.filter(inner_root, value)
        finally:
            filter_instance.distinct = original_distinct

    @classmethod
    def _flat_leaf_walk(
        cls,
        filter_instance: Filter,
    ) -> tuple[tuple[RelationHop, ...], str] | None:
        """Return the hops a flat leaf's ORM path walks and the path left on the last target.

        The hops are ``utils/permissions.py::walk_declared_relation_path``'s
        visibility reading (``undeclared=True``) of the filter's ``field_name``:
        each declared ``RelatedFilter`` hop, the chain the flat-path permission
        gates fire along, then one undeclared hop per relation segment past them
        (``alt_shelves``, ``items`` in ``items__name``). The path left is empty
        for a relation-key leaf (``shelf``, ``shelf__branch``, ``alt_shelves``:
        nothing after the last relation). ``None`` for a leaf whose walk reads no
        visibility: a same-model leaf, a path whose relations no declaration
        claims and whose models no type scopes (``RelationHop.scope``), a
        consumer ``method=`` declared on this set (its Python receives this
        set's queryset and owns its own scoping; GOAL.md "Trust boundary"), a
        ``RelatedFilter`` (a branch, never a leaf), and a
        ``ProjectedChildFilter``, whose hop is its projection
        (``_projection_hop``).
        """
        if (
            isinstance(filter_instance, (ProjectedChildFilter, RelatedFilter))
            or filter_instance.method is not None
        ):
            return None
        hops, remainder = walk_declared_relation_path(
            cls,
            _bound_field_name(filter_instance),
            related_attr=cls._permission.traversal.related_attr,
            target_attr=cls._permission.target_attr,
            undeclared=True,
        )
        if not any(hop.declared or hop.scope is not None for hop in hops):
            return None
        return hops, LOOKUP_SEP.join(remainder)

    @classmethod
    def _projection_hop(cls, projection: ChildProjection) -> RelationHop:
        """Return the declared hop a ``ProjectedChildFilter`` of this set runs its child across."""
        # ``related_filters`` is the metaclass's name-keyed ``RelatedFilter`` map
        # (``sets_mixins.py::collect_related_declarations``); the projection was
        # expanded from one of its entries.
        related: Mapping[str, RelatedFilter] = getattr(cls, "related_filters", {})
        return RelationHop(
            cls,
            projection.branch,
            related[projection.branch],
            projection.filterset,
        )

    @classmethod
    def _visibility_hops(cls, filter_instance: Filter) -> tuple[RelationHop, ...]:
        """Return every declared hop whose target visibility an active ``filter_instance`` reads.

        A walked leaf reads its walk's hops (``_flat_leaf_walk``); a
        ``ProjectedChildFilter`` reads its projection's hop, then whatever its
        child filter reads in the child set, by the child class's own filters
        (the async pre-pass has no child instance yet). Every other leaf reads
        none.
        """
        if isinstance(filter_instance, ProjectedChildFilter):
            projection = filter_instance._projection
            child_cls = projection.filterset
            return (
                cls._projection_hop(projection),
                *child_cls._visibility_hops(child_cls.get_filters()[projection.name]),
            )
        walk = cls._flat_leaf_walk(filter_instance)
        return () if walk is None else walk[0]

    @classmethod
    def _supplied_leaf_filters(cls, input_value: object) -> list[tuple[str, Filter]]:
        """Return ``(name, filter)`` for every supplied leaf of one input level, in input order.

        The supplied leaves are read through ``inputs.py::filter_lookup_table``,
        the one input-leaf to filter mapping, so this is exactly the filters the
        form will run. A leaf is supplied when present and not ``None`` /
        ``UNSET``, whether or not the filter then skips its value.
        """
        lookups_by_attr = (
            filter_lookup_table(cls).by_input_attr if cls._meta.model is not None else {}
        )
        filters: list[tuple[str, Filter]] = []
        for field in iter_active_fields(cls, input_value, cls._input_traversal()):
            if field.kind != LEAF:
                continue
            filters.extend(
                (form_key, filter_instance)
                for form_key, filter_instance, _value in cls._leaf_form_entries(
                    lookups_by_attr,
                    field.python_attr,
                    field.raw_value,
                )
            )
        return filters

    @classmethod
    @override
    def _permission_walk_gates(cls, input_value: object) -> tuple[tuple[type[object], str], ...]:
        """Return the gates the nested twin of each supplied leaf's ORM path fires (``_leaf_gates``)."""
        return tuple(
            gate
            for name, filter_instance in cls._supplied_leaf_filters(input_value)
            for gate in cls._leaf_gates(name, filter_instance)
        )

    @classmethod
    def _leaf_gates(
        cls,
        name: str,
        filter_instance: Filter,
    ) -> tuple[tuple[type[object], str], ...]:
        """Return the gates the nested twin of leaf ``name``'s ORM path fires beyond its gate path's.

        The leaf's gate path already fires its own gate and, for a leaf of a
        child set reached flat, the projection's branch gate and the child
        filter's own gate (``_fire_flat_relation_path_gates``). What remains is
        the walk of the filter's own path in the set that declares it, the
        gates the nested twin's run of that set fires:

        - a ``ProjectedChildFilter``, or an expanded copy of a child filter
          (``_expansion_origin``), answers for its child filter in the child
          set, recursively;
        - any other leaf walking declared hops (``_flat_leaf_walk``) fires
          ``utils/permissions.py::relation_path_gates`` over its ``field_name``:
          each walked branch gate and the last target set's gate for the path
          left there (its primary key for a relation-key leaf), whatever
          lookup, ``isnull`` or ``exclude`` the filter applies;
        - a leaf walking no hop, a ``method=`` filter declared on this set
          included, adds none.
        """
        if isinstance(filter_instance, ProjectedChildFilter):
            projection = filter_instance._projection
            child_cls = projection.filterset
            return child_cls._leaf_gates(
                projection.name,
                child_cls.get_filters()[projection.name],
            )
        if cls._flat_leaf_walk(filter_instance) is None:
            return ()
        origin = cls._expansion_origin(name, filter_instance)
        if origin is not None:
            child_cls, child_name = origin
            return child_cls._leaf_gates(child_name, child_cls.get_filters()[child_name])
        return relation_path_gates(
            cls,
            _bound_field_name(filter_instance),
            related_attr=cls._permission.traversal.related_attr,
            target_attr=cls._permission.target_attr,
        )

    @classmethod
    def _expansion_origin(
        cls,
        name: str,
        filter_instance: Filter,
    ) -> tuple[type[FilterSet], str] | None:
        """Return the child set and child filter name an expanded copy named ``name`` was made from.

        ``_expand_related_filter`` names a copy ``<branch>__<child name>`` and
        appends the child name to its provenance breadcrumb, so the last
        breadcrumb names the child filter and the rest of ``name`` the branch.
        ``None`` for a filter that is not such a copy, and for one held under a
        name no declared branch prefixes (a consumer re-declaring a copy).
        """
        record = filter_generation_provenance(filter_instance)
        if record is None or not record.expanded_from:
            return None
        child_name = record.expanded_from[-1]
        branch = name.removesuffix(f"{LOOKUP_SEP}{child_name}")
        # ``related_filters`` is the metaclass's name-keyed ``RelatedFilter`` map
        # (``sets_mixins.py::collect_related_declarations``).
        related: Mapping[str, RelatedFilter] = getattr(cls, "related_filters", {})
        declaration = related.get(branch)
        child_cls = declaration.filterset if declaration is not None else None
        if child_cls is None:
            return None
        return child_cls, child_name

    @classmethod
    async def _derive_flat_hop_visibility_async(
        cls,
        input_value: object,
        info: object,
        into: dict[tuple[object, str | None], models.QuerySet[models.Model]],
        *,
        parent_db: str | None,
    ) -> None:
        """Await the target visibility of every hop a supplied flat leaf of one input level walks.

        The flat-leaf twin of ``_derive_related_visibility_querysets_async``:
        ``apply_async`` runs it for the top level and
        ``_collect_nested_visibility_querysets_async`` for every ``and`` / ``or``
        / ``not`` arm, so the sync ``.qs`` read finds each hop already in the
        request-wide map and never runs an async-only ``get_queryset``. The
        leaves are ``_supplied_leaf_filters``'s, so the pre-pass sees exactly the
        filters the form will run.
        It runs before any form exists, so it awaits
        the hops of every SUPPLIED leaf (present, not ``None`` / ``UNSET``): a
        supplied value the filter then skips (an empty string) costs one awaited
        ``get_queryset`` and constrains nothing, as a present-but-empty nested
        branch does; an unsupplied leaf costs nothing.
        """
        hops = (
            hop
            for _name, filter_instance in cls._supplied_leaf_filters(input_value)
            for hop in cls._visibility_hops(filter_instance)
        )
        for hop in hops:
            if not hop.declared:
                await cls._await_scoped_rows(hop.scope, info, into, parent_db)
                continue
            owner = cast("type[FilterSet]", hop.owner)
            related_filter = cast("RelatedFilter", hop.related_obj)
            for scope in owner._branch_via_types(related_filter):
                await cls._await_scoped_rows(scope, info, into, parent_db)
            key = (id(related_filter), parent_db)
            if key in into:
                continue
            target_type, _child, child_base = owner._branch_visibility_seed(
                hop.declared_attr,
                related_filter,
                parent_db,
            )
            into[key] = await apply_type_visibility_async(target_type, child_base, info)
        for _name, declaration, _child_input in cls._iter_active_related_branches(input_value):
            # ``related_filters`` holds only ``RelatedFilter`` declarations.
            for scope in cls._branch_via_types(cast("RelatedFilter", declaration)):
                await cls._await_scoped_rows(scope, info, into, parent_db)

    @classmethod
    def _branch_via_types(
        cls,
        related_filter: RelatedFilter,
    ) -> tuple[type[DjangoType] | None, ...]:
        """Return the type scoping each intermediate model a branch of this set crosses.

        A declaration whose ``field_name`` spans several relations
        (``target_version__milestone``) passes through the rows of each model
        before the last; each answers for its type
        (``utils/querysets.py::relation_path_visibility_types``, re-entry into
        this set's own model reading the type this set is bound to). Empty for a
        single relation.
        """
        relation = _bound_field_name(related_filter)
        if LOOKUP_SEP not in relation:
            return ()
        owner = cls._owner_definition
        return relation_path_visibility_types(
            # A branch's declaring set is model-backed (``related_filters`` is collected
            # for model-backed sets only).
            cast("type[models.Model]", cls._meta.model),
            relation.rpartition(LOOKUP_SEP)[0],
            root=owner.origin if owner is not None else None,
        )

    @classmethod
    def _via_rows(
        cls,
        related_filter: RelatedFilter,
        info: object,
        visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]],
        parent_db: str | None,
    ) -> tuple[models.QuerySet[models.Model] | None, ...]:
        """Return the rows each intermediate model of a branch of this set may pass through.

        One entry per model ``_branch_via_types`` reads: the rows its type lets
        the request see (``_scoped_rows``), ``None`` for a model no type scopes.
        """
        return tuple(
            None if scope is None else cls._scoped_rows(scope, info, visibility, parent_db)
            for scope in cls._branch_via_types(related_filter)
        )

    @staticmethod
    def _scoped_rows(
        scope: type[DjangoType],
        info: object,
        visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]],
        parent_db: str | None,
    ) -> models.QuerySet[models.Model]:
        """Return the rows of ``scope``'s model its ``get_queryset`` lets this request see.

        The visibility of a model no declaration owns (an undeclared hop, an
        intermediate model of a multi-relation branch), keyed by
        ``(scope, parent_db)`` in the request-wide hop map: read from it when
        present (``apply_async`` pre-fills it, ``_await_scoped_rows``), derived
        and stored on first use otherwise.
        """
        key = (scope, parent_db)
        rows = visibility.get(key)
        if rows is None:
            seed = base_queryset(model_for(scope), using=parent_db)
            rows = apply_type_visibility_sync(scope, seed, info)
            visibility[key] = rows
        return rows

    @staticmethod
    async def _await_scoped_rows(
        scope: type[DjangoType] | None,
        info: object,
        into: dict[tuple[object, str | None], models.QuerySet[models.Model]],
        parent_db: str | None,
    ) -> None:
        """Await ``_scoped_rows``'s rows of ``scope`` into the hop map; nothing for ``None``."""
        if scope is None or (scope, parent_db) in into:
            return
        seed = base_queryset(model_for(scope), using=parent_db)
        into[scope, parent_db] = await apply_type_visibility_async(scope, seed, info)

    def _hop_visibility(self) -> dict[tuple[object, str | None], models.QuerySet[models.Model]]:
        """Return this instance's request-wide hop visibility map, creating it on first read."""
        visibility = self._flat_hop_visibility
        if visibility is None:
            visibility = self._flat_hop_visibility = {}
        return visibility

    def _hop_visible_rows(
        self,
        hop: RelationHop,
        parent_db: str | None,
    ) -> models.QuerySet[models.Model]:
        """Return ``hop``'s target rows its ``DjangoType.get_queryset`` lets this request see.

        The nested branch's step 3 for one declared hop: the target type is
        resolved and seeded on ``parent_db`` by ``_branch_visibility_seed``, then
        scoped by ``apply_type_visibility_sync`` with this instance's resolver
        ``info``. Read from the request-wide map when present (``apply_async``
        pre-fills it), derived and stored on first use otherwise. An undeclared
        hop reads its scoping type's rows (``_scoped_rows``), or, when no type
        scopes its model, every row of it, as Django's join reads them.
        """
        visibility = self._hop_visibility()
        if not hop.declared:
            scope = hop.scope
            if scope is None:
                return _hop_model(hop)._base_manager.using(parent_db)
            return self._scoped_rows(scope, self._apply_info, visibility, parent_db)
        key = (id(hop.related_obj), parent_db)
        rows = visibility.get(key)
        if rows is None:
            owner = cast("type[FilterSet]", hop.owner)
            target_type, _child, child_base = owner._branch_visibility_seed(
                hop.declared_attr,
                cast("RelatedFilter", hop.related_obj),
                parent_db,
            )
            rows = apply_type_visibility_sync(target_type, child_base, self._apply_info)
            visibility[key] = rows
        return rows

    def _filter_child_rows(
        self,
        filter_instance: Filter,
        rows: models.QuerySet[_M],
        value: object,
    ) -> models.QuerySet[_M]:
        """Run ``filter_instance`` over child rows a branch restriction reads as a row set.

        Distinct-free (``_invoke_suppressing_framework_distinct``), with the
        ``QuerySet`` return assertion ``BaseFilterSet.filter_queryset`` makes.
        """
        result = self._invoke_suppressing_framework_distinct(filter_instance, rows, value)
        assert isinstance(result, models.QuerySet), (
            f"Expected '{type(self).__name__}' filter {filter_instance.field_name!r} "
            f"to return a QuerySet, but got a {type(result).__name__} instead."
        )
        return cast("models.QuerySet[_M]", result)

    def _leaf_applies(
        self,
        queryset: models.QuerySet[_M],
        filter_instance: Filter,
        value: object,
    ) -> bool:
        """Whether a leaf walking declared hops constrains anything for ``value``: its activity probe.

        A filter that returns its input BY IDENTITY applied no constraint
        (django-filter's empty-value skip, ``MultipleChoiceFilter.is_noop``, a
        ``FilterMethod`` short circuit), whatever rows it runs over. The probe is
        the leaf's terminal (``_leaf_chain``) invoked with the value it would
        receive, over the rows of the model it was written for, unscoped: the
        last hop target's base rows (``queryset`` when the chain walks no hop),
        so an inactive leaf runs no ``get_queryset`` and an active one is never
        evaluated against a model its path does not resolve on (a child set on a
        multi-table-inheritance subclass of the relation's target). A walk
        reaching a hop whose target set does not resolve has no terminal; its
        original invocation over ``queryset`` probes it, and an active one raises
        at ``_apply_active_leaf``.
        """
        if any(
            hop.declared and hop.target is None
            for hop in type(self)._visibility_hops(filter_instance)
        ):
            return filter_instance.filter(queryset, value) is not queryset
        # ``_apply_relation_leaf`` probes only a leaf ``_flat_leaf_walk`` reads or a
        # ``ProjectedChildFilter``, which always carries its projection hop.
        chain = cast("_LeafChain", self._leaf_chain(filter_instance))
        rows = self._chain_base(chain, queryset)
        return chain.terminal.filter(rows, chain.terminal_value(value)) is not rows

    def _chain_base(
        self,
        chain: _LeafChain,
        queryset: models.QuerySet[_M],
    ) -> models.QuerySet[models.Model]:
        """The unscoped rows ``chain``'s terminal is written for: its last hop target's, else ``queryset``."""
        if not chain.hops:
            return cast("models.QuerySet[models.Model]", queryset)
        return base_queryset(_hop_model(chain.hops[-1]), using=queryset.db)

    def _apply_relation_leaf(
        self,
        queryset: models.QuerySet[_M],
        filter_instance: Filter,
        value: object,
    ) -> models.QuerySet[_M]:
        """Apply a flat leaf walking declared hops over the rows each hop's target type shows.

        Covers a leaf ``_flat_leaf_walk`` reads (an expanded child, a
        ``Meta.fields`` traversal, a declared filter whose ``field_name`` crosses
        a declared ``RelatedFilter``, a relation-key leaf) and a
        ``ProjectedChildFilter``. An inactive leaf (``_leaf_applies``) returns
        ``queryset`` unchanged: restricting it to parents reaching ANY visible
        child would turn "no constraint" into "has a visible child", and
        ``_apply_flat_leaves`` runs every filter in ``cleaned_data``, supplied or
        not. An active leaf answers as Django's ORM answers the same lookup in a
        world where every row a hop's target type hides, and every row a hop's
        explicit ``RelatedFilter(queryset=...)`` excludes, does not exist
        (``_apply_active_leaf``).
        """
        if not self._leaf_applies(queryset, filter_instance, value):
            return queryset
        return self._apply_active_leaf(queryset, filter_instance, value)

    def _bound_terminal(
        self,
        filter_instance: Filter,
        hop: RelationHop,
        field_name: str,
    ) -> Filter:
        """Return a copy of ``filter_instance`` filtering ``field_name`` over the rows ``hop`` reaches.

        The copy's ``parent``, which a live-``field_name`` filter resolves its
        model and owner against, is the hop's target set instance
        (``_projection_child``), or for an undeclared hop the face its rows offer
        in place of one (``_UndeclaredHopSet``). A shallow copy of the
        per-request filter, so the form field it already built carries over and
        this set's own instance is untouched.
        """
        terminal = copy.copy(filter_instance)
        terminal.field_name = field_name
        target_set = (
            # The walk continues only past a declared hop whose target resolved to a set class.
            self._projection_child(cast("type[FilterSet]", hop.target))
            if hop.declared
            else _UndeclaredHopSet(hop, self.request)
        )
        # django-filter stamps ``parent`` on every per-request filter; the stubs omit it.
        setattr(terminal, "parent", target_set)  # noqa: B010
        return terminal

    def _leaf_chain(self, filter_instance: Filter) -> _LeafChain | None:
        """Return how an active leaf of this set reads the related rows, ``None`` for a leaf walking no hop.

        A ``ProjectedChildFilter`` reads its projection's hop, then whatever its
        child filter reads in the child set (its own hops, or none: the child
        filter itself runs over the hop's visible rows). A walked leaf reads its
        walk's hops (``_flat_leaf_walk``, declared and undeclared) and runs, as
        a filter of the last hop's target set (or of the face an undeclared
        hop's rows offer, ``_UndeclaredHopSet``), over the path left on that
        target. A relation-key
        leaf compares the last hop's key, re-read so the comparison sees only
        rows the hop shows: an ``isnull`` leaf tests the target's primary key
        (a visible row's key is never ``NULL``, so only "no visible related row"
        matches ``True``); a leaf on a forward relation path keeps comparing the
        stored key on the rows that hold it and requires the key to reach a
        visible row (``_LeafChain.key_hop``); a leaf on a to-many path compares
        the target rows' own key column, the column Django's relation lookup
        compares (``_relation_key_value`` reads model-choice values there).
        Every declared hop's target set resolves: a caller derives (or checks)
        the hops first.
        """
        if isinstance(filter_instance, ProjectedChildFilter):
            projection = filter_instance._projection
            hop = type(self)._projection_hop(projection)
            child = self._projection_child(projection.filterset)
            child_filter = child.filters[projection.name]
            inner = child._leaf_chain(child_filter)
            if inner is None:
                return _LeafChain((hop,), child_filter)
            return replace(inner, hops=(hop, *inner.hops))
        walk = type(self)._flat_leaf_walk(filter_instance)
        if walk is None:
            return None
        hops, target_path = walk
        last = hops[-1]
        if target_path:
            return _LeafChain(
                hops,
                self._bound_terminal(filter_instance, last, target_path),
            )
        target_pk = _hop_model(last)._meta.pk
        if filter_instance.lookup_expr == "isnull":
            return _LeafChain(
                hops,
                self._bound_terminal(filter_instance, last, target_pk.name),
            )
        owner_model = _hop_source_model(hops, len(hops) - 1)
        relation = _hop_relation(last)
        if not path_traverses_to_many(owner_model, relation):
            folded = hops[:-1]
            terminal = (
                self._bound_terminal(filter_instance, folded[-1], relation)
                if folded
                else filter_instance
            )
            return _LeafChain(folded, terminal, key_hop=last)
        # The relation's last link names the target column Django's relation lookup
        # compares: the target's primary key, or a single non-key ``to_field``. A
        # GlobalID / raw-key leaf marked for a non-pk ``to_field`` carries the pk.
        relation_field = cast(
            "models.ForeignObject[object, object] | _ManyToManyFieldAny | models.ForeignObjectRel",
            get_model_field(owner_model, relation),
        )
        targets = relation_field.path_infos[-1].target_fields
        key_name, key_attname = target_pk.name, "pk"
        if (
            len(targets) == 1
            and not targets[0].primary_key
            and not getattr(filter_instance, _GLOBALID_RELATION_PK_ATTR, False)
        ):
            key_name, key_attname = targets[0].name, targets[0].attname
        terminal = self._bound_terminal(filter_instance, last, key_name)
        setattr(terminal, _GLOBALID_RELATION_PK_ATTR, False)
        return _LeafChain(hops, terminal, key_attname=key_attname)

    def _reaches_hop(
        self,
        outer: models.QuerySet[_M],
        hop: RelationHop,
        rows: models.QuerySet[models.Model],
    ) -> Exists:
        """Return ``EXISTS`` "the ``outer`` row reaches a row of ``rows`` ``hop`` admits".

        A declared hop admits the rows within its explicit ``queryset=``
        (``_admitted_rows``) and passes through the visible rows of each
        intermediate model its ``field_name`` crosses (``_via_rows``); an
        undeclared hop admits ``rows`` as they are.
        """
        if not hop.declared:
            return _reaches_related(outer, hop.declared_attr, rows)
        related_filter = cast("RelatedFilter", hop.related_obj)
        # A declared hop's owner is the ``FilterSet`` declaring it.
        owner = cast("type[FilterSet]", hop.owner)
        admitted = cast(
            "models.QuerySet[models.Model]",
            _admitted_rows(owner, hop.declared_attr, related_filter, rows),
        )
        via = owner._via_rows(related_filter, self._apply_info, self._hop_visibility(), outer.db)
        return _reaches_related(outer, _bound_field_name(related_filter), admitted, via)

    def _apply_active_leaf(
        self,
        queryset: models.QuerySet[_M],
        filter_instance: Filter,
        value: object,
    ) -> models.QuerySet[_M]:
        """Apply an active leaf walking declared hops as Django answers it over the visible rows.

        The leaf's chain (``_leaf_chain``) runs its terminal over the last hop's
        visible rows, and each hop folds outward with ``_reaches_hop``, the
        correlated ``EXISTS`` every declared branch restricts through, onto the
        previous hop's visible rows, then onto ``queryset``:

        - a positive lookup keeps a parent with a visible chain whose terminal
          matches (the nested twin's answer: ``shelfTopic`` as ``shelf: {topic}``);
        - an ``isnull=True`` lookup also keeps a parent with no visible related
          row at some hop (Django's ``LEFT JOIN`` null extension over the visible
          rows: a ``NULL`` key or a hidden target alike), where the nested twin
          stays existential;
        - an ``exclude=True`` filter keeps the parents its positive twin (the
          same filter with ``exclude`` off) does not keep, negated at the parent
          (Django's exclude across a relation), never the child rows the
          excluding filter keeps.

        A consumer ``method=`` filter is positive whatever its flags: django-filter
        hands its value to the method and applies no lookup of its own. A
        ``NOT EXISTS`` cannot be emptied by a ``NULL`` key the way ``NOT IN`` is.
        """
        using = queryset.db
        # ``_apply_relation_leaf`` reaches here only for a leaf ``_flat_leaf_walk`` reads
        # or a ``ProjectedChildFilter``, which always carries its projection hop.
        # Derived before any target set is read: a hop whose target does not resolve,
        # or has no registered type, raises here (``_branch_visibility_seed``).
        for hop in type(self)._visibility_hops(filter_instance):
            self._hop_visible_rows(hop, using)
        chain = cast("_LeafChain", self._leaf_chain(filter_instance))
        terminal = chain.terminal
        negate = terminal.method is None and terminal.exclude
        if negate:
            terminal = copy.copy(terminal)
            terminal.exclude = False
        value = chain.terminal_value(value)
        null_extends = (
            terminal.method is None and terminal.lookup_expr == "isnull" and value is True
        )
        if not chain.hops:
            key_hop = cast("RelationHop", chain.key_hop)
            if negate:
                inner = self._filter_child_rows(terminal, correlated_inner_root(queryset), value)
                inner = inner.filter(
                    self._reaches_hop(inner, key_hop, self._hop_visible_rows(key_hop, using)),
                )
                return queryset.filter(~Exists(inner))
            # The parent's own rows: the filter's original invocation, consumer
            # ``distinct`` included, as for a leaf walking no hop.
            matched = terminal.filter(queryset, value)
            assert isinstance(matched, models.QuerySet), (
                f"Expected '{type(self).__name__}' filter {terminal.field_name!r} "
                f"to return a QuerySet, but got a {type(matched).__name__} instead."
            )
            return matched.filter(
                self._reaches_hop(matched, key_hop, self._hop_visible_rows(key_hop, using)),
            )
        visible = [self._hop_visible_rows(hop, using) for hop in chain.hops]
        rows = self._filter_child_rows(terminal, visible[-1], value)
        if chain.key_hop is not None:
            rows = rows.filter(
                self._reaches_hop(
                    rows,
                    chain.key_hop,
                    self._hop_visible_rows(chain.key_hop, using),
                ),
            )
        condition = Q()
        for index in range(len(chain.hops) - 1, -1, -1):
            outer = visible[index - 1] if index else queryset
            condition = Q(self._reaches_hop(outer, chain.hops[index], rows))
            if null_extends:
                condition |= ~Q(self._reaches_hop(outer, chain.hops[index], visible[index]))
            if index:
                rows = outer.filter(condition)
        return queryset.filter(~condition if negate else condition)

    def _apply_flat_leaves(self, queryset: models.QuerySet[_M]) -> models.QuerySet[_M]:
        """Apply flat leaves, mirroring ``BaseFilterSet.filter_queryset`` exactly.

        Iterates ``self.form.cleaned_data`` in insertion order (upstream's
        order). A leaf whose ORM path walks a declared ``RelatedFilter`` hop (into a
        target column, or onto the relation's key; ``_flat_leaf_walk``) takes the
        branch path FIRST (``_apply_relation_leaf``): it answers over the rows each
        hop's target visibility and explicit ``queryset=`` admit, so it is never
        routed.
        Otherwise a name is routed through the correlated ``EXISTS`` adapter ONLY
        when its frozen candidate row says so: ``candidate.routable``, the
        BUILD-TIME verdict computed in ``FilterSet.get_filters`` and published in
        the immutable ``ExpansionSnapshot``. That single bit already requires the
        leaf to be an audited generated family on a to-many path with no consumer
        ``method``, the owning class to have overridden none of the package
        generation seams, and the installed ``django-filter`` release to be
        inside the audited optimizer range; see
        ``CandidateFilterMetadata.routable``.

        There is deliberately NO request-time re-verification of the live filter's
        behavior. The optimizer's contract is narrow and stated positively: only
        UNTOUCHED, framework-generated filters from the audited ``django-filter``
        range are rewritten. Every SUPPORTED customization seam -- a declared filter,
        a custom subclass, ``method=``, ``Meta.filter_overrides``, a shadowed
        ``FILTER_DEFAULTS``, an overridden generation hook, an ``__init__`` that
        replaces or mutates ``self.filters`` -- is refused at BUILD time, so it never
        reaches this loop as routable. Process-wide monkeypatching of django-filter's
        own classes is OUT OF CONTRACT: code able to replace ``CharFilter.filter`` can equally
        replace this package's methods, so an in-process signature check cannot
        be a trust boundary, and maintaining one bought complexity without a
        defensible guarantee.

        A non-routable name that walks no declared hop runs the ORIGINAL
        ``self.filters[name].filter(queryset, value)`` byte-for-byte, preserving
        custom methods / consumer ``distinct`` / custom classes and the exact
        upstream ``QuerySet`` return assertion. That is what makes every
        django-filter customization seam fail CLOSED to the outer invocation
        rather than smuggling consumer semantics into the correlated subquery: the
        failure mode is a declined optimization, never a changed result set. For
        an owner-bound expanded leaf (``ProjectedChildFilter``) the original
        invocation is the child filter run inside its own filter set over the
        branch's visible rows, projected back through the relation
        (``_apply_relation_leaf`` too).

        A routed framework-generated to-many leaf is invoked against
        ``correlated_inner_root(queryset)`` through the distinct-suppressing
        helper (``_invoke_suppressing_framework_distinct``) and attached as a
        positive ``Exists`` via ``optimizer/predicates.py::attach_exists``. An
        invocation that returns the inner root BY IDENTITY is upstream's no-op
        (empty-value short circuit, ``_match_none_queryset`` exclude branch,
        ``MultipleChoiceFilter.is_noop``) and attaches nothing -- without this a
        tautological ``EXISTS`` + reserved alias would ride along for every
        inactive to-many candidate.

        Cost boundary (no-op means "no SQL," not "no construction"): a routed
        no-op still builds ``correlated_inner_root(queryset)`` and runs the
        original ``filter()`` BEFORE the ``result is inner_root`` short-circuit
        fires. A request carrying N inactive-but-eligible to-many leaves does N
        inner-root constructions even though the outer queryset ends unchanged
        and NO alias / SQL is attached. The short-circuit is deliberately AFTER
        invocation, not before: the inner root is a pure unevaluated ORM object
        graph that issues NO SQL, and skipping construction earlier would require
        freezing a per-filter contract-identity policy in the generation metadata
        to short-circuit only values known to be identity for THAT filter class
        (a blanket ``EMPTY_VALUES`` skip is wrong -- the package gives
        ``GlobalIDMultipleChoiceFilter`` / ``ListFilter`` ``in: []`` RESTRICTIVE
        match-nothing semantics, which is not a no-op). Measured cost is roughly
        12 microseconds per inactive to-many leaf, all inner-root construction
        and no I/O; a pathological sixteen-inactive-leaf request is about 0.2 ms
        of Python and is dwarfed by the database round-trip of any request that
        actually filters, so the earlier precise policy is not worth the
        construction it would save.

        A restrictive-empty input produces
        ``inner_root.none()`` (NOT identity), which composes as
        ``Exists(none) == False`` with no special case. Negation stays inside the
        original invocation (Django's ``split_exclude`` handles it in the
        subquery); two active leaves are never merged into one inner body, so
        cross-row ``AND`` semantics are preserved.

        A snapshot of ``None`` (a filterset instantiated before its lazy
        ``RelatedFilter`` targets resolve) makes EVERY name a non-candidate, so
        no name is routed; a leaf walking a declared hop still takes the branch
        path.
        """
        snapshot = type(self)._expansion_snapshot()
        candidates: Mapping[str, CandidateFilterMetadata] = (
            snapshot.candidates if snapshot is not None else {}
        )
        cleaned_data: Mapping[str, object] = self.form.cleaned_data
        for name, value in cleaned_data.items():
            candidate = candidates.get(name)
            filter_instance = self.filters[name]
            if type(self)._flat_leaf_walk(filter_instance) is not None:
                queryset = self._apply_relation_leaf(queryset, filter_instance, value)
                continue
            routed = candidate is not None and candidate.routable
            if not routed:
                queryset = filter_instance.filter(queryset, value)
                assert isinstance(queryset, models.QuerySet), (
                    f"Expected '{type(self).__name__}.{name}' to return a QuerySet, "
                    f"but got a {type(queryset).__name__} instead."
                )
                continue
            inner_root = correlated_inner_root(queryset)
            result = self._invoke_suppressing_framework_distinct(
                filter_instance,
                inner_root,
                value,
            )
            assert isinstance(result, models.QuerySet), (
                f"Expected '{type(self).__name__}.{name}' to return a QuerySet, "
                f"but got a {type(result).__name__} instead."
            )
            if result is inner_root:
                continue
            queryset, positive = attach_exists(queryset, result)
            queryset = queryset.filter(positive)
        return queryset

    @override
    def filter_queryset(self, queryset: models.QuerySet[_M]) -> models.QuerySet[_M]:
        """Compose the tree-form ``and`` / ``or`` / ``not`` keys on top of the leaves.

        spec-027 Decision 8 step 8 + Definition-of-done item 4(d). The flat leaf
        clauses are applied by ``self._apply_flat_leaves(queryset)`` -- a
        framework-owned loop that mirrors ``BaseFilterSet.filter_queryset``
        while applying each leaf walking a declared ``RelatedFilter`` hop over the
        rows each hop shows (``_apply_relation_leaf``) and routing eligible
        framework-generated to-many leaves
        through the correlated ``EXISTS`` adapter -- NOT by an inherited
        ``super().filter_queryset(queryset)`` call. This override then composes
        the tree-form ``and`` / ``or`` / ``not`` keys on top via
        ``_evaluate_logic_tree``.

        Tree keys are read off ``self.data`` rather than
        ``self.form.cleaned_data`` because ``django-filter``'s auto-built
        form declares only the leaf-filter fields, so ``cleaned_data``
        drops the ``and`` / ``or`` / ``not`` slots.
        ``_normalize_input`` already emits the wire keys at the top level
        of ``self.data``.

        Per-branch composition uses ``Q(pk__in=child_qs.values("pk"))``
        against a sibling ``cls(data=child_data, queryset=queryset)``
        instantiation. The sibling reuses the parent's already
        visibility-scoped and ``RelatedFilter``-constrained queryset, so
        the visibility-before-filter ordering carries through to every recursive
        level by construction.
        """
        # Framework-owned flat-leaf applicator. Replaces the wholesale
        # ``super().filter_queryset(queryset)`` delegation with a loop mirroring
        # ``BaseFilterSet.filter_queryset`` EXACTLY, applying each leaf that walks
        # a declared ``RelatedFilter`` hop through the branch restriction and
        # routing eligible framework-generated to-many leaves through the
        # row-preserving correlated-EXISTS primitive (``optimizer/predicates.py``)
        # instead of the JOIN + global ``DISTINCT`` idiom.
        #
        # Multiset contract (why the applicator is a selection, not a
        # normalization boundary): framework-generated relational predicates
        # behave as SQL selections over the queryset they receive -- each
        # root-row OCCURRENCE is retained exactly once or removed, never
        # multiplied, and consumer duplicates arising from ``get_queryset`` /
        # annotations / joins / earlier custom filters are never collapsed.
        # Consumer ordering and any explicit consumer ``distinct()`` are
        # preserved (GOAL.md: cooperate with consumer-shaped querysets). The
        # framework-added GLOBAL ``distinct()`` is what the eligible branch
        # drops, not consumer state.
        qs = self._apply_flat_leaves(queryset)
        # ``_logic_depth`` is stashed on instances built by
        # ``_q_for_branch``; for the top-level instance (constructed by
        # ``apply_sync`` / ``apply_async``) it is unset and the counter
        # starts at 0. ``_apply_info`` is stashed the same way so nested
        # branches can re-derive their ``RelatedFilter`` visibility +
        # constraints; it is ``None`` for
        # instances built outside the apply pipeline, which carry no
        # related branches to re-derive. ``_nested_qs_by_branch_id`` is
        # populated only under ``apply_async``; when present, every nested
        # ``child_input`` already carries an awaited visibility map keyed by
        # ``id(child_input)`` so ``_q_for_branch`` can skip the sync derive
        # that would otherwise raise ``SyncMisuseError`` on an async-only
        # target ``get_queryset``. The hop visibility map is shared with every
        # sibling the logic tree builds (one map per request).
        depth = getattr(self, "_logic_depth", 0)
        info = getattr(self, "_apply_info", None)
        nested_map = getattr(self, "_nested_qs_by_branch_id", None)
        q = type(self)._evaluate_logic_tree(
            qs,
            self.data or {},
            request=self.request,
            info=info,
            _depth=depth,
            _nested_qs_by_branch_id=nested_map,
            _flat_hop_visibility=self._hop_visibility(),
        )
        return qs.filter(q)

    @classmethod
    def _evaluate_logic_tree(
        cls,
        queryset: models.QuerySet[models.Model],
        tree_data: object,
        request: object = None,
        info: object = None,
        *,
        _depth: int = 0,
        _nested_qs_by_branch_id: dict[int, dict[str, models.QuerySet[models.Model]]] | None = None,
        _flat_hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]]
        | None = None,
    ) -> models.Q:
        """Build the ``Q`` expression for logical operator branches.

        Recursion terminates naturally when ``tree_data`` carries no
        logical keys -- an empty ``Q()`` is the identity element for
        ``qs.filter(...)`` and the no-op for an empty sub-branch list.
        ``_depth`` is the recursion-cap counter shared with
        ``_q_for_branch``; both helpers cap at ``cls._MAX_LOGIC_DEPTH``.
        ``_nested_qs_by_branch_id`` carries the pre-derived async
        visibility maps produced by ``_collect_nested_visibility_querysets_async``
        (None on the sync path); ``_flat_hop_visibility`` is the request-wide hop
        visibility map every sibling's flat relation leaves read
        (``FilterSet._flat_hop_visibility``).

        Inactive children (``None`` / ``strawberry.UNSET``) inside sequence
        lists -- and an inactive single-element value -- are skipped, matching
        ``_collect_nested_visibility_querysets_async``. Without that skip an
        inactive ``or`` arm materializes as ``pk__in=<full qs>`` (match-all)
        and silently widens past every real sibling arm.
        """
        q = models.Q()
        if not isinstance(tree_data, dict) or not tree_data:
            return q
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()

        for op, children in cls._iter_logic_branches(tree_data):
            branch_qs = [
                cls._q_for_branch(
                    queryset,
                    child_input,
                    request=request,
                    info=info,
                    _depth=_depth + 1,
                    _nested_qs_by_branch_id=_nested_qs_by_branch_id,
                    _flat_hop_visibility=_flat_hop_visibility,
                )
                for child_input in children
            ]
            q &= op.compose(branch_qs)

        return q

    @classmethod
    def _q_for_branch(
        cls,
        queryset: models.QuerySet[models.Model],
        child_input: object,
        request: object = None,
        info: object = None,
        *,
        _depth: int = 0,
        _nested_qs_by_branch_id: dict[int, dict[str, models.QuerySet[models.Model]]] | None = None,
        _flat_hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]]
        | None = None,
    ) -> models.Q:
        """Materialize one nested-branch input into a ``pk__in`` ``Q``.

        Re-applies this branch's ``RelatedFilter`` visibility scoping +
        constraints exactly as ``apply_sync`` does at the top level, THEN
        normalizes the Strawberry input and builds a sibling ``FilterSet``
        instance against the constrained ``queryset``. Reading ``.qs``
        triggers ``BaseFilterSet``'s leaf-clause path against the child's
        normalized data AND re-enters this override for any deeper
        ``and`` / ``or`` / ``not`` keys the branch carries.

        The related re-application is essential: ``_normalize_input``
        STRIPS related-branch keys from the child's form data (the parent
        form cannot validate the nested-dict shape), so without deriving
        and applying them here a related branch nested inside a logical
        clause -- ``or: [{shelves: {code: {iContains: "X"}}}]`` -- would
        silently widen to the whole parent queryset. Under ``apply_async`` the nested visibility map is
        pre-derived via ``_collect_nested_visibility_querysets_async`` and
        threaded through ``_nested_qs_by_branch_id`` keyed by
        ``id(child_input)``; that stash is consumed by ``.get(id(...))``
        here so an async-only target ``get_queryset`` does not raise
        ``SyncMisuseError`` mid-``.qs``. Under ``apply_sync`` the stash is
        ``None`` and the helper falls back to the sync derive, which keeps
        the documented sync-misuse error on the pure-sync path.

        ``_depth`` and ``_apply_info`` are stashed on the sibling instance
        so ``filter_queryset`` can carry the recursion counter and the
        resolver ``info`` across django-filter's ``.qs`` machinery into the
        next ``_evaluate_logic_tree`` call. Without this hand-off the depth
        counter would reset at every nesting level and deeper branches
        would lose the ``info`` needed to re-derive their related
        visibility (the recursion path crosses through django-filter's
        ``BaseFilterSet`` which we do not own and cannot pass kwargs
        through). ``_nested_qs_by_branch_id`` is stashed on the sibling
        too so a deeper ``_q_for_branch`` call (via the sibling's own
        ``filter_queryset`` -> ``_evaluate_logic_tree``) can keep
        consulting the pre-derived map, and so is ``_flat_hop_visibility``, so
        the sibling's flat relation leaves read (and, under ``apply_async``, find
        pre-derived) the same hop visibility as the top level.

        Perf note: constructing the
        sibling ``cls(...)`` per branch triggers django-filter's
        ``BaseFilterSet.__init__`` deepcopy of ``base_filters``, so cost
        scales with branches x filters. This is correctness-neutral and
        bounded by ``_MAX_LOGIC_DEPTH``; not optimized here because doing so
        means reaching into upstream's per-instance copy semantics. Profile
        before optimizing if a deeply-nested query ever shows up hot.
        """
        # Defensive identity for direct callers: an inactive child must not
        # materialize as ``pk__in=<full queryset>`` (match-all). ``_evaluate_logic_tree``
        # already skips inactive arms; returning empty ``Q()`` here keeps AND/OR
        # identity if this helper is reached alone.
        if is_inactive_value(child_input, unset_sentinel=UNSET):
            return models.Q()
        if _nested_qs_by_branch_id is not None:
            child_qs_by_branch = _nested_qs_by_branch_id.get(id(child_input))
            if child_qs_by_branch is None:
                # Defensive fallback: the pre-pass walks every reachable
                # logical branch, but a consumer who short-circuits past
                # the walker (e.g. by calling ``_q_for_branch`` directly)
                # still gets a correct result via the sync derive. Apply
                # the same async/sync caveat the docstring names.
                child_qs_by_branch = cls._derive_related_visibility_querysets_sync(
                    child_input,
                    info,
                    parent_db=queryset.db,
                    _depth=_depth,
                )
        else:
            child_qs_by_branch = cls._derive_related_visibility_querysets_sync(
                child_input,
                info,
                parent_db=queryset.db,
                _depth=_depth,
            )
        if _flat_hop_visibility is None:
            _flat_hop_visibility = {}
        constrained = cls._apply_related_constraints(
            child_input,
            queryset,
            child_qs_by_branch,
            info,
            _flat_hop_visibility,
        )
        child_data = cls._normalize_input(child_input)
        # basedpyright: typeshed narrows ``request`` to ``HttpRequest``; upstream only stores it,
        # and the context request need not be a Django one. It rejects ``object`` for
        # ``HttpRequest | None``
        child_set = cls(
            data=child_data,
            queryset=constrained,
            request=request,  # pyright: ignore[reportArgumentType]
        )
        child_set._logic_depth = _depth
        child_set._apply_info = info
        child_set._nested_qs_by_branch_id = _nested_qs_by_branch_id
        child_set._flat_hop_visibility = _flat_hop_visibility
        cls._validate_form_or_raise(child_set)
        return models.Q(pk__in=child_set.qs.values("pk"))

    @classmethod
    def _apply_related_constraints(
        cls,
        input_value: object,
        parent_qs: models.QuerySet[_M],
        child_qs_by_branch: Mapping[str, models.QuerySet[models.Model]],
        info: object,
        hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]],
    ) -> models.QuerySet[_M]:
        """Constrain `parent_qs` by each active branch's intersected child qs.

        The explicit `RelatedFilter(queryset=...)`
        constraint AND-intersects with the visibility-scoped child qs
        from step 3, then the parent keeps the rows reaching an intersected
        child row through one correlated ``EXISTS`` per active branch
        (``_restrict_through_branch``, the restriction a flat leaf walking
        the branch applies too), passing through only the visible rows of each
        intermediate model a multi-relation branch crosses (``_via_rows``, read
        from and stored in the request-wide ``hop_visibility`` map). Inactive
        branches do not constrain the parent.
        """
        constrained = parent_qs
        for field_name, declaration, _ in cls._iter_active_related_branches(input_value):
            # ``child_qs_by_branch`` is keyed by the declared name (see
            # ``_derive_related_visibility_querysets_*``); ``related_filters`` holds
            # only the ``RelatedFilter`` declarations the metaclass collected
            # (``sets_mixins.py::collect_related_declarations``).
            constrained = _restrict_through_branch(
                constrained,
                cls,
                field_name,
                cast("RelatedFilter", declaration),
                child_qs_by_branch.get(field_name),
                cls._via_rows(
                    cast("RelatedFilter", declaration),
                    info,
                    hop_visibility,
                    parent_qs.db,
                ),
            )
        return constrained

    @classmethod
    def _apply_common_prelude(
        cls,
        input_value: object,
        queryset: models.QuerySet[_M],
        info: object,
        child_qs_by_branch: Mapping[str, models.QuerySet[models.Model]],
        hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]],
    ) -> tuple[dict[str, object], object, models.QuerySet[_M]]:
        """Return the form data, request and constrained queryset shared by both apply paths.

        Captures the verbatim normalize / request / related-constraints
        sequence both apply paths run identically, before the filterset is
        built by ``_apply_common_finalize``. ``hop_visibility`` is the
        request-wide hop visibility map the filter set instance reads next.
        """
        data = cls._normalize_input(input_value)
        request = cls._request_from_info(info)
        constrained = cls._apply_related_constraints(
            input_value,
            queryset,
            child_qs_by_branch,
            info,
            hop_visibility,
        )
        return data, request, constrained

    @classmethod
    def _apply_common_finalize(
        cls,
        input_value: object,
        constrained: models.QuerySet[_M],
        data: dict[str, object],
        request: object,
        info: object,
        *,
        nested_qs_by_branch_id: dict[int, dict[str, models.QuerySet[models.Model]]] | None = None,
        flat_hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]]
        | None = None,
        run_permissions: bool = True,
    ) -> models.QuerySet[_M]:
        """Build the filterset, then run the perm check + form validate + lazy ``.qs`` read.

        The filterset is built over ``constrained`` with ``info`` stashed as
        ``_apply_info`` and the async-only pre-derived
        ``nested_qs_by_branch_id`` map and ``flat_hop_visibility`` map (both
        ``None`` on the sync path) stashed as ``_nested_qs_by_branch_id`` and
        ``_flat_hop_visibility``. Its ``.qs`` is
        ``filter_queryset(constrained.all())`` (django-filter's
        ``BaseFilterSet.qs``), a filtered clone over ``constrained``'s own
        model, so the result keeps the model of the queryset passed in.

        Sync ``apply_sync`` calls this directly; async ``apply_async``
        wraps the single call in ``run_in_one_sync_boundary`` (the neutral
        ``sync_to_async(thread_sensitive=True)`` owner in
        ``utils/querysets.py``) so a consumer's filterset constructor /
        ``check_*_permission`` hook / custom ``method=`` filter body /
        leaf-clause ORM evaluation does not block the event loop.

        ``run_permissions=False`` skips the ``_run_permission_checks`` pass.
        The related-visibility derivation invokes the child filterset's
        ``apply_*`` purely to compute the child's filtered queryset; the
        child's gates are already fired ONCE by the top-level pass that
        recurses into every active related branch, so re-running them here
        would double-fire nested gates (compounding with nesting depth).
        Form validation still runs so a malformed nested clause still raises
        ``FILTER_INVALID``.
        """
        # basedpyright: typeshed narrows ``request`` to ``HttpRequest`` (see ``_q_for_branch``); it
        # rejects ``object`` for ``HttpRequest | None``
        filterset_instance = cls(
            data=data,
            queryset=constrained,
            request=request,  # pyright: ignore[reportArgumentType]
        )
        filterset_instance._apply_info = info
        filterset_instance._nested_qs_by_branch_id = nested_qs_by_branch_id
        filterset_instance._flat_hop_visibility = flat_hop_visibility
        if run_permissions:
            cls._run_permission_checks(input_value, request)
        cls._validate_form_or_raise(filterset_instance)
        return filterset_instance.qs

    @classmethod
    def apply_sync(
        cls,
        input_value: object,
        queryset: models.QuerySet[_M],
        info: object,
        *,
        run_permissions: bool = True,
        _depth: int = 0,
    ) -> models.QuerySet[_M]:
        """Sync resolver entry point (Decision 8).

        Steps run in the pinned order: derive visibility
        querysets, resolve the request, apply related constraints
        BEFORE constructing the filterset (so the constraints land in
        `self.queryset` and propagate through to `.qs`), then permission
        check, form validate, and return the lazy queryset.

        ``run_permissions`` defaults to ``True`` for every consumer entry
        point; the related-visibility derivation passes ``False`` so a nested
        child filterset's gates are fired only by the single top-level
        ``_run_permission_checks`` pass (see ``_apply_common_finalize``).

        ``_depth`` is the internal related-recursion budget: the visibility
        derivation re-enters this method (``run_permissions=False``) once per
        related hop, so a self-referential ``RelatedFilter`` is capped here with
        a typed ``ConfigurationError`` instead of a raw ``RecursionError``
        (report Defect 5). The derivation runs FIRST, so this is the earliest
        point the runaway recursion surfaces. The parent queryset's database
        alias (``queryset.db``) is threaded into the derivation so each child
        visibility hook sees the parent's shard (report Defect 3).
        """
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()
        child_qs_by_branch = cls._derive_related_visibility_querysets_sync(
            input_value,
            info,
            parent_db=queryset.db,
            _depth=_depth,
        )
        hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]] = {}
        data, request, constrained = cls._apply_common_prelude(
            input_value,
            queryset,
            info,
            child_qs_by_branch,
            hop_visibility,
        )
        return cls._apply_common_finalize(
            input_value,
            constrained,
            data,
            request,
            info,
            flat_hop_visibility=hop_visibility,
            run_permissions=run_permissions,
        )

    @classmethod
    async def apply_async(
        cls,
        input_value: object,
        queryset: models.QuerySet[_M],
        info: object,
        *,
        run_permissions: bool = True,
        _depth: int = 0,
    ) -> models.QuerySet[_M]:
        """Async sibling of `apply_sync` awaiting every blocking step.

        Steps:
            1. Await the top-level ``_derive_related_visibility_querysets_async``
               so every active ``RelatedFilter`` branch's target
               ``get_queryset`` runs on the async path.
            2. Await, via ``_derive_flat_hop_visibility_async``, the target
               visibility of every declared hop a supplied top-level flat
               relation leaf walks, into the request-wide hop map.
            3. Pre-walk every ``and`` / ``or`` / ``not`` arm via
               ``_collect_nested_visibility_querysets_async`` so nested
               branches whose target type's ``get_queryset`` is async-only
               get their visibility maps awaited BEFORE the sync ``.qs``
               read fans into ``_q_for_branch``, and each arm's flat-leaf hops
               land in the same hop map. Without this step,
               ``_q_for_branch``'s sync derive (or a flat leaf's first-use
               derive) would raise ``SyncMisuseError`` mid-``.qs``.
            4. Normalize the input and apply the related constraints via
               ``_apply_common_prelude`` (shared with ``apply_sync``).
            5. Route ``_apply_common_finalize`` (filterset build with the
               nested-visibility and hop-visibility maps stashed - the
               async-only step with no sync analog - then perm check + form
               validate + ``.qs`` read)
               through ``run_in_one_sync_boundary`` so a consumer's
               ``check_*_permission`` hook that performs a blocking ORM read
               does not block the event loop.

        ``run_permissions`` defaults to ``True`` for consumer entry points;
        the related-visibility derivation passes ``False`` so a nested child
        filterset's gates fire only once, via the top-level pass (see
        ``_apply_common_finalize`` / ``_derive_related_visibility_querysets_sync``).

        ``_depth`` (related-recursion cap, report Defect 5) and the parent
        ``queryset.db`` alias (report Defect 3) thread through the top-level
        derivations and the arm pre-walk exactly as in ``apply_sync``.
        """
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()
        child_qs_by_branch = await cls._derive_related_visibility_querysets_async(
            input_value,
            info,
            parent_db=queryset.db,
            _depth=_depth,
        )
        flat_hop_visibility: dict[tuple[object, str | None], models.QuerySet[models.Model]] = {}
        await cls._derive_flat_hop_visibility_async(
            input_value,
            info,
            flat_hop_visibility,
            parent_db=queryset.db,
        )
        nested_qs_by_branch_id = await cls._collect_nested_visibility_querysets_async(
            input_value,
            info,
            parent_db=queryset.db,
            _depth=_depth,
            flat_hop_visibility=flat_hop_visibility,
        )
        data, request, constrained = cls._apply_common_prelude(
            input_value,
            queryset,
            info,
            child_qs_by_branch,
            flat_hop_visibility,
        )
        return await run_in_one_sync_boundary(
            cls._apply_common_finalize,
            input_value,
            constrained,
            data,
            request,
            info,
            nested_qs_by_branch_id=nested_qs_by_branch_id,
            flat_hop_visibility=flat_hop_visibility,
            run_permissions=run_permissions,
        )

    @classmethod
    def apply(
        cls,
        input_value: object,
        queryset: models.QuerySet[_M],
        info: object,
    ) -> models.QuerySet[_M]:
        """Thin dispatcher - picks `apply_sync` and translates sync-misuse.

        Decision 8 - catches the typed ``SyncMisuseError``
        raised by ``apply_type_visibility_sync`` and rethrows as
        ``RuntimeError`` with the actionable "use apply_async instead"
        message consumers can match on. Class-based dispatch, not
        substring-matching against a constant string.
        """
        try:
            return cls.apply_sync(input_value, queryset, info)
        except SyncMisuseError as exc:
            # ``from exc`` already records the original ``SyncMisuseError``
            # on ``__cause__``; standard traceback machinery surfaces it.
            # Avoid duplicating the cause's ``str()`` in the message here
            # (the cause prints once via the chain, twice if both included).
            raise RuntimeError(
                "FilterSet.apply called against async get_queryset; use apply_async instead.",
            ) from exc
