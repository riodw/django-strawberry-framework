"""Set-input traversal substrate shared by the FilterSet and OrderSet families.

FilterSet and OrderSet independently grew the SAME runtime walk over a generated
Strawberry input value: detect dict vs input-dataclass shape, decide which values
are active (``None`` / ``strawberry.UNSET``), resolve the per-field ``FieldSpec``
provenance, and classify each supplied top-level field as a leaf, a related
branch, or a logical operator. That classification was spelled inline at four
correctness-sensitive call sites -- the filter normalizer
(``filters/sets.py::FilterSet._normalize_input``), the order normalizer
(``orders/inputs.py::normalize_input_value``), and the two permission walkers
(``utils/permissions.py::active_permission_field_paths`` /
``active_related_branches``). A drift between any two copies in the active-input
decision is a real bug class -- a filter applied without its permission gate, a
related visibility hook skipped, work done on inactive input -- so the neutral
mechanics are single-sited here.

This module owns the *traversal mechanics* only; the family-specific *leaf
semantics* stay at the call sites:

* the filter normalizer keeps its per-field operator-bag iteration and the
  ``RangeFilter`` positional patch;
* the order normalizer keeps its ``Ordering`` direction handling and its
  recursion into child ordersets;
* the permission walkers keep the per-class ``check_*`` dedup and the
  parent-vs-child double dispatch.

Each consumer drives ``iter_active_fields`` with a ``SetInputTraversal`` config
and filters the yielded ``ActiveField`` records by ``kind``. It depends on no
family package (it operates on a duck-typed ``set_cls`` plus a config), so both
families import it without a cycle -- same contract as ``utils/permissions.py``
/ ``utils/connections.py`` / ``utils/inputs.py``.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from ..exceptions import ConfigurationError, _safe_type_name

# Default maximum traversal depth across set input graphs (logical operators and related branches).
# Sets with custom depth requirements (e.g. FilterSet._MAX_LOGIC_DEPTH) can override the class-level
# limit, while traversal algorithms (e.g. permission checks in utils/permissions.py) fall back to this
# neutral default.
DEFAULT_SET_INPUT_TRAVERSAL_DEPTH = 8

# ``ActiveField.kind`` markers. A supplied top-level field is exactly one of:
# a logical operator key (filter ``and_`` / ``or_`` / ``not_``), a related
# branch (a ``RelatedFilter`` / ``RelatedOrder`` declaration), or a leaf. The
# three are mutually exclusive -- the logical-operator attrs are never related
# names and related names are never logical -- so classification order between
# the logic and related checks is immaterial; ``iter_active_fields`` tests logic
# first to mirror ``FilterSet._normalize_input``'s original branch order.
LOGIC = "logic"
RELATED = "related"
LEAF = "leaf"


def _field_name(value: Any, *, input_value: Any) -> str:
    """Normalize one input key or reject it before lookup/permission dispatch."""
    if not isinstance(value, str):
        raise ConfigurationError(
            "Set input field names must be strings; received an invalid field name in an "
            f"input of type {_safe_type_name(input_value)}.",
        )
    return str.__str__(value)


def _walk_error(input_value: Any, detail: str) -> ConfigurationError:
    """Build a typed, safe traversal error for malformed consumer input."""
    return ConfigurationError(
        f"Could not traverse set input of type {_safe_type_name(input_value)}: {detail}.",
    )


def iter_input_items(input_value: Any) -> list[tuple[str, Any]] | None:
    """Walk a dict or Strawberry-input dataclass into ``(name, value)`` pairs.

    Returns ``None`` when ``input_value`` is neither a dict nor an object
    carrying ``__dataclass_fields__`` (the Strawberry-input sniff used
    package-wide -- faster than ``dataclasses.is_dataclass`` and matching the
    shape upstream uses to introspect input classes). Returns ``[]`` for a
    walkable-but-empty input.

    Single-sited here as the lowest-level traversal primitive; re-exported from
    ``utils/permissions.py`` so the existing
    ``from ..utils.permissions import iter_input_items`` consumers keep working.
    """
    if isinstance(input_value, dict):
        pairs = dict.items(input_value)
        return [(_field_name(name, input_value=input_value), value) for name, value in pairs]
    try:
        dataclass_fields = getattr(input_value, "__dataclass_fields__", None)
    except BaseException as exc:
        raise _walk_error(input_value, "its dataclass metadata could not be read") from exc
    if dataclass_fields is None:
        return None
    if not isinstance(dataclass_fields, Mapping):
        raise ConfigurationError(
            "Could not traverse set input of type "
            f"{_safe_type_name(input_value)}: its dataclass metadata is not a mapping.",
        )
    try:
        names = tuple(dataclass_fields)
    except BaseException as exc:
        raise _walk_error(input_value, "its dataclass fields could not be enumerated") from exc
    items: list[tuple[str, Any]] = []
    for name in names:
        field_name = _field_name(name, input_value=input_value)
        try:
            value = getattr(input_value, field_name)
        except BaseException as exc:
            raise _walk_error(input_value, "a dataclass field value could not be read") from exc
        items.append((field_name, value))
    return items


def input_field_value(input_value: Any, name: str) -> Any:
    """Read ONE field off a dict-or-dataclass input; ``None`` when absent.

    The single-field sibling of ``iter_input_items``: the dict-vs-dataclass
    sniff (``.get`` vs ``getattr``) lives in exactly one module - this one,
    whose charter is the input-shape traversal primitives - so a caller that
    needs one branch value (``utils/permissions.py::extract_branch_value``)
    composes this with ``is_inactive_value`` instead of re-spelling the sniff.
    """
    field_name = _field_name(name, input_value=input_value)
    if isinstance(input_value, dict):
        return dict.get(input_value, field_name)
    try:
        return getattr(input_value, field_name, None)
    except BaseException as exc:
        raise _walk_error(input_value, "a field value could not be read") from exc


def is_inactive_value(value: Any, *, unset_sentinel: Any = None) -> bool:
    """Return ``True`` when ``value`` should be treated as "not supplied".

    The single active-input rule shared by every traversal surface: a value is
    inactive when it is ``None`` or the family's ``unset_sentinel``. The filter
    side passes ``unset_sentinel=strawberry.UNSET`` (Strawberry input dataclasses
    default unsupplied fields to ``UNSET``); the order side leaves it ``None``
    (order inputs default unsupplied fields to ``None``), which makes the
    sentinel arm a harmless ``value is None`` repeat. Defined once so the
    ``UNSET`` / ``None`` decision cannot drift between the normalizers, the
    permission walkers, and ``extract_branch_value``.
    """
    return value is None or value is unset_sentinel


@dataclass(frozen=True)
class SetInputTraversal:
    """Family-specific configuration for ``iter_active_fields``.

    Carries everything the neutral walker needs to classify a supplied field
    without knowing filter / order leaf semantics:

    * ``field_specs`` -- the per-``(set_cls, python_attr)`` provenance map
      (``filters/inputs.py::_field_specs`` / ``orders/inputs.py::_field_specs``);
      consulted for every field so leaf and related consumers can read
      ``django_source_path`` off the yielded record.
    * ``related_attr`` -- the per-class related-collection attribute name
      (``"related_filters"`` / ``"related_orders"``); read off ``set_cls`` to
      recognize related branches.
    * ``logic_keys`` -- the python-attr tokens of the logical operators (filter
      ``and_`` / ``or_`` / ``not_``); empty for the order side, which has no
      logical operator bag.
    * ``unset_sentinel`` -- the family's "not supplied" sentinel (``UNSET`` for
      filters, ``None`` for orders); threaded into ``is_inactive_value``.
    * ``handle_top_level_list`` -- the order side's top-level ``list[<T>]`` input
      shape; when set, a list ``input_value`` is flattened element-by-element.
    """

    field_specs: Mapping[Any, Any]
    related_attr: str
    logic_keys: frozenset[str] = frozenset()
    unset_sentinel: Any = None
    handle_top_level_list: bool = False


@dataclass(frozen=True)
class ActiveField:
    """One supplied, active top-level input field, classified.

    ``spec`` is the ``FieldSpec`` from ``config.field_specs`` (``None`` when the
    map has no entry -- a leaf consumer falls back to its own form-key rule, an
    order consumer skips defensively). ``related_obj`` is the declared
    ``RelatedFilter`` / ``RelatedOrder`` instance for a ``RELATED`` field and
    ``None`` otherwise.
    """

    python_attr: str
    raw_value: Any
    spec: Any | None
    kind: str
    related_obj: Any = None


def iter_active_fields(
    set_cls: type,
    input_value: Any,
    config: SetInputTraversal,
) -> Iterator[ActiveField]:
    """Yield one ``ActiveField`` per supplied, active top-level field of ``input_value``.

    Owns the mechanics every consumer previously re-spelled:

    * the ``None`` / ``unset_sentinel`` inactive-value skip (via
      ``is_inactive_value``), applied to the whole input and to each field;
    * the dict-vs-dataclass walk (via ``iter_input_items`` -- a non-walkable
      input yields nothing);
    * the order side's top-level ``list[<T>]`` flattening
      (``handle_top_level_list``), recursing per element so each element's
      fields stream out in order;
    * the per-field ``FieldSpec`` lookup;
    * the leaf / related / logic classification.

    It does NOT recurse into child set inputs -- a ``RELATED`` field carries its
    raw child value on the record and the consumer recurses with the
    family-appropriate entry point (the order normalizer re-enters
    ``normalize_input_value``; the filter normalizer strips the branch and lets
    ``_apply_related_constraints`` own it). Leaf shape (operator bags, ranges,
    directions) is the consumer's business too; this walker only marks the kind.
    """
    try:
        unset_sentinel = config.unset_sentinel
        handle_top_level_list = config.handle_top_level_list
    except BaseException as exc:
        raise _walk_error(input_value, "the traversal configuration could not be read") from exc
    if is_inactive_value(input_value, unset_sentinel=unset_sentinel):
        return
    if handle_top_level_list and isinstance(input_value, list):
        elements = list.__iter__(input_value)
        for element in elements:
            if is_inactive_value(element, unset_sentinel=unset_sentinel):
                continue
            if isinstance(element, list) or iter_input_items(element) is None:
                raise ConfigurationError(
                    "Order input list elements must be mapping or dataclass values; "
                    f"received {_safe_type_name(element)}.",
                )
            yield from iter_active_fields(set_cls, element, config)
        return
    items = iter_input_items(input_value)
    if items is None:
        return
    try:
        related = getattr(set_cls, config.related_attr, {})
    except BaseException as exc:
        raise _walk_error(input_value, "the related-field declarations could not be read") from exc
    if related is None:
        related = {}
    if not isinstance(related, Mapping):
        raise ConfigurationError(
            "Could not traverse set input of type "
            f"{_safe_type_name(input_value)}: related-field declarations are not a mapping.",
        )
    for python_attr, raw_value in items:
        if is_inactive_value(raw_value, unset_sentinel=unset_sentinel):
            continue
        try:
            spec = config.field_specs.get((set_cls, python_attr))
            is_logic = python_attr in config.logic_keys
        except BaseException as exc:
            raise _walk_error(input_value, "field provenance could not be resolved") from exc
        if is_logic:
            yield ActiveField(python_attr, raw_value, spec, LOGIC)
        else:
            try:
                is_related = python_attr in related
            except BaseException as exc:
                raise _walk_error(
                    input_value,
                    "related-field declarations could not be checked",
                ) from exc
            if not is_related:
                yield ActiveField(python_attr, raw_value, spec, LEAF)
                continue
            try:
                related_obj = related[python_attr]
            except BaseException as exc:
                raise _walk_error(
                    input_value,
                    "a related-field declaration could not be read",
                ) from exc
            yield ActiveField(python_attr, raw_value, spec, RELATED, related_obj)
