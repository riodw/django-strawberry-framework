"""Domain-app namespace imported as ``apps.<app_name>`` from the fakeshop project root.

Each app owns a focused example surface: products for catalog data and seed tooling,
library for deeper relation graphs, scalars for converter coverage, and kanban/glossary
for repository docs rendered from database rows.

The namespace stays intentionally concrete: every app contributes real Django models,
schema objects, and tests that exercise django-strawberry-framework through project
configuration instead of synthetic package-only fixtures.
"""
