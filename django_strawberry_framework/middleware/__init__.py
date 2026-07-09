"""Django HTTP middleware integrations for django-strawberry-framework.

Import-clean by design: this package marker imports nothing optional, so
``import django_strawberry_framework.middleware`` succeeds on machines without
django-debug-toolbar and whole-package walkers (the ``docs/TREE.md`` renderer,
coverage collection) traverse it safely. The consumer-facing surface is the
full leaf dotted path in a ``MIDDLEWARE`` settings string
(``django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware``);
there is deliberately NO re-export here - importing the leaf module is the
soft-dependency opt-in (spec-042 Decisions 3/4/5).
"""
