"""The ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases + ``Meta`` validation + bind (Slice 2).

The form-mutation write surface, riding the ``036`` mutation seams
(``mutations/sets.py``). Two bases (spec-038 Decision 6):

- ``DjangoModelFormMutation`` - subclasses ``DjangoMutation`` and overrides the
  seams (``_resolve_model`` -> ``Meta.form_class._meta.model``, ``_validate_meta``
  -> the ``ModelForm`` matrix, ``build_input`` -> the ``forms/inputs.py``
  generator, ``input_type_name`` / ``input_module_path`` -> the form-input
  namespace, ``resolve_*`` -> the Slice-3 form pipeline). It rides the
  ``DjangoMutation`` metaclass + declaration registry + ``bind_mutations()``
  unchanged, so a ``ModelForm`` mutation binds its model-backed ``<Name>Payload``
  (``node`` / ``result`` slot) through the SAME phase-2.5 path as the ``036``
  model mutation.
- ``DjangoFormMutation`` - the model-LESS sibling (a plain ``forms.Form``, no
  model, no ``DjangoType`` object slot). Its OWN metaclass + declaration registry
  (via ``make_declaration_registry``) + ``bind_form_mutations()``: the bind
  materializes its form-derived input + the pinned ``{ ok errors }`` payload
  (Decision 6 - no object slot).

The two ``_validate_meta`` overrides are disjoint matrices (Decision 6 / Decision
10 / spec-038 Slice 2): both require ``Meta.form_class``; the plain base checks
``issubclass(form_class, forms.ModelForm)`` FIRST and rejects it naming
``DjangoModelFormMutation`` (the targeted Edge-case message), then requires a
``forms.Form``, and rejects ANY ``Meta.operation``; the ``ModelForm`` base
requires a ``forms.ModelForm`` and ``Meta.operation in {"create", "update"}``
(``"delete"`` rejected - no form delete pipeline). Field narrowing
(``Meta.fields`` / ``Meta.exclude`` mutual exclusion + fail-loud) reuses the
Slice-1 ``forms/inputs.py::resolve_effective_form_fields`` machinery, never a
re-spelled copy.

**Slice 3 fills the resolver seams + the form-construction hooks.** The
``resolve_sync`` / ``resolve_async`` overrides delegate to the
``forms/resolvers.py`` pipeline; both flavors carry the overridable
``get_form_kwargs`` / ``get_form`` construction hooks (the plain flavor adds
``perform_mutate`` + its own ``check_permission``), the ``get_form_kwargs``
waiver is wired into ``build_input`` (the create-required guard is skipped when a
consumer overrides the construction hook), and the Slice-1 reverse-map
``field_specs`` are stashed at bind (``_input_field_specs``) for the decode.
"""

from __future__ import annotations

from typing import Any

from django import forms

from ..exceptions import ConfigurationError
from ..mutations.inputs import (
    PARTIAL,
    build_payload_type,
    materialize_mutation_input_class,
)
from ..mutations.permissions import _PERMISSION_ASYNC_RECOURSE, DenyAll
from ..mutations.sets import (
    NON_DELETE_OPERATION_INPUT_KIND,
    NON_DELETE_WRITE_OPERATIONS,
    DjangoMutation,
    _hook_overridden,
    _validate_permission_classes,
    _ValidatedMutationMeta,
    build_and_stash_input,
    cached_build_input,
    construction_kwargs,
    make_declaration_registry,
    non_delete_operation_error,
    reject_unknown_meta_keys,
    require_backing_class,
    resolve_backed_model_or_raise,
    resolve_meta_model,
    resolver_seams,
)
from ..utils.inputs import make_shape_build_cache
from ..utils.querysets import reject_async_in_sync_context
from .inputs import (
    FORM,
    build_form_input_class,
    build_form_inputs,
    form_input_type_name,
    get_form_fields,
    guard_create_required_fields,
    guard_partial_required_column_less_fields,
    materialize_form_input_class,
    resolve_effective_form_fields,
)
from .inputs import (
    INPUTS_MODULE_PATH as FORMS_INPUTS_MODULE_PATH,
)

# The form ``Meta``'s allowed-key sets (spec-038 Slice 2 / Decision 6). Disjoint
# from ``036``'s ``_ALLOWED_MUTATION_META_KEYS``: a form ``Meta`` adds
# ``form_class`` and drops ``model`` / ``input_class`` / ``partial_input_class``.
# The ``ModelForm`` flavor keeps ``operation`` (create / update); the plain
# flavor drops it (a model-less mutation has no model operation - Decision 10).
_ALLOWED_MODELFORM_META_KEYS: frozenset[str] = frozenset(
    {
        "form_class",
        "operation",
        "fields",
        "exclude",
        "permission_classes",
    },
)
_ALLOWED_PLAIN_FORM_META_KEYS: frozenset[str] = frozenset(
    {
        "form_class",
        "fields",
        "exclude",
        "permission_classes",
    },
)

