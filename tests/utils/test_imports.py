"""Pending tests for the shared optional-import raising guard (spec-041 Slice 1)."""

# TODO(spec-041 Slice 1): add executable tests for
# ``utils/imports.py::require_optional_module`` before ``routers.py`` uses it.
#
# TODO(spec-041 Slice 1) pseudo-test plan:
# - success case: require the always-present ``sys`` module and assert the
#   returned object is the real ``sys`` module;
# - absence case: require a deliberately missing package and assert the raised
#   ``ImportError`` contains the supplied hint and chains the original error;
# - non-memoization case: monkeypatch ``importlib.import_module`` to record calls,
#   require the same module twice, and assert the importer was invoked twice.
#
# Keep these tests generic. Router-specific hint wording and channels-absence
# behavior belong in ``tests/test_routers.py`` so the utility owner remains
# portable for future soft dependencies.
