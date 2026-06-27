# TODO(spec-039 Slice 2): Add package tests for the DRF soft-dependency guard.
# Pseudo cases:
#   - root package import succeeds when DRF is absent;
#   - root `SerializerMutation` lookup raises the install hint when DRF is absent;
#   - `django_strawberry_framework.rest_framework` import raises the same hint;
#   - `rest_framework.sets` import raises the same hint;
#   - `from django_strawberry_framework import *` succeeds without DRF and binds
#     no `SerializerMutation`;
#   - `SerializerMutation` is absent from root `__all__` while DRF is soft;
#   - root lookup does not memoize `SerializerMutation` after success or failure.
#
# Test setup obligations:
#   - simulate absent DRF by monkeypatching import, not uninstalling the dev dep;
#   - evict both `rest_framework*` and
#     `django_strawberry_framework.rest_framework*` from `sys.modules`;
#   - delete any bound root `django_strawberry_framework.SerializerMutation`
#     attribute before asserting the absent path.