# The model-less declaration registry for the plain ``DjangoFormMutation`` flavor
# (spec-038 Decision 13). A SECOND, disjoint ledger from the ``036``
# ``_mutation_registry`` - the dedup / post-finalize reject / clear mechanics are
# single-sourced via ``make_declaration_registry``, the storage is separate.
# ``register_form_mutation`` / ``clear_form_mutation_registry`` /
# ``iter_form_mutations`` are the public names ``registry.py`` (the co-clear),
# ``DjangoFormMutationMetaclass``, ``bind_form_mutations``, and the tests
# reference; ``_form_mutation_registry`` is the backing list the tests introspect.
_form_mutation_declaration_registry = make_declaration_registry("DjangoFormMutation")
register_form_mutation = _form_mutation_declaration_registry.register
clear_form_mutation_registry = _form_mutation_declaration_registry.clear
iter_form_mutations = _form_mutation_declaration_registry.iter_
_form_mutation_registry = _form_mutation_declaration_registry.store


# Per-finalize-pass form-input build cache keyed by the form shape identity
# ``(form_class, operation_kind, frozenset(effective field names))`` - the form
# twin of ``mutations/sets.py::_shape_build_cache``. Without it each ``build_input``
# call would build a FRESH ``@strawberry.input`` class object, so two mutations
# over the same form + effective set would hand the materialize ledger two DISTINCT
# same-named classes and trip the AR-M6 collision raise instead of deduping. Caching
# by shape identity makes identical shapes reuse one class object, so
# ``materialize_form_input_class`` dedupes idempotently (the same dedupe contract the
# model flavor's ``_shape_build_cache`` provides). The cache VALUE is the
# ``(input_cls, field_specs)`` pair (spec-038 Slice 3): the Slice-1 reverse-map
# ``field_specs`` MUST survive the dedupe so the bind can stash them on the mutation
# (``_input_field_specs``) for the Slice-3 decode - caching only ``input_cls`` would
# discard the load-bearing P1 reverse map. Cleared at the start of
# ``bind_form_mutations()`` and co-cleared from ``registry.clear()`` so a stale class
# from a prior (failed or re-run) finalize never leaks. Both flavors' ``build_input``
# consult it via ``_cached_build_form_input``.
#
# The ``(cache, clear)`` pair rides the promoted ``utils/inputs.py::make_shape_build_cache``
# plumbing (spec-039 P1.3 / SR-1), the SAME factory the serializer cache uses, so the
# form + serializer + mutation caches share one dict-plus-clear shape while staying
# disjoint (separate dicts, registered + cleared separately). ``clear_form_shape_build_cache``
# is co-cleared from ``registry.clear()`` (a ``registry.clear()``-only reset, NOT a
# pre-bind input clear - it is a per-pass build cache).
_form_shape_build_cache, clear_form_shape_build_cache = make_shape_build_cache()


def _cached_build_form_input(
    form_class: type,
    *,
    operation_kind: str,
    fields: Any,
    exclude: Any,
    guard_required: bool,
) -> tuple[type, list]:
    """Build the operation's form input once per shape; return ``(input_cls, field_specs)``.

    Mirrors ``mutations/sets.py::_materialize_input_for``'s cache-by-shape-identity:
    the first ``build_input`` for a given ``(form_class, operation_kind, effective
    set)`` builds + caches the class; a later identical shape reuses it so the
    materialize ledger dedupes idempotently. The create-required-narrowing guard
    (``guard_create_required_fields``) runs PER declaration, BEFORE the cache
    lookup, so a waiving mutation that materializes a narrowed shape first cannot
    suppress the guard for a later non-waiving mutation reusing the cached shape
    (the cache key excludes ``guard_required`` - spec-038 Decision 7 P2).
    The create-shaped kinds (``CREATE`` / ``FORM``) then route through
    ``build_form_inputs`` (with ``guard_required=False`` - already guarded), and
    only the matching input + its specs are returned (the partial it also builds is
    discarded). ``PARTIAL`` builds the partial directly (never create-required
    guarded - it widens model-backed fields optional).

    Returns the ``(input_cls, field_specs)`` pair so the Slice-1 reverse-map specs
    survive the per-shape dedupe and reach the bind's ``_input_field_specs`` stash
    (spec-038 Slice 3 - the P1 decode reverse map).
    """
    effective = _resolve_effective_form_field_names(form_class, fields=fields, exclude=exclude)

    # Run the create-required-narrowing guard PER declaration, BEFORE the per-shape
    # cache lookup (the load-bearing ordering ``cached_build_input`` enforces): the
    # cache key excludes ``guard_required``, so a waiving mutation
    # (``guard_required=False``, having overridden ``get_form_kwargs`` / ``get_form``)
    # that materializes this shape FIRST must not suppress the guard for a later
    # non-waiving mutation reusing the same cached shape - the guard is tied to the
    # declaration, not the built input shape (spec-038 Decision 7 P2). The create
    # shape rejects ANY dropped required field; the partial (update) shape rejects
    # only dropped required COLUMN-LESS fields (feedback #4) - a model-backed
    # required field is widened optional and reconstructed from the row, but a
    # column-less extra cannot be reconstructed, so dropping it finalizes a form that
    # can never validate.
    def _guard() -> None:
        if not guard_required:
            return
        if operation_kind == PARTIAL:
            guard_partial_required_column_less_fields(form_class, effective)
        else:
            guard_create_required_fields(form_class, effective)

    def _build() -> tuple[type, list]:
        if operation_kind == PARTIAL:
            return build_form_input_class(
                form_class,
                operation_kind=PARTIAL,
                fields=fields,
                exclude=exclude,
            )
        # The guard already ran per-declaration above; ``build_form_inputs`` would
        # otherwise re-run it only on a cache MISS (the bypass this fix closes).
        input_cls, field_specs, _partial_cls, _partial_specs = build_form_inputs(
            form_class,
            operation_kind=operation_kind,
            fields=fields,
            exclude=exclude,
            guard_required=False,
        )
        return input_cls, field_specs

    cache_key = (form_class, operation_kind, frozenset(effective))
    return cached_build_input(
        _form_shape_build_cache,
        cache_key,
        guard=_guard,
        build_fn=_build,
    )


