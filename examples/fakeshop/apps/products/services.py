"""Faker catalog seeding, user lifecycle, cascade fixtures, and catalog cleanup services.

Discovers ALL Faker providers and their generator methods at runtime.
No hardcoded provider names or method lists - fully dynamic.

The module also creates and deletes permission-shaped test users, deletes catalog
subsets or whole fixtures, and builds deterministic cascade-visibility data.

Quick check - print the number of detected providers and methods:

    uv run python -c "
    import django, os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    django.setup()
    from apps.products.services import discover_providers
    from faker import Faker
    p = discover_providers(Faker())
    print(f'{len(p)} providers, {sum(len(m) for m in p.values())} methods')
    "

Expected output (Faker 40.15.0): 25 providers, 174 methods

Estimating created rows for a given count (X):

    Category   = 25              (one per provider)
    Property   = 174             (one per method)
    Item       = 25 * X          (X items per provider)
    Entry      = 174 * X         (one entry per property per item)
    ---
    Total rows = 25 + 174 + (25 * X) + (174 * X)
               = 199 + 199X

    Examples:
        X=1   ->    398 rows
        X=5   ->   1194 rows
        X=50  ->  10149 rows
"""

from __future__ import annotations

import inspect
import pkgutil
import random
from collections.abc import Callable
from decimal import Decimal
from functools import cache
from typing import TYPE_CHECKING

from apps.products.models import Category, Entry, Item, Property

if TYPE_CHECKING:
    from faker import Faker


def _is_safe_generator(fake: Faker, method_name: str) -> bool:
    """Probe a Faker method by calling it once to check it returns a usable string value.

    Rejects methods that return non-scalar types (bytes, dicts, lists, tuples, etc.)
    or raise exceptions when called with no arguments.
    """
    try:
        result = getattr(fake, method_name)()
    except Exception:
        return False

    # Only accept simple scalar types that can be meaningfully stored as text
    return isinstance(
        result,
        (
            str,
            int,
            float,
            bool,
            Decimal,
        ),
    )


def discover_providers(fake: Faker) -> dict[str, list[str]]:
    """Discover all Faker providers and their no-arg generator methods.

    Returns a dict mapping provider short names to lists of callable method names.
    Each method is probed at runtime to confirm it returns a usable scalar value.
    Nothing is hardcoded - the result is entirely driven by introspecting Faker.
    """
    import faker.providers as fp
    from faker.providers import BaseProvider

    base_methods = set(dir(BaseProvider))

    providers: dict[str, list[str]] = {}

    for _importer, modname, ispkg in pkgutil.walk_packages(fp.__path__, fp.__name__ + "."):
        if not ispkg:
            continue

        short_name = modname.replace("faker.providers.", "")

        # Only use top-level providers (skip locale sub-packages like "address.en_US")
        if "." in short_name:
            continue

        try:
            mod = __import__(modname, fromlist=["Provider"])
        except ImportError:
            continue

        if not hasattr(mod, "Provider"):
            continue

        provider_cls = mod.Provider
        methods: list[str] = []

        for name in sorted(dir(provider_cls)):
            if name.startswith("_") or name in base_methods:
                continue

            attr = getattr(provider_cls, name, None)
            if attr is None or not callable(attr) or isinstance(attr, property):
                continue

            # Only include methods with no required args beyond self
            try:
                sig = inspect.signature(attr)
                params = list(sig.parameters.values())
                required = [
                    p
                    for p in params[1:]  # skip self
                    if p.default is inspect.Parameter.empty
                    and p.kind
                    not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                ]
                if len(required) != 0:
                    continue
            except (ValueError, TypeError):
                continue

            # Probe the method to verify it returns a usable scalar
            if _is_safe_generator(fake, name):
                methods.append(name)

        if methods:
            providers[short_name] = methods

    return providers


def _fake_value(fake: Faker, method_name: str) -> str:
    """Call a Faker method and return its result as a string."""
    fn: Callable = getattr(fake, method_name)
    result = fn()
    return str(result)


