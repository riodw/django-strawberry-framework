"""Test-data factories for the kanban app.

Plain ``faker``-backed factory functions (the repo convention - see
``apps.products.services``; no ``factory_boy`` dependency). Each ``make_*``
returns a saved instance:

- **Lookup factories** (``make_status``, ``make_section`` ...) ``get_or_create`` by
  ``key`` so repeated calls reuse the one canonical row, exactly like the live
  board. Pass a ``key`` to get a specific row.
- **Domain factories** (``make_card``, ``make_card_item`` ...) create a new row
  each call, auto-filling required FKs by calling the relevant lookup/domain
  factory when one is not supplied, and computing unique ``number`` / ``order``
  values. Override any field with a keyword argument.

Example::

    from apps.kanban.factories import make_card, make_card_item

    card = make_card(title="My card")
    make_card_item(card=card, text="A scope bullet")

The ``UUIDModel`` side-table is intentionally not factoried - the
``create_uuid_row`` signal materializes it on first save of every linked model.
"""

from __future__ import annotations

import itertools

from django.db.models import Max
from faker import Faker

from apps.kanban import models

fake = Faker()
_seq = itertools.count(1).__next__


def _label(key: str) -> str:
    return key.replace("_", " ").replace("-", " ").title()


def _lookup(model, key: str, **defaults):
    """get_or_create a LookupBase-style row by ``key`` (label defaults from key)."""
    obj, _ = model.objects.get_or_create(key=key, defaults={"label": _label(key), **defaults})
    return obj


def _next_order(manager, **scope) -> int:
    current = manager.filter(**scope).aggregate(top=Max("order"))["top"]
    return 0 if current is None else current + 1


# --------------------------------------------------------------------------- #
# Lookup factories
# --------------------------------------------------------------------------- #


def make_milestone(key: str = "alpha", **defaults):
    return _lookup(models.Milestone, key, **defaults)


def make_status(key: str = "todo", **defaults):
    return _lookup(models.Status, key, **defaults)


def make_priority(key: str = "medium", **defaults):
    return _lookup(models.Priority, key, **defaults)


def make_relative_size(key: str = "m", *, order: int = 2, **defaults):
    return _lookup(models.RelativeSize, key, order=order, **defaults)


def make_upstream(key: str = "graphene_django", *, emoji: str = "⚛️", **defaults):
    return _lookup(models.Upstream, key, emoji=emoji, **defaults)


def make_parity_level(key: str = "required", **defaults):
    return _lookup(models.ParityLevel, key, **defaults)


def make_section(key: str = "scope", **defaults):
    return _lookup(models.Section, key, **defaults)


def make_card_reference_kind(key: str = "related", **defaults):
    return _lookup(models.CardReferenceKind, key, **defaults)


def make_board_doc_kind(key: str = "column", **defaults):
    return _lookup(models.BoardDocKind, key, **defaults)


def make_label(key: str | None = None, **defaults):
    key = key or f"label-{_seq()}"
    obj, _ = models.Label.objects.get_or_create(key=key, defaults=defaults)
    return obj


# --------------------------------------------------------------------------- #
# Version + spec
# --------------------------------------------------------------------------- #


def make_target_version(number: str | None = None, *, milestone=None, **defaults):
    number = number or f"0.0.{_seq()}"
    milestone = milestone or make_milestone()
    obj, _ = models.TargetVersion.objects.get_or_create(
        number=number,
        defaults={"milestone": milestone, **defaults},
    )
    return obj


def make_spec_doc(*, card=None, **fields):
    card = card or make_card()
    fields.setdefault("name", f"spec-{card.number:03d}-{fake.slug()}")
    fields.setdefault("path", f"docs/SPECS/spec-{card.number:03d}-{fake.slug()}.md")
    return models.SpecDoc.objects.create(card=card, **fields)


def make_tracked_path(path: str | None = None, **fields):
    """Create a TrackedPath (``current`` by default) under the package root."""
    path = path or f"django_strawberry_framework/factory_{_seq()}.py"
    fields.setdefault("state", models.TRACKED_PATH_CURRENT)
    fields.setdefault("is_directory", path.endswith("/"))
    obj, _ = models.TrackedPath.objects.get_or_create(path=path, defaults=fields)
    return obj


# --------------------------------------------------------------------------- #
# Card + edges
# --------------------------------------------------------------------------- #


def _next_card_number() -> int:
    current = models.Card.objects.aggregate(top=Max("number"))["top"]
    return 1 if current is None else current + 1


def make_card(**fields):
    """Create a Card, auto-filling every required FK and unique field.

    The card's milestone is derived from its target version (no stored FK).
    Passing ``status=make_status("done")`` creates the required spec and glossary
    link first, then flips the card to ``done``.
    """
    target_version = fields.pop("target_version", None) or make_target_version()
    fields.setdefault("target_version", target_version)
    fields.setdefault("status", make_status())
    fields.setdefault("priority", make_priority())
    fields.setdefault("relative_size", make_relative_size())
    fields.setdefault("number", _next_card_number())
    fields.setdefault("title", f"Card {_seq()}: {fake.sentence(nb_words=4).rstrip('.')}")
    requested_status = fields["status"]
    if requested_status.key != "done":
        return models.Card.objects.create(**fields)

    fields["status"] = make_status("todo")
    card = models.Card.objects.create(**fields)
    make_spec_doc(card=card)
    make_card_glossary_term(card=card)
    # The status state machine forbids a direct todo -> done move; bridge through
    # wip (todo -> wip -> done) so the done-card guards still fire on the final
    # save while every step is a legal transition.
    card.status = make_status("wip")
    card.save(update_fields=["status"])
    card.status = requested_status
    card.save(update_fields=["status"])
    card.refresh_from_db()
    return card