def _resolve_effective_form_field_names(
    form_class: type,
    *,
    fields: Any,
    exclude: Any,
) -> tuple[str, ...]:
    """Return the effective form-field names after ``Meta.fields`` / ``Meta.exclude``.

    Routes through the Slice-1 ``resolve_effective_form_fields`` (the narrowing
    fail-loud machinery: mutual exclusion, bare-string / duplicate rejection,
    unknown-name rejection against ``form_class.base_fields``, empty-set guard) so
    the form ``_validate_meta`` does not re-spell that validation. Returns the
    ordered effective name tuple the snapshot's input-name derivation consults.
    """
    effective = resolve_effective_form_fields(form_class, fields=fields, exclude=exclude)
    return tuple(effective)


def _form_kwargs_overridden(cls: type, base: type) -> bool:
    """Return whether ``cls`` overrides ``get_form_kwargs`` / ``get_form`` (the waiver detection).

    The ``get_form_kwargs`` / ``get_form`` waiver (spec-038 Decision 7 / Slice 3):
    True when the concrete mutation re-defines EITHER construction hook relative to
    its framework ``base``. When a consumer overrides the form-construction hook to
    inject fields the generated input does not carry (a ``user``, a tenant, a
    defaulted column), the create-required-narrowing guard cannot know WHICH fields
    the override supplies, so it trusts the override and waives the guard.

    Rides the promoted ``mutations/sets.py::_hook_overridden(cls, base, name)``
    (spec-039 P2.6) for each hook - the per-hook identity comparison is single-sited
    there (the serializer ``get_serializer_kwargs`` waiver rides the same primitive),
    so the form / serializer waivers cannot drift on how an override is detected.

    **Caveat (deliberate trade-off, spec-038 Decision 7).** The waiver is COARSE: it
    trusts that the override supplies any required field a ``Meta.fields`` /
    ``Meta.exclude`` narrowing dropped, but does NOT verify it. An override taken for
    an UNRELATED reason (scoping a ``ModelChoiceField.queryset``, injecting a
    ``request``) while ALSO narrowing a required field away therefore silently
    re-opens the "schema looks valid but can never validate" hole the guard exists to
    catch. The strict alternative (only waive for fields the override demonstrably
    injects) would reject legitimate kwarg-injection forms, so the spec accepts the
    trust; a consumer who hits the hole keeps the narrowed-away field in the input
    instead.
    """
    return _hook_overridden(cls, base, "get_form_kwargs") or _hook_overridden(
        cls,
        base,
        "get_form",
    )


def _default_get_form_kwargs(
    self: Any,  # noqa: ARG001  # receiver of the instance method; the default ignores it
    info: Any,
    *,
    data: Any,
    files: Any,
    instance: Any = None,
) -> dict[str, Any]:
    """The default ``get_form_kwargs`` body shared by both form bases (spec-038 Decision 8 step 4).

    Returns ``{"data": data, "files": files}`` plus ``"instance": instance`` when
    ``instance`` is non-``None`` (the ``ModelForm`` update path binds the located
    row; create / plain pass ``None`` so no ``instance=`` kwarg is sent). A consumer
    overrides this to inject extra constructor kwargs (a kwarg-requiring form's
    ``user=``), which waives the create-required guard. Single-sourced as a
    module-level function both bases reference so the default body never drifts.
    """
    del info  # the default ignores ``info``; an override may consult it.
    # The "add ``instance`` only on update" clause is single-sited in
    # ``mutations/sets.py::construction_kwargs`` (spec-039 Md7), shared with the
    # serializer ``get_serializer_kwargs`` default.
    return construction_kwargs(data=data, files=files, instance=instance)


def _default_get_form(
    self: Any,
    info: Any,
    *,
    data: Any,
    files: Any,
    instance: Any = None,
) -> Any:
    """The default ``get_form`` body shared by both form bases (spec-038 Decision 8 step 4).

    The coarser construction hook: ``form_class(**self.get_form_kwargs(...))``. A
    consumer overrides this when it needs full control of instantiation (a form
    requiring positional args); the finer ``get_form_kwargs`` override suffices for
    the common "inject a kwarg" case. Single-sourced so the construction path is
    identical for both flavors.
    """
    form_class = type(self)._mutation_meta.form_class
    return form_class(
        **self.get_form_kwargs(info, data=data, files=files, instance=instance),
    )


