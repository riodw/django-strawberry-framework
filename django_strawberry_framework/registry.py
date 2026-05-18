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
        # TODO(spec-014-meta_primary-0_0_6.md Slice 1): replace the one-type
        # map with ordered per-model storage plus explicit primary tracking.
        # Pseudo:
        # - _types: dict[Model, list[type]] = {}
        # - _primaries: dict[Model, type] = {}
        # - keep _models as the type -> model reverse lookup.
        self._types: dict[type[models.Model], type] = {}
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

    # TODO(spec-014-meta_primary-0_0_6.md Slice 1): add keyword-only
    # primary: bool = False and return bool for "state was added".
    # Pseudo:
    # - reject type_cls already mapped to a different model.
    # - if type_cls is already in _types[model], compare primary to
    #   (_primaries.get(model) is type_cls); flag flips raise.
    # - if primary and a different primary exists, raise duplicate-primary.
    # - append new types in registration order; set _models and _primaries.
    # - return True for append, False for idempotent same-type no-op.
    def register(self, model: type[models.Model], type_cls: type) -> None:
        """Register ``type_cls`` as the ``DjangoType`` for ``model``.

        Maintains both directions of the mapping so the optimizer can
        reverse a ``DjangoType`` class back to its Django model in O(1).

        Raises:
            ConfigurationError: ``model`` already has a registered type,
                ``type_cls`` is already registered against a different
                model, or the registry is finalized.  The error message
                names the conflicting class or model so the consumer can
                identify the duplicate at import time.
        """
        self._check_mutable()
        if model in self._types:
            raise self._already_registered("as", model.__name__, self._types[model].__name__)
        existing_model = self._models.get(type_cls)
        if existing_model is not None and existing_model is not model:
            raise self._already_registered("against", type_cls.__name__, existing_model.__name__)
        self._types[model] = type_cls
        self._models[type_cls] = model

    # TODO(spec-014-meta_primary-0_0_6.md Slice 1): change lookup semantics to
    # primary-first, single-type fallback, ambiguous-multiple-as-None.
    # Pseudo:
    # - if _primaries.get(model): return it
    # - if len(_types.get(model, ())) == 1: return the only type
    # - return None for no type or multiple types without primary.
    def get(self, model: type[models.Model]) -> type | None:
        """Return the registered ``DjangoType`` for ``model``, or ``None``."""
        return self._types.get(model)

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

    # TODO(spec-014-meta_primary-0_0_6.md Slice 1): add primary_for(model),
    # types_for(model), and models_with_multiple_types(); update iter_types()
    # to yield one (model, type_cls) pair for every registered type.
    # Pseudo:
    # - primary_for -> _primaries.get(model)
    # - types_for -> tuple(_types.get(model, ()))
    # - models_with_multiple_types -> models whose stored list has len >= 2.
    def iter_types(self) -> Iterator[tuple[type[models.Model], type]]:
        """Yield ``(model, type_cls)`` pairs for every registered ``DjangoType``.

        Public iterator so consumers (B6 schema audit, B7 walker) do not
        reach into ``_types`` directly. Keeps the internal dict shape
        private and provides a clean extension point for future filtering
        (e.g., schema-scoped registries).
        """
        yield from self._types.items()

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
    ) -> None:
        """Atomic ``register`` + ``register_definition`` pair.

        If ``register_definition`` raises after ``register`` succeeded,
        the model->type mapping is rolled back so the consumer sees the
        real underlying error on the next re-import or test rerun
        instead of "already registered". ``DjangoType.__init_subclass__``
        is the only intended caller; see ``types/base.py``.
        """
        # TODO(spec-014-meta_primary-0_0_6.md Slice 1): forward primary= to
        # register() and make rollback conditional on that call appending state.
        # Pseudo:
        # - pre_primary = _primaries.get(model)
        # - appended = register(model, type_cls, primary=primary)
        # - if register_definition raises and appended: remove only this type,
        #   restore _models, and restore/pop _primaries back to pre_primary.
        # - if appended is False: leave pre-existing registry state untouched.
        self.register(model, type_cls)
        try:
            self.register_definition(type_cls, definition)
        except Exception:
            self._types.pop(model, None)
            self._models.pop(type_cls, None)
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
        # TODO(spec-014-meta_primary-0_0_6.md Slice 1): clear _primaries here
        # after adding explicit primary tracking.
        self._models.clear()
        self._enums.clear()
        self._definitions.clear()
        self._pending.clear()
        self._finalized = False


registry = TypeRegistry()
