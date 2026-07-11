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
mechanics are single-sited here (the 0.0.9 DRY pass, ``docs/feedback.md``
Major 1).

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
        return list(input_value.items())
    dataclass_fields = getattr(input_value, "__dataclass_fields__", None)
    if dataclass_fields is None:
        return None
    return [(name, getattr(input_value, name)) for name in dataclass_fields]


def input_field_value(input_value: Any, name: str) -> Any:
    """Read ONE field off a dict-or-dataclass input; ``None`` when absent (DRY review C6).

    The single-field sibling of ``iter_input_items``: the dict-vs-dataclass
    sniff (``.get`` vs ``getattr``) lives in exactly one module - this one,
    whose charter is the input-shape traversal primitives - so a caller that
    needs one branch value (``utils/permissions.py::extract_branch_value``)
    composes this with ``is_inactive_value`` instead of re-spelling the sniff.
    """
    if isinstance(input_value, dict):
        return input_value.get(name)
    return getattr(input_value, name, None)


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
    if is_inactive_value(input_value, unset_sentinel=config.unset_sentinel):
        return
    if config.handle_top_level_list and isinstance(input_value, list):
        for element in input_value:
            yield from iter_active_fields(set_cls, element, config)
        return
    items = iter_input_items(input_value)
    if items is None:
        return
    related = getattr(set_cls, config.related_attr, {}) or {}
    for python_attr, raw_value in items:
        if is_inactive_value(raw_value, unset_sentinel=config.unset_sentinel):
            continue
        spec = config.field_specs.get((set_cls, python_attr))
        if python_attr in config.logic_keys:
            yield ActiveField(python_attr, raw_value, spec, LOGIC)
        elif python_attr in related:
            yield ActiveField(python_attr, raw_value, spec, RELATED, related[python_attr])
        else:
            yield ActiveField(python_attr, raw_value, spec, LEAF)