def _build_and_stash_form_input(
    cls: type,
    meta: _ValidatedMutationMeta,
    *,
    operation_kind: str,
    base: type,
) -> type:
    """Build + materialize a form input and stash its reverse map (both flavors' ``build_input`` tail).

    The shared body the two bases' ``build_input`` seams differ in only by their
    ``operation_kind`` (``CREATE`` / ``PARTIAL`` for the ``ModelForm`` flavor, the
    ``FORM`` sentinel for the plain flavor) and their waiver ``base`` (the framework
    base whose default ``get_form_kwargs`` / ``get_form`` an override is detected
    against). Routes through ``_cached_build_form_input`` (per-shape dedupe +
    per-declaration create-required guard) and the promoted
    ``mutations/sets.py::build_and_stash_input`` (spec-039 P1.7), which materializes
    the class into ``forms.inputs`` and stashes the reverse-map ``field_specs`` on
    the mutation (``cls._input_field_specs``) for the Slice-3 decode. The form's
    per-flavor stash value (``build_and_stash_input``'s ``payload``) IS the
    ``field_specs`` list, so ``specs_of`` is identity. Single-sited (with the
    serializer flavor) so a future change to the materialize-and-stash sequence
    touches one place.
    """
    return build_and_stash_input(
        cls,
        build=lambda: _cached_build_form_input(
            meta.form_class,
            operation_kind=operation_kind,
            fields=meta.fields,
            exclude=meta.exclude,
            guard_required=not _form_kwargs_overridden(cls, base),
        ),
        materialize=materialize_form_input_class,
        specs_of=lambda field_specs: field_specs,
    )


def _form_input_type_name_for(meta: _ValidatedMutationMeta, operation_kind: str) -> str:
    """Derive a form input's generated class name (both flavors' ``input_type_name`` body).

    The shared name derivation the two bases' ``input_type_name`` seams differ in
    only by ``operation_kind``: resolve the effective field set (after
    ``Meta.fields`` / ``Meta.exclude``), then defer to
    ``forms/inputs.py::form_input_type_name`` for the ``<FormClass>Input`` /
    ``<FormClass>PartialInput`` canonical name (or a shape-derived name for a
    narrowing). Single-sited with ``_build_and_stash_form_input`` so the bind's name
    choice and the field-factory's ``data:`` ref derive the name identically.
    """
    effective = _resolve_effective_form_field_names(
        meta.form_class,
        fields=meta.fields,
        exclude=meta.exclude,
    )
    full = tuple(get_form_fields(meta.form_class))
    return form_input_type_name(meta.form_class, operation_kind, effective, full_field_names=full)