def make_card_item(*, card=None, section=None, **fields):
    card = card or make_card()
    section = section or make_section()
    fields.setdefault("text", fake.sentence())
    fields.setdefault("order", _next_order(card.items, section=section))
    return models.CardItem.objects.create(card=card, section=section, **fields)


def make_card_reference(*, source_card=None, target_card=None, kind=None, **fields):
    """Create a CardReference (the single source of truth for card edges).

    Defaults to a side-effect-free ``related`` reference. A ``dependency`` /
    ``blocked_by`` reference is a dependency edge (surfaced via
    ``Card.dependency_cards``). ``order`` is assigned per source_card by
    ``CardReference.save()``.
    """
    source_card = source_card or make_card()
    target_card = target_card or make_card()
    kind = kind or make_card_reference_kind()
    fields.setdefault("raw_text", "")
    return models.CardReference.objects.create(
        source_card=source_card,
        target_card=target_card,
        kind=kind,
        **fields,
    )


def make_card_path_link(*, card=None, path=None, **fields):
    """Create a CardPathLink through row directly (``predicted`` kind by default).

    Creating the through row via ``.objects.create()`` (rather than an M2M
    ``.add()``) emits ``post_save``, so ``create_uuid_row`` materializes the
    side-row; the M2M ``.add()`` path is wired separately by an ``m2m_changed``
    receiver.
    """
    card = card or make_card()
    path = path or make_tracked_path()
    fields.setdefault("kind", models.CARD_PATH_LINK_PREDICTED)
    return models.CardPathLink.objects.create(card=card, path=path, **fields)


def make_parity_claim(*, card=None, upstream=None, level=None):
    return models.ParityClaim.objects.create(
        card=card or make_card(),
        upstream=upstream or make_upstream(),
        level=level or make_parity_level(),
    )


def make_card_glossary_term(*, card=None, term=None, **fields):
    """Link a kanban Card to a glossary term (creates both ends if omitted)."""
    from apps.glossary.factories import make_glossary_term

    card = card or make_card()
    term = term or make_glossary_term()
    fields.setdefault("raw_text", "")
    fields.setdefault("order", _next_order(card.glossary_links))
    return models.CardGlossaryTerm.objects.create(card=card, term=term, **fields)


# --------------------------------------------------------------------------- #
# Work-tracking dimension
# --------------------------------------------------------------------------- #


def make_attempt_outcome(key: str = "succeeded", **defaults):
    return _lookup(models.AttemptOutcome, key, **defaults)


def make_verification_kind(key: str = "test_run", **defaults):
    return _lookup(models.VerificationKind, key, **defaults)


def make_actor(key: str = "maintainer", *, kind: str = models.ACTOR_HUMAN, **defaults):
    obj, _ = models.Actor.objects.get_or_create(
        key=key,
        defaults={"label": _label(key), "kind": kind, **defaults},
    )
    return obj


def make_card_transition(*, card=None, from_status=None, to_status=None, actor=None, **fields):
    card = card or make_card()
    actor = actor or make_actor()
    to_status = to_status or make_status("wip")
    return models.CardTransition.objects.create(
        card=card,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        **fields,
    )


def make_work_attempt(*, card=None, actor=None, **fields):
    card = card or make_card()
    actor = actor or make_actor()
    return models.WorkAttempt.objects.create(card=card, actor=actor, **fields)


_UNSET = object()


def make_decision(*, card=_UNSET, actor=None, **fields):
    """Create a Decision.

    A card is auto-created when omitted; pass ``card=None`` explicitly for a
    board-level decision.
    """
    card = make_card() if card is _UNSET else card
    actor = actor or make_actor()
    fields.setdefault("question", fake.sentence())
    fields.setdefault("choice", fake.sentence())
    return models.Decision.objects.create(card=card, actor=actor, **fields)


def make_board_doc(*, kind=None, **fields):
    kind = kind or make_board_doc_kind()
    fields.setdefault("namespace", "kanban")
    fields.setdefault("key", f"doc-{_seq()}")
    fields.setdefault("title", fake.sentence(nb_words=3).rstrip("."))
    fields.setdefault("body", fake.paragraph())
    return models.BoardDoc.objects.create(kind=kind, **fields)


def make_board_doc_card_reference(*, doc=None, card=None, **fields):
    doc = doc or make_board_doc()
    card = card or make_card()
    fields.setdefault("raw_text", "")
    fields.setdefault("order", _next_order(doc.card_references))
    return models.BoardDocCardReference.objects.create(doc=doc, card=card, **fields)
