"""Package-wide app-registry isolation for the optimizer test modules.

Every module here declares synthetic ``models.Model`` subclasses (``managed =
False``) to drive planning over relation shapes the fakeshop apps do not carry.
Django registers a model in ``django.apps.apps.all_models[app_label]`` at class
creation and nothing ever unregisters it, so without this fixture a synthetic
model outlives the test that declared it for the rest of the worker process:

* it stays visible to ``apps.get_models()`` and to any sweep that enumerates the
  registry, which is how an unrelated test's "every model" assertion acquires a
  neighbour's fixture;
* it stays wired into the relation tree of whatever real model it points at, so
  ``Category._meta.related_objects`` keeps naming a class the declaring test
  already discarded;
* re-running the declaring test in the same process re-registers the same
  ``(app_label, model_name)`` key, and Django answers that with
  ``RuntimeWarning: Model ... was already registered`` - an error under this
  suite's ``filterwarnings = error`` policy.

The fixture is autouse at package scope rather than per-module because the
invariant is the same in every module and a module that forgets to opt in is
exactly the leak this exists to stop.
"""

from typing import Any

import pytest
from django.apps import apps


@pytest.fixture(autouse=True)
def _restore_app_registry() -> Any:
    """Leave ``django.apps.apps`` holding exactly the models the test found.

    The snapshot shallow-copies each app label's inner dict; the restore writes
    back IN PLACE (``clear`` then ``update``) because ``AppConfig.import_models``
    binds ``AppConfig.models`` to the very dict object stored in
    ``all_models[label]`` - rebinding ``all_models[label]`` to a fresh dict would
    leave every installed app's ``AppConfig`` still pointing at the polluted one.
    Labels the test invented (``all_models`` is a ``defaultdict``, so declaring a
    model under an uninstalled label such as ``tests`` creates the key) are
    dropped outright.

    ``apps.clear_cache()`` runs last: ``Apps.get_models`` is cached and every
    ``_meta`` relation tree (``_relation_tree``, ``related_objects``) computed
    while the synthetic models were registered still names them, so restoring
    the registry without expiring those caches restores nothing observable.
    """
    snapshot = {label: dict(models) for label, models in apps.all_models.items()}
    try:
        yield
    finally:
        added_labels = [label for label in apps.all_models if label not in snapshot]
        changed = bool(added_labels) or any(
            apps.all_models[label] != models for label, models in snapshot.items()
        )
        if changed:
            for label, models in snapshot.items():
                live = apps.all_models[label]
                live.clear()
                live.update(models)
            for label in added_labels:
                del apps.all_models[label]
            apps.clear_cache()