class DjangoModelFormMutation(DjangoMutation):
    """A ``ModelForm``-backed write mutation (spec-038 Decision 6).

    Rides the ``DjangoMutation`` base: the SAME metaclass validates its ``Meta``
    (through the ``_validate_meta`` override below), the SAME declaration registry
    records it, and the SAME ``bind_mutations()`` phase-2.5 bind resolves its
    model's primary ``DjangoType`` + materializes its model-backed
    ``<Name>Payload`` (``node`` / ``result`` slot). The form-specific behavior is
    the seam overrides: the model comes from ``Meta.form_class._meta.model``, the
    input is form-derived (``forms/inputs.py``), and the input namespace is
    ``forms.inputs``.

    A concrete subclass declares ``Meta.form_class`` (a ``forms.ModelForm``
    subclass) + ``Meta.operation in {"create", "update"}`` (plus optional
    ``Meta.fields`` / ``Meta.exclude`` / ``Meta.permission_classes``).
    """

    @classmethod
    def _resolve_model(cls, meta: type) -> Any:
        """Resolve the model from ``Meta.form_class._meta.model`` (the ``036`` seam override).

        Returns ``None`` for a missing ``form_class`` / a form with no ``_meta`` /
        a ``ModelForm`` whose ``_meta.model`` is unset. ``_validate_meta`` has
        already validated ``form_class`` presence + ``ModelForm``-subclass-hood
        BEFORE calling this, so a ``None`` return here means "a ``ModelForm`` with
        no resolvable model" - the base validation raises a clean
        ``ConfigurationError`` (never a raw ``AttributeError``).
        """
        return resolve_meta_model(meta, key="form_class", meta_attr="_meta")

    @classmethod
    def _validate_meta(cls, meta: type) -> _ValidatedMutationMeta:
        """Validate a ``ModelForm``-mutation ``Meta`` at class creation (spec-038 Decision 6).

        The ``ModelForm`` matrix (raising ``ConfigurationError`` naming the
        offending key):

        - **unknown ``Meta`` key** - the typo guard over
          ``_ALLOWED_MODELFORM_META_KEYS`` (adds ``form_class``, drops ``model`` /
          ``input_class`` / ``partial_input_class``).
        - **missing ``form_class``** - a clean error naming the key.
        - **``form_class`` not a ``forms.ModelForm``** - type-checked BEFORE
          ``_resolve_model``, so a wrong-type ``form_class`` is a clean error, never
          a raw ``AttributeError`` from ``form_class._meta.model``.
        - **no resolvable ``_meta.model``** - a ``ModelForm`` with no model raises
          (``_resolve_model`` returns ``None``).
        - **bad ``operation``** - missing or not in ``{"create", "update"}``
          (``"delete"`` is rejected - the form flavor has no delete pipeline,
          Decision 10).
        - **``fields`` + ``exclude`` both supplied / bare-string / duplicate /
          unknown-name** - via the Slice-1 ``resolve_effective_form_fields``.

        ``permission_classes`` is validated + normalized by the shared
        ``_validate_permission_classes`` (the ``DjangoModelPermission`` default
        when unset). The snapshot carries ``form_class`` + the resolved ``model``.
        """
        name = cls.__name__
        reject_unknown_meta_keys(
            f"DjangoModelFormMutation {name}",
            meta,
            _ALLOWED_MODELFORM_META_KEYS,
        )

        form_class = require_backing_class(
            name,
            meta,
            key="form_class",
            base_label="DjangoModelFormMutation",
            expected_label="forms.ModelForm",
        )
        if not (isinstance(form_class, type) and issubclass(form_class, forms.ModelForm)):
            raise ConfigurationError(
                f"DjangoModelFormMutation {name}.Meta.form_class must be a forms.ModelForm "
                f"subclass; got {form_class!r}. (A plain forms.Form belongs on DjangoFormMutation.)",
            )

        model = resolve_backed_model_or_raise(
            cls,
            meta,
            base_label="DjangoModelFormMutation",
            key="form_class",
            noun="ModelForm",
        )

        operation = getattr(meta, "operation", None)
        if operation not in NON_DELETE_WRITE_OPERATIONS:
            raise non_delete_operation_error("DjangoModelFormMutation", name, operation)

        fields = getattr(meta, "fields", None)
        exclude = getattr(meta, "exclude", None)
        # Validate the narrowing fail-loud via the Slice-1 machinery (mutual
        # exclusion, bare-string / duplicate / unknown-name, empty-set guard); the
        # snapshot stores the RAW declarations (``build_input`` re-normalizes them).
        _resolve_effective_form_field_names(form_class, fields=fields, exclude=exclude)

        permission_classes = _validate_permission_classes(
            name,
            getattr(meta, "permission_classes", None),
        )

        return _ValidatedMutationMeta(
            model=model,
            operation=operation,
            input_class=None,
            partial_input_class=None,
            fields=fields,
            exclude=exclude,
            permission_classes=permission_classes,
            form_class=form_class,
        )

    # The form-input namespace (``forms.inputs``), overriding the ``036`` model
    # default (``mutations.inputs``) so a ``ModelForm`` mutation's lazy ``data:``
    # ref resolves the form-derived input, not a model-column input.
    input_module_path: str = FORMS_INPUTS_MODULE_PATH

    # The Slice-1 reverse-map records (``converter.FormInputFieldSpec`` per input
    # field), stashed at bind so the Slice-3 decode reaches the form-field-keyed
    # reverse map. ``None`` until bind (mirrors ``_input_class``).
    _input_field_specs: list | None = None

    @classmethod
    def build_input(cls, meta: _ValidatedMutationMeta, primary_type: type) -> type | None:
        """Build + materialize the operation's form-derived input (the seam override).

        Mirrors the ``036`` ``_materialize_input_for`` one-input-per-operation
        shape: a ``create`` materializes the ``CREATE``-shaped ``<FormClass>Input``,
        an ``update`` materializes the ``PARTIAL``-shaped
        ``<FormClass>PartialInput``. The input comes from the Slice-1 generator (the
        form's ``base_fields``, the symmetric model-backed converters), NOT the
        model's editable columns. Materialized into ``forms.inputs`` via
        ``materialize_form_input_class`` so the lazy ``data:`` ref resolves there.

        The **create** path runs the Slice-1 create-required-narrowing guard (a
        ``Meta.fields`` / ``Meta.exclude`` dropping a still-declared required form
        field raises - a bound form could never validate without it); the **update**
        path builds the partial directly (no create-required guard - the partial
        widens model-backed fields optional). Routes through
        ``_cached_build_form_input`` so two mutations over the same form + effective
        set reuse one class object and dedupe idempotently at materialize.

        ``guard_required`` is waived (``False``) when the concrete mutation
        overrides ``get_form_kwargs`` / ``get_form`` (spec-038 Slice 3 waiver): the
        override injects whatever fields a narrowing dropped, so the guard trusts it.
        The Slice-1 reverse-map ``field_specs`` are stashed on the mutation
        (``cls._input_field_specs``) so the Slice-3 decode can produce a
        form-field-keyed payload (the P1 reverse map).
        """
        del primary_type  # the form input derives from the form, not the model primary.
        return _build_and_stash_form_input(
            cls,
            meta,
            operation_kind=NON_DELETE_OPERATION_INPUT_KIND[meta.operation],
            base=DjangoModelFormMutation,
        )

    get_form_kwargs = _default_get_form_kwargs
    get_form = _default_get_form

    @classmethod
    def input_type_name(cls, meta: _ValidatedMutationMeta) -> str:
        """Return the generated form-input class name (the name seam override).

        The form-flavor name via ``forms/inputs.py::form_input_type_name`` (the
        ``<FormClass>Input`` / ``<FormClass>PartialInput`` canonical name, or a
        shape-derived name for a narrowing), single-sourced with the bind's name
        choice in ``build_input``.
        """
        return _form_input_type_name_for(meta, NON_DELETE_OPERATION_INPUT_KIND[meta.operation])

    # The sync / async ``ModelForm`` resolver seams (delegate to the Slice-3 form
    # pipeline), via the shared ``resolver_seams`` factory (spec-039 M1b). The
    # generated seams' function-local import of ``forms/resolvers.py`` keeps
    # ``forms/sets.py`` free of a load-time edge to the resolver module.
    resolve_sync, resolve_async = resolver_seams(
        "django_strawberry_framework.forms.resolvers",
        "resolve_form_sync",
        "resolve_form_async",
    )


