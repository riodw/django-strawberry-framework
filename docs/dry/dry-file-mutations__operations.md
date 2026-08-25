# DRY review: `django_strawberry_framework/mutations/operations.py`

Status: verified

## System trace

`django_strawberry_framework/mutations/operations.py` is the single authoritative declaration site for write-side mutation operation metadata and vocabulary across the framework ([spec-036][spec-036], [spec-038][spec-038], [spec-039][spec-039]).

It owns:
1. Operation descriptors ([`MutationOperationDescriptor`][mutations-operations]): Dataclass declaring name, input generator kind (`CREATE` / `PARTIAL`), consumer input override attribute name (`input_class` / `partial_input_class`), GraphQL root argument shape (`id`, `data`), Django model permission action codename (`add`, `change`, `delete`), and flavor support (`supports_model_mutation`, `supports_form_mutation`).
   - Constant instances: `django_strawberry_framework/mutations/operations.py::OPERATION_CREATE`, `django_strawberry_framework/mutations/operations.py::OPERATION_UPDATE`, `django_strawberry_framework/mutations/operations.py::OPERATION_DELETE`, `django_strawberry_framework/mutations/operations.py::OPERATION_FORM`.
   - Operation registry: `django_strawberry_framework/mutations/operations.py::_OPERATIONS_BY_NAME`.
2. Operation lookup and inspection helpers:
   - [`get_operation_descriptor`][mutations-operations] (`django_strawberry_framework/mutations/operations.py::get_operation_descriptor`): Lookup by operation name.
   - [`operation_takes_id`][mutations-operations] (`django_strawberry_framework/mutations/operations.py::operation_takes_id`): Query whether an operation takes a root `id: ID!` argument.
   - [`operation_takes_data`][mutations-operations] (`django_strawberry_framework/mutations/operations.py::operation_takes_data`): Query whether an operation takes a root `data: ...` input argument.
3. Derived metadata collections:
   - `NON_DELETE_OPERATION_INPUT_KIND`: Mapping of operation name to input generator kind.
   - `_OPERATION_INPUT_OVERRIDE_ATTR`: Mapping of operation name to consumer override attribute.
   - `NON_DELETE_WRITE_OPERATIONS`: Frozenset of create/update operation verbs.
   - `_VALID_OPERATIONS`: Frozenset of valid model mutation operations (`create`, `update`, `delete`).
   - `_OPERATION_PERMISSION_ACTION`: Mapping of operation name to Django permission action verb.
   - `non_delete_operation_error`: Canonical error constructor for form/serializer mutation operations.

## Duplication probing matrix

| Axis | Probed? | Finding |
|---|---|---|
| 1. Cross-flavor policy mirroring | Yes | Model (`DjangoMutation`), form (`DjangoModelFormMutation`, `DjangoFormMutation`), and serializer (`SerializerMutation`) write flavors derive their operation metadata, input kinds, and error messages from this single module without duplicating vocabularies. |
| 2. Sync and async twins | Yes | Operation descriptors are static schema-time metadata consumed identically by sync and async mutation pipelines. |
| 3. Derived rather than repeated knowledge | Yes | All dictionaries and sets (`NON_DELETE_OPERATION_INPUT_KIND`, `_OPERATION_INPUT_OVERRIDE_ATTR`, `NON_DELETE_WRITE_OPERATIONS`, `_VALID_OPERATIONS`, `_OPERATION_PERMISSION_ACTION`) are derived programmatically from the canonical `MutationOperationDescriptor` declarations. |
| 4. Inverse and round-trip pairs | Yes | N/A for operation descriptors (one-way dispatch from operation verb to pipeline behavior). |
| 5. Contracts restated in another medium | Yes | Graphql-core and Strawberry schema arguments (`id`, `data`) are derived directly via `operation_takes_id` and `operation_takes_data`. |

## Single-edit-site test

### Proposed change: Add a new write operation verb (e.g. `upsert`)
- **Production ownership count**: 1 site (`django_strawberry_framework/mutations/operations.py` declaring the `MutationOperationDescriptor`).
- **Propagation count**: 3 sites (resolver dispatch handling the new verb in `mutations/resolvers.py`, unit tests in `tests/mutations/`, docs).

## Opportunities evaluated

- **Candidate 1: Centralization of mutation operation metadata**: Implemented in `django_strawberry_framework/mutations/operations.py`, removing scattered operation tables across `mutations/sets.py`, `mutations/permissions.py`, `mutations/fields.py`, and `mutations/resolvers.py`.

## Independent verification (Worker 2)

Verified that `django_strawberry_framework/mutations/operations.py` establishes single authoritative ownership over mutation operation metadata with production ownership count = 1.

<!-- LINK DEFINITIONS -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_14.md
[spec-038]: ../SPECS/spec-038-forms-0_0_14.md
[spec-039]: ../SPECS/spec-039-rest-framework-0_0_14.md
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
