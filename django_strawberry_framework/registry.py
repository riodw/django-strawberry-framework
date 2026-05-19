"""Type registry for ``DjangoType`` metadata, pending relations, and choice enums.

Maps Django models to their generated ``DjangoType`` and ``(model,
field_name)`` to generated ``Enum`` classes. Used by:

- ``types.converters.convert_relation`` for relation resolution once
  target types are registered.
- ``types.converters.convert_choices_to_enum`` for enum reuse across
  multiple ``DjangoType`` subclasses reading the same choice column.

The registry is a process-global singleton (``registry``). Test isolation
is via the ``clear()`` helper, typically wired into a ``pytest`` autouse
fixture.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import Enum
from typing import TYPE_CHECKING

from django.db import models

from .exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover
    from .types.definition import DjangoTypeDefinition
    from .types.relations import PendingRelation


class TypeRegistry:
    """Process-global registry of generated GraphQL types and enums.

    Mutating methods are not guarded by a lock. This is safe because
    every production-path mutation runs at import time from
    ``DjangoType.__init_subclass__`` (single-threaded module loading);
    ``clear`` is test-only. Do not mutate the registry from a request
    handler or async resolver.
    """

    def __init__(self) -> None:
        self._types: dict[type[models.Model], list[type]] = {}
        self._primaries: dict[type[models.Model], type] = {}
        self._models: dict[type, type[models.Model]] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}
        self._definitions: dict[type, DjangoTypeDefinition] = {}
        self._pending: list[PendingRelation] = []
        self._finalized: bool = False

    def _check_mutable(self) -> None:
        """Defense-in-depth guard: refuse mutation after ``mark_finalized``.

        ``DjangoType.__init_subclass__`` already rejects new subclasses
        once the registry is finalized; this check pins the same contract
        at the registry boundary so any out-of-band mutator (e.g., a late
        import triggered from a request handler) fails loud instead of
        silently corrupting the post-finalization snapshot.
        """
        if self._finalized:
            raise ConfigurationError(
                "TypeRegistry is finalized; mutators are import-time only "
                "(call registry.clear() before registering new types)",
            )

    @staticmethod
    def _already_registered(label: str, name: str, existing_name: str) -> ConfigurationError:
        """Build the canonical "already registered" ``ConfigurationError``.

        Centralizes the phrasing so the three mutator collision messages
        (``register`` forward, ``register`` reverse, ``register_enum``)
        stay grep-stable for tests and consumer error matching.
        """
        return ConfigurationError(f"{name} is already registered {label} {existing_name}")

    def register(
        self,
        model: type[models.Model],
        type_cls: type,
        *,
        primary: bool = False,
    ) -> bool:
        """Register ``type_cls`` as a ``DjangoType`` for ``model``.

        Multiple types may register against the same model; the optional
        ``primary`` keyword flags exactly one of them as the relation-
        resolution target. ``_models`` is still one-to-one: the same
        class cannot be registered against two different models.

        Behavior:

        - First registration appends ``type_cls`` to ``_types[model]`` and
          sets ``_primaries[model] = type_cls`` when ``primary=True``.
          Returns ``True``.
        - Idempotent re-register of the same ``type_cls`` for the same
          model is a no-op when the ``primary`` flag matches the stored
          state; returns ``False``.  A mismatched ``primary`` flag in
          either direction raises (primary status is a declaration, not a
          mutable property).
        - Registering a different ``type_cls`` for the same model appends
          to ``_types[model]``. If ``primary=True`` and ``_primaries[model]``
          is already set to a different class, raise ``ConfigurationError``.
        - Returns ``True`` whenever state was added; the return value
          drives the snapshot-conditional rollback in
          ``register_with_definition``.

        Raises:
            ConfigurationError: reverse-collision (same ``type_cls``,
                different ``model``); duplicate-primary collision; primary
                flag flipped on idempotent re-register; the registry is
                finalized.
        """
        self._check_mutable()
        existing_model = self._models.get(type_cls)
        if existing_model is not None and existing_model is not model:
            raise self._already_registered("against", type_cls.__name__, existing_model.__name__)
        existing_types = self._types.setdefault(model, [])
        if type_cls in existing_types:
            stored_as_primary = self._primaries.get(model) is type_cls
            if primary != stored_as_primary:
                raise ConfigurationError(
                    f"{type_cls.__name__} is already registered for {model.__name__}; "
                    "primary flag cannot be flipped on re-register",
                )
            return False
        if primary:
            existing_primary = self._primaries.get(model)
            if existing_primary is not None:
                raise ConfigurationError(
                    f"{type_cls.__name__} is already declared primary as {existing_primary.__name__}",
                )
        existing_types.append(type_cls)
        self._models[type_cls] = model
        if primary:
            self._primaries[model] = type_cls
        return True

    def get(self, model: type[models.Model]) -> type | None:
        """Return the relation-resolution target for ``model``, or ``None``.

        Three return states:

        - **Primary declared.** ``_primaries[model]`` is set; return it.
        - **Single registered type, no primary flag.** Backward-compatible
          path for the single-type-per-model case; return that type.
        - **Multiple registered types and no declared primary.** Ambiguous
          state pending the ``finalize_django_types()`` audit; return
          ``None``. Callers cannot distinguish this from
          "no type registered" without checking ``types_for(model)``.
        """
        primary = self._primaries.get(model)
        if primary is not None:
            return primary
        candidates = self._types.get(model)
        if candidates is not None and len(candidates) == 1:
            return candidates[0]
        return None

    def model_for_type(self, type_cls: type | None) -> type[models.Model] | None:
        """Reverse-lookup: return the Django model for a registered ``DjangoType``.

        Used by ``DjangoOptimizerExtension`` to trace a resolver's
        GraphQL return type back to a Django model so it can walk
        ``model._meta.get_fields()`` against the resolver's selection set.
        Returns ``None`` for unregistered classes (and for ``None`` itself,
        so the optimizer can pipeline through unwrapped wrapper types
        without an extra guard).
        """
        if type_cls is None:
            return None
        return self._models.get(type_cls)

    def iter_types(self) -> Iterator[tuple[type[models.Model], type]]:
        """Yield ``(model, type_cls)`` pairs once per registered type.

        A model with multiple registered types appears multiple times in
        the iterator; consumers that need a per-model action must dedupe
        by model. Public iterator so consumers (B6 schema audit, B7
        walker) do not reach into ``_types`` directly.
        """
        for model, type_list in self._types.items():
            for type_cls in type_list:
                yield (model, type_cls)

    def primary_for(self, model: type[models.Model]) -> type | None:
        """Return the explicitly declared primary type for ``model``, or ``None``.

        Strict ``_primaries`` lookup. Distinct from ``get()``: returns
        ``None`` for the single-type-no-primary case where ``get()``
        would return that lone type.
        """
        return self._primaries.get(model)

    def types_for(self, model: type[models.Model]) -> tuple[type, ...]:
        """Return every registered type for ``model`` in registration order.

        Immutable snapshot. Returns ``()`` for an unregistered model.
        """
        return tuple(self._types.get(model, ()))

    def models_with_multiple_types(self) -> Iterator[type[models.Model]]:
        """Yield each model that has at least two registered types.

        Drives ``_audit_primary_ambiguity`` (Slice 3) without exposing the
        internal ``_types`` dict to the finalizer.
        """
        return (model for model, types in self._types.items() if len(types) >= 2)

    def register_definition(self, type_cls: type, definition: DjangoTypeDefinition) -> None:
        """Register the collected definition object for ``type_cls``.

        Asymmetry note: ``type_cls`` is not required to be present in
        ``_types``/``_models`` first.  The caller (``DjangoType.__init_subclass__``
        in ``types/base.py``) is responsible for ordering — it calls
        ``register`` before ``register_definition`` for every concrete
        ``DjangoType`` subclass.  Definitions for un-modelled wrapper
        classes are not a supported entry point.
        """
        self._check_mutable()
        existing = self._definitions.get(type_cls)
        if existing is not None and existing is not definition:
            raise ConfigurationError(f"{type_cls.__name__} already has a registered DjangoTypeDefinition")
        self._definitions[type_cls] = definition

    def register_with_definition(
        self,
        model: type[models.Model],
        type_cls: type,
        definition: DjangoTypeDefinition,
        *,
        primary: bool = False,
    ) -> None:
        """Atomic ``register`` + ``register_definition`` pair.

        Snapshots ``_primaries[model]`` before calling ``register`` and
        captures whether that call appended state.  If
        ``register_definition`` then raises, only state added by THIS
        call is rolled back — a pre-existing registration (idempotent
        same-type re-register) survives a re-register-with-different-
        definition failure intact. ``DjangoType.__init_subclass__`` is
        the only intended caller; see ``types/base.py``.
        """
        pre_primary = self._primaries.get(model)
        appended = self.register(model, type_cls, primary=primary)
        try:
            self.register_definition(type_cls, definition)
        except Exception:
            if appended:
                types = self._types.get(model, [])
                types.remove(type_cls)
                if not types:
                    self._types.pop(model, None)
                self._models.pop(type_cls, None)
                if pre_primary is None:
                    self._primaries.pop(model, None)
                else:
                    self._primaries[model] = pre_primary
            raise

    def get_definition(self, type_cls: type) -> DjangoTypeDefinition | None:
        """Return the collected definition for ``type_cls``, or ``None``."""
        return self._definitions.get(type_cls)

    def iter_definitions(self) -> Iterator[tuple[type, DjangoTypeDefinition]]:
        """Yield ``(type_cls, definition)`` pairs in registration order."""
        yield from self._definitions.items()

    def add_pending_relation(self, pending: PendingRelation) -> None:
        """Record a relation whose target type must be resolved during finalization."""
        self._check_mutable()
        self._pending.append(pending)

    def iter_pending_relations(self) -> Iterator[PendingRelation]:
        """Yield pending relation records in collection order.

        ``discard_pending`` may be called between yields by the finalizer;
        callers that materialize the iterator and then trigger discards
        will observe a stale view.  Typical consumers (the finalizer
        itself) drain into a list before mutating.
        """
        yield from self._pending

    def discard_pending(self, resolved: Iterable[PendingRelation]) -> None:
        """Drop pending records that have been resolved successfully.

        Identity-matched (``id()``) rather than equality-matched: the
        finalizer hands back the very ``PendingRelation`` instances it
        received from ``iter_pending_relations``, so identity is a
        stronger contract than ``__eq__`` and avoids coupling this
        module to ``PendingRelation``'s hashability.
        """
        self._check_mutable()
        resolved_ids = {id(record) for record in resolved}
        self._pending = [pending for pending in self._pending if id(pending) not in resolved_ids]

    def is_finalized(self) -> bool:
        """Return whether the registry has completed ``finalize_django_types()``."""
        return self._finalized

    def mark_finalized(self) -> None:
        """Mark the registry as finalized."""
        self._finalized = True

    def register_enum(
        self,
        model: type[models.Model],
        field_name: str,
        enum_cls: type[Enum],
    ) -> None:
        """Cache ``enum_cls`` for the ``(model, field_name)`` choice field.

        Two ``DjangoType``s pointing at the same choice column reuse the
        same enum, even if their consumer-facing class names differ.

        Raises:
            ConfigurationError: an enum is already cached for
                ``(model, field_name)`` and it is a different class.
                Re-registering the *same* enum class is a no-op so the
                normal ``get_enum``-then-``register_enum`` cache pattern
                in ``convert_choices_to_enum`` still works under retry.
        """
        self._check_mutable()
        key = (model, field_name)
        existing = self._enums.get(key)
        if existing is not None and existing is not enum_cls:
            raise self._already_registered(
                "as",
                f"{model.__name__}.{field_name}",
                existing.__name__,
            )
        self._enums[key] = enum_cls

    def get_enum(
        self,
        model: type[models.Model],
        field_name: str,
    ) -> type[Enum] | None:
        """Return the cached enum for ``(model, field_name)``, or ``None``."""
        return self._enums.get((model, field_name))

    def clear(self) -> None:
        """Drop all registered types and enums.

        Test-only — production code should never need to call this.
        Wire into ``pytest`` autouse fixtures so each registry-using test
        starts with a clean registry.
        """
        self._types.clear()
        self._primaries.clear()
        self._models.clear()
        self._enums.clear()
        self._definitions.clear()
        self._pending.clear()
        self._finalized = False


registry = TypeRegistry()