class DjangoFormMutationMetaclass(type):
    """Collect + validate a concrete ``DjangoFormMutation``'s ``Meta`` and register it.

    Mirrors ``DjangoMutationMetaclass.__new__`` but over the DISJOINT plain-form
    declaration registry (``register_form_mutation``): build the class, skip the
    abstract base (no ``Meta``), else validate via the class's ``_validate_meta``
    and record it for the ``bind_form_mutations()`` phase-2.5 bind. A separate
    metaclass (not ``DjangoMutationMetaclass``) because ``DjangoFormMutation`` is
    model-less - it is NOT a ``DjangoMutation`` subclass and does not ride the
    model declaration registry or ``bind_mutations()``.
    """

    def __new__(
        cls: type[DjangoFormMutationMetaclass],
        name: str,
        bases: tuple,
        attrs: dict,
    ) -> DjangoFormMutationMetaclass:
        """Build the class; for a concrete subclass, validate ``Meta`` and register it."""
        new_class = super().__new__(cls, name, bases, attrs)
        meta = attrs.get("Meta")
        if meta is None:
            # The abstract base ``DjangoFormMutation`` (no nested ``Meta``) is not a
            # concrete mutation: skip validation / registration (the same
            # in-flight-base-class guard the model metaclass uses).
            return new_class
        new_class._mutation_meta = new_class._validate_meta(meta)
        register_form_mutation(new_class)
        return new_class