# Item/Entry privacy is drawn from this fixed-seed stream rather than the process
# RNG: an unseeded draw makes every derived expectation probabilistic, and a run
# that happens to hide the whole Item -> Category chain turns a prefetch-count
# assertion into a false failure.
PRIVACY_STREAM_SEED = 20260827


@cache
def _seed_provider_methods() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Discover the process-stable provider shape used by repeated seed calls."""
    from faker import Faker

    probe = Faker()
    probe.seed_instance(0)
    return tuple(
        (provider_name, tuple(method_names))
        for provider_name, method_names in sorted(discover_providers(probe).items())
    )


def seed_data(count: int, db_alias: str = "default") -> dict[str, int]:
    """Seed the database with Faker-driven data for every discovered provider.

    Ensures at least ``count`` ``Item`` instances exist per provider.
    Only creates the difference if some already exist.
    Provider discovery is deterministic and cached per process; installed Faker
    provider modules do not change between calls, while generated row values remain
    fresh on every invocation.

    For each provider (e.g. "bank", "person", "address"):
      - Creates one ``Category`` (or reuses existing)
      - Creates one ``Property`` per provider method (or reuses existing)
      - Ensures ``count`` ``Item`` instances exist (creates only the shortfall)
      - Each new ``Item`` gets one ``Entry`` per ``Property``

    ``is_private`` for Categories and Properties alternates by sorted index
    (even index -> public, odd index -> private) giving an exact 50/50 split
    that is deterministic across runs.  Items and Entries draw theirs from a
    fixed-seed stream (``PRIVACY_STREAM_SEED``), so the mix stays uncorrelated
    with the index parities above while the visible set a caller derives is the
    same on every run.  Only the Faker-generated text varies per run.

    Args:
        count: Desired number of ``Item`` instances per provider.
        db_alias: DB alias to seed (default ``"default"``).  Pass
            ``"shard_a"`` / ``"shard_b"`` under the sharded settings to
            populate the shard DB files used for multi-DB local testing
            (see ``seed_shards`` management command).

    Returns:
        A summary dict with counts of newly created rows.
    """
    from faker import Faker

    fake = Faker()
    privacy = random.Random(PRIVACY_STREAM_SEED)

    total_categories = 0
    total_properties = 0
    total_items = 0
    total_entries = 0

    for cat_index, (provider_name, method_names) in enumerate(_seed_provider_methods()):
        # --- Category (alternating: even=public, odd=private) ---
        category, created = Category.objects.using(db_alias).get_or_create(
            name=provider_name,
            defaults={
                "description": f"Auto-generated from Faker's {provider_name} provider",
                "is_private": cat_index % 2 == 1,
            },
        )
        if created:
            total_categories += 1

        # --- Properties (alternating within each provider) ---
        properties: list[Property] = []
        for prop_index, method_name in enumerate(method_names):
            prop, created = Property.objects.using(db_alias).get_or_create(
                name=method_name,
                category=category,
                defaults={
                    "description": f"{provider_name}.{method_name}",
                    "is_private": prop_index % 2 == 1,
                },
            )
            properties.append(prop)
            if created:
                total_properties += 1

        # --- Items + Entries (fixed-seed is_private - names vary per run) ---
        existing_count = Item.objects.using(db_alias).filter(category=category).count()
        needed = max(0, count - existing_count)

        for _ in range(needed):
            item = Item.objects.using(db_alias).create(
                name=f"{provider_name}_{fake.uuid4()[:8]}",
                description=f"Generated {provider_name} instance",
                category=category,
                is_private=privacy.choice([True, False]),
            )
            total_items += 1

            entries_to_create = [
                Entry(
                    value=_fake_value(fake, prop.name),
                    description="",
                    property=prop,
                    item=item,
                    is_private=privacy.choice([True, False]),
                )
                for prop in properties
            ]
            Entry.objects.using(db_alias).bulk_create(entries_to_create)
            total_entries += len(entries_to_create)

    return {
        "categories": total_categories,
        "properties": total_properties,
        "items": total_items,
        "entries": total_entries,
    }


# --------------------------------------------------------------------------- #
# User seeding
# --------------------------------------------------------------------------- #

# The four model-level view permissions used by schema.py get_queryset branches.
VIEW_PERMISSIONS = [
    "view_category",
    "view_item",
    "view_property",
    "view_entry",
]

# Shared password for all test users - makes manual login easy.
TEST_USER_PASSWORD = "admin"


def create_users(count: int = 1, db_alias: str = "default") -> dict[str, int]:
    """Create test users with individual model-view permissions.

    For each unit in ``count``, creates one user per view permission
    (4 users per unit).  Each user receives **only** the single
    permission matching their role so the schema's ``get_queryset``
    branches can be exercised independently.

    Naming: ``<permission>_<n>`` (e.g. ``view_item_1``,
    ``view_property_2``).  All users share the password
    ``TEST_USER_PASSWORD``.  The permission users and ``regular_<n>``
    are **not** staff.

    Also creates one ``staff_<n>`` (``is_staff=True``) and one
    unprivileged ``regular_<n>`` per unit.  ``staff_<n>`` is
    deliberately NOT a superuser: the live write-authorization tier
    needs it to run the real permission checks rather than
    short-circuit on ``is_superuser``, and ``delete_users`` - which
    never deletes superusers - must be able to remove it.

    The function is idempotent - existing usernames are skipped.

    Args:
        count: Number of user sets to create.
        db_alias: DB alias to target (default ``"default"``).  Pass a
            shard alias to populate that shard instead.

    Returns:
        A summary dict with the number of newly created users.
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Permission
    from faker import Faker

    User = get_user_model()
    user_manager = User.objects.db_manager(db_alias)
    perm_manager = Permission.objects.db_manager(db_alias)
    created = 0

    fake = Faker()

    for n in range(1, count + 1):
        last_name = fake.last_name()

        # --- Staff user ---
        username = f"staff_{n}"
        if not user_manager.filter(username=username).exists():
            user_manager.create_user(
                username=username,
                password=TEST_USER_PASSWORD,
                is_staff=True,
                first_name="Staff",
                last_name=last_name,
            )
            created += 1

        # --- Regular user (no permissions, not staff) ---
        username = f"regular_{n}"
        if not user_manager.filter(username=username).exists():
            user_manager.create_user(
                username=username,
                password=TEST_USER_PASSWORD,
                is_staff=False,
                first_name="Regular",
                last_name=last_name,
            )
            created += 1

        # --- Per-permission users ---
        for perm_codename in VIEW_PERMISSIONS:
            username = f"{perm_codename}_{n}"
            if not user_manager.filter(username=username).exists():
                # e.g. "view_item" -> "View Item"
                first_name = perm_codename.replace("_", " ").title()
                user = user_manager.create_user(
                    username=username,
                    password=TEST_USER_PASSWORD,
                    is_staff=False,
                    first_name=first_name,
                    last_name=last_name,
                )
                perm = perm_manager.get(
                    codename=perm_codename,
                    content_type__app_label="products",
                )
                user.user_permissions.add(perm)
                created += 1

    return {"users": created}


