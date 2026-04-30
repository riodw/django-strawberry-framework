# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
## [0.0.2] - prerelease
### Added
- `DjangoType` base class — DRF-shaped `Meta`-driven Django-model-to-Strawberry-type adapter (`django_strawberry_framework/types.py`). Covers `Meta.model`, `Meta.fields = "__all__" | (...)`, `Meta.exclude`, `Meta.name`, `Meta.description`, abstract intermediates without `Meta`, and consumer-annotation overrides on top of synthesized fields.
- `Meta` validation rejects unknown keys (typo guard) and the deferred-spec keys `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, and `search_fields` until their owning specs ship.
- Scalar field conversion (`django_strawberry_framework/converters.py`) for `AutoField`/`BigAutoField`/`SmallAutoField`, `CharField`/`TextField`/`SlugField`/`EmailField`/`URLField`, integer types, `BooleanField`, `FloatField`, `DecimalField`, date/time/duration types, `UUIDField`, `BinaryField`, `FileField`/`ImageField`. Unsupported field types raise `ConfigurationError`.
- `TypeRegistry` singleton (`django_strawberry_framework/registry.py`) with `register` / `get` / `register_enum` / `get_enum` / `clear`. Collision raises `ConfigurationError`.
- Exception hierarchy (`django_strawberry_framework/exceptions.py`): `DjangoStrawberryFrameworkError` base, `ConfigurationError`, `OptimizerError`.
- Default `DjangoType.get_queryset` identity classmethod and the `_is_default_get_queryset` sentinel reserved for Slice 6's `has_custom_get_queryset` override-detection.
- Stubbed scaffolding for Slice 3+ (`convert_relation`, `registry.lazy_ref`, `DjangoOptimizerExtension`, `plan_relation`, `has_custom_get_queryset`) with `NotImplementedError` and per-slice TODO comments.
- `py.typed` PEP 561 marker so consumers' type checkers consume the package's annotations.
- Package re-exports at the root: `DjangoType`, `DjangoOptimizerExtension`, `auto` (pass-through of `strawberry.auto`), plus a package-level `logging.getLogger("django_strawberry_framework")`.
- `tests/test_django_types.py` covering registry behaviour, `Meta` validation (missing model, fields/exclude exclusivity, deferred-key rejection both parametrized and named, unknown-key typo guard, abstract intermediate pass-through), scalar synthesis on `Category`/`Item`, Strawberry finalization (`__strawberry_definition__` attachment, `Meta.name`, `Meta.description`), default `get_queryset`, and the `convert_scalar` unsupported-field branch.