class DjangoFormMutation(metaclass=DjangoFormMutationMetaclass):
    """A model-LESS plain-``forms.Form`` write mutation (spec-038 Decision 6).

    The lighter sibling: no model, no ``DjangoType`` object slot. It shares the
    form converter + the Slice-3 form pipeline but carries its OWN metaclass +
    declaration registry + ``bind_form_mutations()`` bind. A concrete subclass
    declares ``Meta.form_class`` (a ``forms.Form`` subclass; a ``ModelForm`` is
    rejected naming ``DjangoModelFormMutation``) + optional ``Meta.fields`` /
    ``Meta.exclude`` / ``Meta.permission_classes``. It rejects ANY
    ``Meta.operation`` (a model-less mutation has no model operation - Decision
    10) and uses the fixed ``"form"`` shape-identity sentinel for its input cache
    key.

    Its bind materializes the form-derived input + the pinned ``{ ok errors }``
    payload (no object slot). The resolver pipeline is Slice 3.
    """

    # The validated ``Meta`` snapshot the metaclass stashes on a concrete subclass.
    # ``None`` on the abstract base (no ``Meta``).
    _mutation_meta: _ValidatedMutationMeta | None = None

    # Bind outputs (forward-compat plumbing for Slice 3). ``_primary_type`` is
    # ALWAYS ``None`` (a model-less mutation returns no ``DjangoType``); the bind
    # stashes the materialized input class + the pinned ``{ ok errors }`` payload
    # name. ``DjangoMutationField`` (Slice 3) reads them.
    _primary_type: type | None = None
    _input_class: type | None = None
    _payload_type_name: str | None = None

    # The Slice-1 reverse-map records, stashed at bind for the Slice-3 decode
    # (mirrors ``DjangoModelFormMutation._input_field_specs``).
    _input_field_specs: list | None = None

    # The form-input namespace; mirrors ``DjangoModelFormMutation``.
    input_module_path: str = FORMS_INPUTS_MODULE_PATH

    @classmethod
    def _validate_meta(cls, meta: type) -> _ValidatedMutationMeta:
        """Validate a plain-form-mutation ``Meta`` at class creation (spec-038 Decision 6 / 10).

        The plain-form matrix (raising ``ConfigurationError`` naming the offending
        key):

        - **any ``Meta.operation``** - checked FIRST and rejected outright with a
          targeted message (a model-less mutation has no model operation - Decision
          10), so a copied ``DjangoModelFormMutation`` ``Meta`` gets a clear reason
          rather than a generic unknown-key error.
        - **unknown ``Meta`` key** - the typo guard over
          ``_ALLOWED_PLAIN_FORM_META_KEYS`` (no ``operation``, no ``model``).
        - **missing ``form_class``** - a clean error naming the key.
        - **``form_class`` is a ``forms.ModelForm``** - checked FIRST, rejected
          naming ``DjangoModelFormMutation`` as the correct base (the targeted
          Edge-case message: without this a bare ``forms.Form`` gate would reject a
          ``ModelForm`` with a confusing generic message, and a let-through
          ``ModelForm`` would silently ``form.save()`` with no object slot / no
          ``DjangoModelPermission`` default / no optimizer re-fetch, defeating the
          two-base split - P2).
        - **``form_class`` not a ``forms.Form``** - the general type gate after the
          targeted ``ModelForm`` reject.
        - **any ``Meta.operation``** - rejected outright (a model-less mutation has
          no model operation - Decision 10).
        - **``fields`` + ``exclude`` both supplied / bare-string / duplicate /
          unknown-name** - via the Slice-1 ``resolve_effective_form_fields``.
        - **``permission_classes``** - validated + normalized by the shared
          ``_validate_permission_classes`` with ``unset_default=(DenyAll,)``: a
          model-less form cannot inherit the model-permission default, so an unset
          ``permission_classes`` denies by default and a public write is the
          explicit ``permission_classes = []`` opt-out (Decision 11).

        The snapshot carries ``model=None`` + the ``"form"`` operation sentinel +
        ``form_class`` (Decision 7 P2 - the fixed shape-identity component a plain
        form carries in place of a model operation).
        """
        name = cls.__name__
        # ``operation`` is RECOGNIZED-but-rejected on the plain base (not merely an
        # unknown key): a model-less mutation has no model operation (Decision 10).
        # Reject it by KEY PRESENCE, not value, so an explicit ``operation = None``
        # is rejected too - the fixed ``"form"`` sentinel must not accept ANY copied
        # ``Meta.operation`` key (spec-038 Decision 10; a value check let
        # ``None`` slip through as if absent). Reject it FIRST with a targeted
        # message naming the reason, so a consumer who copied a
        # ``DjangoModelFormMutation`` ``Meta`` sees "operation is not supported"
        # rather than a generic "unknown keys: ['operation']" - then run the
        # promoted typo guard over the genuinely-unknown remainder (``operation`` is
        # added to the allowed set passed there so a stray ``operation`` cannot
        # double-report; it is already rejected above by the key-presence check).
        if "operation" in vars(meta):
            raise ConfigurationError(
                f"DjangoFormMutation {name}.Meta.operation is not supported; a model-less form "
                "mutation has no model operation (Decision 10). Remove Meta.operation.",
            )

        reject_unknown_meta_keys(
            f"DjangoFormMutation {name}",
            meta,
            _ALLOWED_PLAIN_FORM_META_KEYS | {"operation"},
        )

        form_class = require_backing_class(
            name,
            meta,
            key="form_class",
            base_label="DjangoFormMutation",
            expected_label="forms.Form",
        )
        # Check ``ModelForm`` FIRST (Edge case P2): ``forms.ModelForm`` is NOT a
        # subclass of ``forms.Form`` - both are siblings under ``forms.BaseForm`` -
        # so a bare ``issubclass(_, forms.Form)`` gate would reject a ``ModelForm``
        # with a confusing "not a Form" message. The targeted reject names the
        # correct base.
        if isinstance(form_class, type) and issubclass(form_class, forms.ModelForm):
            raise ConfigurationError(
                f"DjangoFormMutation {name}.Meta.form_class {form_class.__name__} is a "
                "forms.ModelForm; use DjangoModelFormMutation for a ModelForm (it returns the "
                "saved object + applies the DjangoModelPermission default + the optimizer "
                "re-fetch). DjangoFormMutation is for a plain forms.Form only.",
            )
        if not (isinstance(form_class, type) and issubclass(form_class, forms.Form)):
            raise ConfigurationError(
                f"DjangoFormMutation {name}.Meta.form_class must be a forms.Form subclass; "
                f"got {form_class!r}.",
            )

        fields = getattr(meta, "fields", None)
        exclude = getattr(meta, "exclude", None)
        _resolve_effective_form_field_names(form_class, fields=fields, exclude=exclude)

        # The plain flavor has no model, so it CANNOT inherit the
        # ``DjangoModelPermission`` default (that class reads the resolved model,
        # which a model-less mutation never provides - it would crash at request
        # time, not deny). An unset ``permission_classes`` therefore defaults to
        # ``[DenyAll]`` (deny-by-default); a public plain-form write is the explicit
        # ``permission_classes = []`` opt-out (spec-038 Decision 11).
        permission_classes = _validate_permission_classes(
            name,
            getattr(meta, "permission_classes", None),
            unset_default=(DenyAll,),
        )

        return _ValidatedMutationMeta(
            model=None,
            operation=FORM,
            input_class=None,
            partial_input_class=None,
            fields=fields,
            exclude=exclude,
            permission_classes=permission_classes,
            form_class=form_class,
        )

    @classmethod
    def build_input(cls, meta: _ValidatedMutationMeta) -> type:
        """Build + materialize the plain form's model-less input (the ``"form"`` sentinel shape).

        A plain form has ONE input (create-shaped, the ``FORM`` sentinel kind -
        each field's requiredness from ``field.required``), so the bind builds the
        single ``<FormClass>Input``. Runs the create-required-narrowing guard (a
        narrowing dropping a required form field raises). Routes through
        ``_cached_build_form_input`` so two plain mutations over the same form +
        effective set reuse one class object and dedupe idempotently at materialize
        (the ``"form"``-sentinel shape identity).

        ``guard_required`` is waived when the concrete mutation overrides
        ``get_form_kwargs`` / ``get_form`` (spec-038 Slice 3 waiver). The Slice-1
        reverse-map ``field_specs`` are stashed on the mutation for the Slice-3
        decode (the P1 reverse map).
        """
        return _build_and_stash_form_input(
            cls,
            meta,
            operation_kind=FORM,
            base=DjangoFormMutation,
        )

    get_form_kwargs = _default_get_form_kwargs
    get_form = _default_get_form

    def perform_mutate(self, form: Any, info: Any) -> None:
        """The plain-form write hook (spec-038 Decision 6 / Decision 8 step 5).

        The default calls ``form.save()`` when the form defines one (a
        ``forms.Form`` does not by default), else a no-op. A consumer overrides this
        to perform the model-less side effect (send an email, enqueue a job, write
        an audit row); the pipeline wraps the call in ``save_or_field_errors`` so a
        post-validation ``IntegrityError`` returns the ``{ ok: false }`` envelope,
        never a top-level error. The ``ModelForm`` flavor writes via ``form.save()``
        directly (it has a real model save), so this hook is plain-flavor only.
        """
        del info
        save = getattr(form, "save", None)
        if callable(save):
            save()

    def check_permission(
        self,
        info: Any,
        operation: str,
        data: Any,
        instance: Any = None,
    ) -> bool:
        """Return whether the request is authorized (the plain-flavor write-auth seam).

        The plain ``DjangoFormMutation`` is NOT a ``DjangoMutation`` subclass, so it
        carries its own ``check_permission`` mirroring the ``036`` default: delegate
        to every ``Meta.permission_classes`` entry, denying as soon as one denies.
        Slice-3's ``forms/resolvers.py`` calls this through the reused
        ``authorize_or_raise`` gate (which maps ``False`` to a top-level
        ``GraphQLError``). An ``async def has_permission`` entry returns a truthy
        coroutine, which ``reject_async_in_sync_context`` closes + raises as a
        ``SyncMisuseError`` (an authorization bypass otherwise - the same discipline
        the model flavor applies).
        """
        meta = type(self)._mutation_meta
        for permission_class in meta.permission_classes:
            allowed = reject_async_in_sync_context(
                permission_class().has_permission(info, type(self), operation, data, instance),
                owner=permission_class.__name__,
                method="has_permission",
                context="mutation",
                recourse=_PERMISSION_ASYNC_RECOURSE,
            )
            if not allowed:
                return False
        return True

    @classmethod
    def input_type_name(cls, meta: _ValidatedMutationMeta) -> str:
        """Return the generated form-input class name (the ``FORM``-sentinel create shape)."""
        return _form_input_type_name_for(meta, FORM)

    # The sync / async plain-form resolver seams (delegate to the Slice-3 form
    # pipeline), via the shared ``resolver_seams`` factory with ``with_id=False`` -
    # a model-less form has no row to locate, so the seam signature is
    # ``(info, *, data)`` (spec-039 M1b). The generated seams' function-local import
    # keeps ``forms/sets.py`` free of a load-time edge to the resolver module.
    resolve_sync, resolve_async = resolver_seams(
        "django_strawberry_framework.forms.resolvers",
        "resolve_form_sync",
        "resolve_form_async",
        with_id=False,
    )


