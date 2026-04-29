"""Dynamic data seeding service using Faker providers.

Discovers ALL Faker providers and their generator methods at runtime.
No hardcoded provider names or method lists — fully dynamic.

Quick check — print the number of detected providers and methods:

    uv run python -c "
    import django, os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'fakeshop.settings'
    django.setup()
    from fakeshop.products.services import discover_providers
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

import inspect
import pkgutil
import random
from collections.abc import Callable
from decimal import Decimal

from faker import Faker
from faker.providers import BaseProvider
from fakeshop.products.models import Category, Entry, Item, Property


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
    return isinstance(result, (str, int, float, bool, Decimal))


def discover_providers(fake: Faker) -> dict[str, list[str]]:
    """Discover all Faker providers and their no-arg generator methods.

    Returns a dict mapping provider short names to lists of callable method names.
    Each method is probed at runtime to confirm it returns a usable scalar value.
    Nothing is hardcoded — the result is entirely driven by introspecting Faker.
    """
    import faker.providers as fp

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
                    and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
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


def seed_data(count: int, db_alias: str = "default") -> dict[str, int]:
    """Seed the database with Faker-driven data for every discovered provider.

    Ensures at least ``count`` ``Item`` instances exist per provider.
    Only creates the difference if some already exist.

    For each provider (e.g. "bank", "person", "address"):
      - Creates one ``Category`` (or reuses existing)
      - Creates one ``Property`` per provider method (or reuses existing)
      - Ensures ``count`` ``Item`` instances exist (creates only the shortfall)
      - Each new ``Item`` gets one ``Entry`` per ``Property``

    ``is_private`` for Categories and Properties alternates by sorted index
    (even index → public, odd index → private) giving an exact 50/50 split
    that is deterministic across runs.  Items and Entries still use random
    assignment since their names vary per run.

    Args:
        count: Desired number of ``Item`` instances per provider.
        db_alias: DB alias to seed (default ``"default"``).  Pass
            ``"shard_a"`` / ``"shard_b"`` under the sharded settings to
            populate the shard DB files used for multi-DB local testing
            (see ``seed_shards`` management command).

    Returns:
        A summary dict with counts of newly created rows.
    """
    fake = Faker()
    providers = discover_providers(fake)

    total_categories = 0
    total_properties = 0
    total_items = 0
    total_entries = 0

    for cat_index, (provider_name, method_names) in enumerate(sorted(providers.items())):
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

        # --- Items + Entries (random is_private — names vary per run) ---
        existing_count = Item.objects.using(db_alias).filter(category=category).count()
        needed = max(0, count - existing_count)

        for _ in range(needed):
            item = Item.objects.using(db_alias).create(
                name=f"{provider_name}_{fake.uuid4()[:8]}",
                description=f"Generated {provider_name} instance",
                category=category,
                is_private=random.choice([True, False]),
            )
            total_items += 1

            entries_to_create = [
                Entry(
                    value=_fake_value(fake, prop.name),
                    description="",
                    property=prop,
                    item=item,
                    is_private=random.choice([True, False]),
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

# Shared password for all test users — makes manual login easy.
TEST_USER_PASSWORD = "admin"


def create_users(count: int = 1, db_alias: str = "default") -> dict[str, int]:
    """Create test users with individual model-view permissions.

    For each unit in ``count``, creates one user per view permission
    (4 users per unit).  Each user receives **only** the single
    permission matching their role so the schema's ``get_queryset``
    branches can be exercised independently.

    Naming: ``<permission>_<n>`` (e.g. ``view_item_1``,
    ``view_property_2``).  All users share the password
    ``TEST_USER_PASSWORD`` and are **not** staff.

    Also creates one ``staff_<n>`` superuser per unit for convenience.

    The function is idempotent — existing usernames are skipped.

    Args:
        count: Number of user sets to create.
        db_alias: DB alias to target (default ``"default"``).  Pass a
            shard alias to populate that shard instead.

    Returns:
        A summary dict with the number of newly created users.
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Permission

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
