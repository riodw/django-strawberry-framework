"""Test-data factories for the glossary app.

Plain ``faker``-backed factory functions (the repo convention — see
``apps.products.services``; no ``factory_boy`` dependency). Each ``make_*``
returns a saved instance:

- **Lookup factories** (``make_glossary_status`` …) ``get_or_create`` by ``key``
  so repeated calls reuse the one canonical row.
- **Domain factories** (``make_glossary_term`` …) create a new row each call,
  auto-filling required FKs and computing unique ``anchor`` / ``order`` values.
  Override any field with a keyword argument.

Example::

    from apps.glossary.factories import make_glossary_term, make_glossary_alias

    term = make_glossary_term(title="`FilterSet`")
    make_glossary_alias(term=term, label="filter set")
"""

from __future__ import annotations

import itertools

from django.db.models import Max
from faker import Faker

from apps.glossary import models

fake = Faker()
_seq = itertools.count(1).__next__


def _label(key: str) -> str:
    return key.replace("_", " ").replace("-", " ").title()


def _lookup(model, key: str, **defaults):
    obj, _ = model.objects.get_or_create(key=key, defaults={"label": _label(key), **defaults})
    return obj


def _next_order(manager, **scope) -> int:
    current = manager.filter(**scope).aggregate(top=Max("order"))["top"]
    return 0 if current is None else current + 1


# --------------------------------------------------------------------------- #
# Lookup factories
# --------------------------------------------------------------------------- #


def make_glossary_status(key: str = "shipped", **defaults):
    return _lookup(models.GlossaryStatus, key, **defaults)


def make_glossary_category(key: str = "filtering", **defaults):
    return _lookup(models.GlossaryCategory, key, **defaults)


def make_glossary_term_link_kind(key: str = "see_also", **defaults):
    return _lookup(models.GlossaryTermLinkKind, key, **defaults)


# --------------------------------------------------------------------------- #
# Term + edges
# --------------------------------------------------------------------------- #


def make_glossary_term(*, status=None, **fields):
    """Create a GlossaryTerm with unique ``title`` / ``title_sort`` / ``anchor``."""
    status = status or make_glossary_status()
    n = _seq()
    word = fake.word()
    fields.setdefault("title", f"`{word}{n}`")
    fields.setdefault("title_sort", f"{word}{n}".lower())
    fields.setdefault("anchor", f"{word}{n}".lower())
    fields.setdefault("status_text", "shipped (`0.0.8`)")
    fields.setdefault("body", fake.paragraph())
    fields.setdefault("entry_order", n)
    fields.setdefault("index_order", n)
    return models.GlossaryTerm.objects.create(status=status, **fields)


def make_glossary_alias(*, term=None, **fields):
    term = term or make_glossary_term()
    label = fields.pop("label", None) or f"{fake.word()} {_seq()}"
    fields.setdefault("label", label)
    fields.setdefault("normalized", label.lower())
    return models.GlossaryAlias.objects.create(term=term, **fields)


def make_glossary_term_link(*, source_term=None, target_term=None, kind=None, **fields):
    source_term = source_term or make_glossary_term()
    target_term = target_term or make_glossary_term()
    kind = kind or make_glossary_term_link_kind()
    fields.setdefault("raw_label", "")
    fields.setdefault("order", _next_order(source_term.outgoing_links, kind=kind))
    return models.GlossaryTermLink.objects.create(
        source_term=source_term,
        target_term=target_term,
        kind=kind,
        **fields,
    )


def make_glossary_category_membership(*, category=None, term=None, **fields):
    category = category or make_glossary_category()
    term = term or make_glossary_term()
    fields.setdefault("order", _next_order(category.memberships))
    return models.GlossaryCategoryMembership.objects.create(
        category=category,
        term=term,
        **fields,
    )


def make_glossary_spec_mention(*, term=None, **fields):
    term = term or make_glossary_term()
    fields.setdefault("spec_path", f"docs/SPECS/spec-{_seq():03d}-{fake.slug()}.md")
    fields.setdefault("term_text", fake.word())
    fields.setdefault("notes", "")
    fields.setdefault("order", _next_order(term.spec_mentions))
    return models.GlossarySpecMention.objects.create(term=term, **fields)


def make_glossary_source_link(*, term=None, **fields):
    term = term or make_glossary_term()
    fields.setdefault("label", fake.sentence(nb_words=3).rstrip("."))
    fields.setdefault("target", fake.url())
    fields.setdefault("kind", "")
    fields.setdefault("order", _next_order(term.source_links))
    return models.GlossarySourceLink.objects.create(term=term, **fields)