def _bind_form_mutation(mutation_cls: type) -> None:
    """Bind one registered plain ``DjangoFormMutation`` at phase 2.5 (spec-038 Decision 6).

    Materializes the form-derived input (via the ``build_input`` seam, into
    ``forms.inputs``) + the pinned model-less ``{ ok errors }`` payload (via
    ``build_payload_type(object_type=None)`` - the single-sourced payload builder,
    routed through the SAME ``materialize_mutation_input_class`` ledger as the
    model payloads so the AR-M6 distinct-shape collision raise + the
    ``registry.clear()`` co-clear apply). Stashes the refs for Slice 3's
    ``DjangoMutationField`` (``_primary_type`` stays ``None`` - no object to
    return).
    """
    meta = mutation_cls._mutation_meta
    input_cls = mutation_cls.build_input(meta)

    payload_cls = build_payload_type(
        mutation_cls.__name__,
        object_type=None,
        object_slot=None,
    )
    materialize_mutation_input_class(payload_cls.__name__, payload_cls)

    mutation_cls._primary_type = None
    mutation_cls._input_class = input_cls
    mutation_cls._payload_type_name = payload_cls.__name__


def bind_form_mutations() -> None:
    """Bind every registered plain ``DjangoFormMutation`` (the finalizer phase-2.5 entry point).

    The plain-form sibling of ``bind_mutations()``: ``types/finalizer.py`` calls it
    in the phase-2.5 window (alongside ``bind_mutations()``), after primary-type
    state is settled and before ``strawberry.type(...)`` freezes the schema
    classes. Drains the disjoint plain-form declaration registry in registration
    order; each ``_bind_form_mutation`` materializes that mutation's form-derived
    input + its pinned ``{ ok errors }`` payload. The ``ModelForm`` flavor rides
    ``bind_mutations()`` (it is a ``DjangoMutation`` subclass), so it is NOT bound
    here - this drains only the model-less ledger.

    ``_form_shape_build_cache`` is this pass's own (per-pass) build cache, cleared at
    the top so each form input is rebuilt fresh. The cross-pass materialization
    ledgers (the form-input ledger here, plus the mutation ledger the plain ``{ ok
    errors }`` payload rides) are reset ONCE by ``finalize_django_types`` before the
    bind sequence so a recover-in-place re-finalize is retry-idempotent (feedback
    #6); they are NOT reset here, where a per-pass clear would wipe the
    ``ModelForm``-flavor inputs ``bind_mutations()`` already materialized into the
    form ledger.
    """
    _form_shape_build_cache.clear()
    for mutation_cls in iter_form_mutations():
        _bind_form_mutation(mutation_cls)
