"""WS-1B: store repo-relative ``SpecDoc.path``; derive the GitHub ``url``.

The GitHub blob URL is a pure function of the repo-relative path (see
``SpecDoc.url``), so ``path`` becomes the stored column and ``url`` is dropped.
The backfill strips the known ``blob/main`` prefix; the reverse rebuilds the URL
from the path so the migration round-trips.
"""

import warnings

from django.db import migrations, models

SPEC_URL_PREFIX = "https://github.com/riodw/django-strawberry-framework/blob/main"


def _backfill_path_from_url(apps, schema_editor):
    """Set ``path`` = ``url`` with the known GitHub blob prefix stripped.

    URLs that do not carry the expected GitHub blob prefix (a live-DB surprise --
    a fork, a moved repo, a hand-entered value) fall back to storing the raw URL
    as ``path`` and are collected into a single warning rather than aborting the
    migrate. The reverse rebuild is a pure function of ``path``, so a raw-URL
    fallback still round-trips faithfully.
    """
    SpecDoc = apps.get_model("kanban", "SpecDoc")
    manager = SpecDoc.objects.using(schema_editor.connection.alias)
    prefix = f"{SPEC_URL_PREFIX}/"
    unmatched = []
    for row in manager.all():
        url = row.url or ""
        if url.startswith(prefix):
            manager.filter(pk=row.pk).update(path=url[len(prefix) :])
        else:
            unmatched.append(row.name)
            manager.filter(pk=row.pk).update(path=url)
    if unmatched:
        warnings.warn(
            f"SpecDoc backfill: {len(unmatched)} url(s) did not start with "
            f"{prefix!r}; stored the raw url as path for: {', '.join(sorted(unmatched))}.",
            stacklevel=2,
        )


def _rebuild_url_from_path(apps, schema_editor):
    """Reverse: reconstruct the full GitHub URL from the repo-relative path."""
    SpecDoc = apps.get_model("kanban", "SpecDoc")
    manager = SpecDoc.objects.using(schema_editor.connection.alias)
    for row in manager.all():
        manager.filter(pk=row.pk).update(url=f"{SPEC_URL_PREFIX}/{row.path}")


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0008_targetversion_structured_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="specdoc",
            name="path",
            field=models.TextField(default=""),
        ),
        migrations.RunPython(_backfill_path_from_url, _rebuild_url_from_path),
        migrations.RemoveField(
            model_name="specdoc",
            name="url",
        ),
    ]
