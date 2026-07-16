"""Domain-app namespace imported as ``apps.<app_name>`` from the fakeshop project root.

Each app owns a focused example surface: accounts for session auth, products for
catalog and write APIs, library for relation and mutation matrices, scalars for
converter and upload coverage, and kanban/glossary for repository docs rendered from
database rows.

The namespace stays concrete: model-backed apps contribute real models, schema objects,
and app-local tests, while schema-only accounts exercises Django's ``auth.User``
through the shared live HTTP suite.
"""
