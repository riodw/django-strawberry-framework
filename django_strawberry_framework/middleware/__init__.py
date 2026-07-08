"""Django HTTP middleware integrations for django-strawberry-framework."""

# TODO(spec-042 Slice 1): Keep this package marker import-clean on machines
# without django-debug-toolbar. Do not re-export DebugToolbarMiddleware here;
# the consumer-facing public surface is the full leaf dotted path in MIDDLEWARE:
# ``django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware``.