def delete_users(target: int | str) -> dict[str, int]:
    """Delete test users created by ``create_users``.

    Superusers (``is_superuser=True``) are **never** deleted.

    Modes:
      - ``target`` is an **int**: delete the first *target* non-superusers
        (by primary key order).
      - ``target == "all"``: delete every non-superuser.

    Returns a summary dict with counts of deleted users.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    result: dict[str, int] = {"users": 0}

    if target == "all":
        qs = User.objects.exclude(is_superuser=True)
        result["users"] = qs.count()
        qs.delete()
    else:
        count = int(target)
        qs = User.objects.exclude(is_superuser=True).order_by("pk")
        pks = list(qs.values_list("pk", flat=True)[:count])
        if pks:
            result["users"] = len(pks)
            User.objects.filter(pk__in=pks).delete()

    return result


def delete_data(target: int | str) -> dict[str, int]:
    """Delete data from the database.

    Modes:
      - ``target`` is an **int**: delete the first *target* ``Item`` rows
        (by primary key order). Related ``Entry`` rows cascade automatically.
      - ``target == "all"``: delete every ``Item`` and ``Entry``.
      - ``target == "everything"``: wipe all four tables
        (``Entry``, ``Item``, ``Property``, ``Category``).

    Returns a summary dict with counts of deleted rows per model.
    """
    result: dict[str, int] = {
        "categories": 0,
        "properties": 0,
        "items": 0,
        "entries": 0,
    }

    if target == "everything":
        result["entries"] = Entry.objects.all().count()
        result["items"] = Item.objects.all().count()
        result["properties"] = Property.objects.all().count()
        result["categories"] = Category.objects.all().count()
        # Delete in FK-safe order
        Entry.objects.all().delete()
        Item.objects.all().delete()
        Property.objects.all().delete()
        Category.objects.all().delete()

    elif target == "all":
        result["entries"] = Entry.objects.all().count()
        result["items"] = Item.objects.all().count()
        Entry.objects.all().delete()
        Item.objects.all().delete()

    else:
        count = int(target)
        pks = list(Item.objects.order_by("pk").values_list("pk", flat=True)[:count])
        if pks:
            result["entries"] = Entry.objects.filter(item__pk__in=pks).count()
            Entry.objects.filter(item__pk__in=pks).delete()
            result["items"] = Item.objects.filter(pk__in=pks).count()
            Item.objects.filter(pk__in=pks).delete()

    return result


# Every row the named fixture helpers below create is named with a ``zzz_`` prefix,
# and that prefix is a grammar rather than a habit:
#
# * ``seed_data`` names its rows after Faker providers and methods, none of which
#   begin with ``zzz_``. A fixture row therefore never collides with a catalog row,
#   and a name-ordered page always ends with the fixture rows.
# * ``Category.name`` is unique across the WHOLE table
#   (``examples/fakeshop/apps/products/models.py::Category``), while ``Item.name``
#   and ``Property.name`` are unique only within their category
#   (``unique_item_per_category`` / ``unique_property_per_category``). So a category
#   name belongs to this module, not to the helper that writes it: two helpers one
#   test calls together collide on a shared category name and raise
#   ``IntegrityError`` at seed time rather than showing up as a visible-rows
#   difference.
#
# ``examples/fakeshop/apps/products/tests/test_services.py::test_every_named_fixture_helper_seeds_into_one_database``
# holds that second rule, by calling every helper below against one database.


def seed_cascade_split(db_alias: str = "default") -> dict[str, object]:
    """Seed a deterministic private/public 2-deep chain for cascade-visibility tests.

    The named seed helper for the cascade live tests (the "seed-helper tests are the
    only exception" carve-out in ``AGENTS.md`` -- catalog rows for live tests are
    created here, not hand-rolled in the test module). Unlike ``seed_data`` (whose
    ``is_private`` flags are randomized / index-parity), this builds a FIXED split so
    per-edge cascade narrowing is observable:

    * a PRIVATE category holding a PUBLIC item and a PUBLIC property, carrying a
      PUBLIC entry -- everything below the category is public, so only the category's
      privacy can hide the entry through the cascade;
    * a PUBLIC category holding the mirror public item / property / entry (a fully
      visible control chain);
    * two mixed-edge PUBLIC entries that isolate one hop each: item under the
      private category with a public-category property, and the reverse. Either
      hop alone must hide the entry; a both-private chain cannot tell them apart.

    Returns the key rows so a test can assert against them by identity.
    """
    private_cat = Category.objects.using(db_alias).create(name="zzz_private_cat", is_private=True)
    public_cat = Category.objects.using(db_alias).create(name="zzz_public_cat", is_private=False)

    priv_prop = Property.objects.using(db_alias).create(
        name="priv_prop",
        category=private_cat,
        is_private=False,
    )
    pub_prop = Property.objects.using(db_alias).create(
        name="pub_prop",
        category=public_cat,
        is_private=False,
    )

    item_under_private = Item.objects.using(db_alias).create(
        name="zzz_item_under_private",
        category=private_cat,
        is_private=False,
    )
    item_under_public = Item.objects.using(db_alias).create(
        name="zzz_item_under_public",
        category=public_cat,
        is_private=False,
    )

    entry_under_private = Entry.objects.using(db_alias).create(
        value="zzz_entry_under_private",
        property=priv_prop,
        item=item_under_private,
        is_private=False,
    )
    entry_under_public = Entry.objects.using(db_alias).create(
        value="zzz_entry_under_public",
        property=pub_prop,
        item=item_under_public,
        is_private=False,
    )
    entry_via_private_item = Entry.objects.using(db_alias).create(
        value="zzz_entry_via_private_item",
        property=pub_prop,
        item=item_under_private,
        is_private=False,
    )
    entry_via_private_property = Entry.objects.using(db_alias).create(
        value="zzz_entry_via_private_property",
        property=priv_prop,
        item=item_under_public,
        is_private=False,
    )
    return {
        "private_cat": private_cat,
        "public_cat": public_cat,
        "priv_prop": priv_prop,
        "pub_prop": pub_prop,
        "item_under_private": item_under_private,
        "item_under_public": item_under_public,
        "entry_under_private": entry_under_private,
        "entry_under_public": entry_under_public,
        "entry_via_private_item": entry_via_private_item,
        "entry_via_private_property": entry_via_private_property,
    }


# The two row names ``seed_decoy_and_target_rows`` is read by name for. Exported so a
# ``get_queryset`` hook can name those rows without hand-rolling them; every other
# fixture below is asserted against by identity and needs no constant.
DECOY_CATEGORY_NAME = "zzz_decoy_category"
TARGET_ITEM_NAME = "zzz_target_item"


def seed_cascade_identity_chain(db_alias: str = "default") -> dict[str, object]:
    """Seed one public ``Category -> Item + Property -> Entry`` chain.

    The minimal shape for the identity-hook cascade rows: every edge is public, so
    a registered target contributes a subquery without narrowing anything and the
    entry survives. Returns each row so a test asserts by identity, not by name.
    """
    category = Category.objects.using(db_alias).create(name="zzz_identity_cat")
    item = Item.objects.using(db_alias).create(name="zzz_identity_item", category=category)
    prop = Property.objects.using(db_alias).create(name="zzz_identity_prop", category=category)
    entry = Entry.objects.using(db_alias).create(
        value="zzz_identity_entry",
        item=item,
        property=prop,
    )
    return {
        "category": category,
        "item": item,
        "property": prop,
        "entry": entry,
    }


def seed_public_category_with_item(db_alias: str = "default") -> dict[str, object]:
    """Seed one public ``Category`` holding one public ``Item``.

    The control fixture for rows that assert a permissive hook leaves the item
    visible: nothing in the chain is private, so any narrowing that shows up came
    from the walk under test rather than from the data.
    """
    category = Category.objects.using(db_alias).create(name="zzz_control_cat", is_private=False)
    item = Item.objects.using(db_alias).create(
        name="zzz_control_item",
        category=category,
        is_private=False,
    )
    return {"category": category, "item": item}


def seed_field_scope_split(db_alias: str = "default") -> dict[str, object]:
    """Seed public/hidden ``Item`` and ``Property`` rows under one public category.

    Three entries isolate the two cascade edges: one wholly public, one whose item
    is hidden, and one whose property is hidden. Scoping the walk to a single edge
    must keep the entry whose OTHER edge is the hidden one.
    """
    category = Category.objects.using(db_alias).create(name="zzz_scope_cat")
    public_item = Item.objects.using(db_alias).create(name="zzz_pub_item", category=category)
    hidden_item = Item.objects.using(db_alias).create(
        name="zzz_hidden_item",
        category=category,
        is_private=True,
    )
    public_prop = Property.objects.using(db_alias).create(
        name="zzz_pub_prop",
        category=category,
    )
    hidden_prop = Property.objects.using(db_alias).create(
        name="zzz_hidden_prop",
        category=category,
        is_private=True,
    )
    keeps = Entry.objects.using(db_alias).create(
        value="zzz_keeps",
        item=public_item,
        property=public_prop,
    )
    drops_item = Entry.objects.using(db_alias).create(
        value="zzz_drops_item",
        item=hidden_item,
        property=public_prop,
    )
    survives_prop = Entry.objects.using(db_alias).create(
        value="zzz_survives_prop",
        item=public_item,
        property=hidden_prop,
    )
    return {
        "category": category,
        "public_item": public_item,
        "hidden_item": hidden_item,
        "public_prop": public_prop,
        "hidden_prop": hidden_prop,
        "keeps": keeps,
        "drops_item": drops_item,
        "survives_prop": survives_prop,
    }


def seed_gate_name_split(db_alias: str = "default") -> dict[str, object]:
    """Seed one public and one hidden ``Category`` for the gated-``name`` filter rows.

    A gate walks the filter INPUT, so the hidden row is what proves a passing input
    still cannot recover a row the cascade already dropped.
    """
    public = Category.objects.using(db_alias).create(name="zzz_gate_public", is_private=False)
    hidden = Category.objects.using(db_alias).create(name="zzz_gate_name_hidden", is_private=True)
    return {"public": public, "hidden": hidden}


def seed_gate_order_split(db_alias: str = "default") -> dict[str, object]:
    """Seed two public ``Category`` rows out of alphabetical order, plus a hidden one.

    Insertion order deliberately contradicts name order so an ascending sort is
    observable, and the hidden row pins that ordering arranges only what the
    cascade left visible.
    """
    beta = Category.objects.using(db_alias).create(name="zzz_gate_beta", is_private=False)
    alpha = Category.objects.using(db_alias).create(name="zzz_gate_alpha", is_private=False)
    hidden = Category.objects.using(db_alias).create(name="zzz_gate_order_hidden", is_private=True)
    return {"alpha": alpha, "beta": beta, "hidden": hidden}


def seed_gate_existence_split(db_alias: str = "default") -> dict[str, object]:
    """Seed a public and a private ``Category``, each holding one public ``Item``.

    The no-existence-leak fixture: the item under the private category is dropped
    by the cascade itself, so deleting that chain changes the data without changing
    the visible rows - which is what makes two gate denials comparable.
    """
    public_cat = Category.objects.using(db_alias).create(
        name="zzz_leak_public_cat",
        is_private=False,
    )
    private_cat = Category.objects.using(db_alias).create(
        name="zzz_leak_private_cat",
        is_private=True,
    )
    visible_item = Item.objects.using(db_alias).create(
        name="zzz_leak_visible_item",
        category=public_cat,
        is_private=False,
    )
    hidden_item = Item.objects.using(db_alias).create(
        name="zzz_leak_hidden_item",
        category=private_cat,
        is_private=False,
    )
    return {
        "public_cat": public_cat,
        "private_cat": private_cat,
        "visible_item": visible_item,
        "hidden_item": hidden_item,
    }


def seed_decoy_and_target_rows(db_alias: str = "default") -> dict[str, object]:
    """Seed a ``Category`` no query returns beside a ``Category`` holding one ``Item``.

    The decoy row exists only so a test can prove the answer came from the ``Item``
    table: a walk that resolved against ``Category`` instead would surface
    ``DECOY_CATEGORY_NAME``. Names are module constants so a ``get_queryset`` hook
    can name the rows without creating them.
    """
    decoy = Category.objects.using(db_alias).create(name=DECOY_CATEGORY_NAME)
    holder = Category.objects.using(db_alias).create(name="zzz_target_category")
    item = Item.objects.using(db_alias).create(name=TARGET_ITEM_NAME, category=holder)
    return {"decoy": decoy, "holder": holder, "item": item}
