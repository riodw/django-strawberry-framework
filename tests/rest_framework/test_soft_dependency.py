# TODO(spec-039 Slice 2): Add package tests for the DRF soft-dependency guard.
# Pseudo cases:
#   - root package import succeeds when DRF is absent;
#   - root `SerializerMutation` lookup raises the install hint when DRF is absent;
#   - `django_strawberry_framework.rest_framework` import raises the same hint;
#   - `rest_framework.sets` import raises the same hint;
#   - root lookup does not memoize `SerializerMutation` after a guarded failure.
#
# Test setup obligations:
#   - simulate absent DRF by monkeypatching import, not uninstalling the dev dep;
#   - evict both `rest_framework*` and
#     `django_strawberry_framework.rest_framework*` from `sys.modules`;
#   - delete any bound root `django_strawberry_framework.SerializerMutation`
#     attribute before asserting the absent path.
