"""Tests for the management commands wrapped around services.py."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from fakeshop.products.models import Category, Item
from fakeshop.products.services import create_users, seed_data

User = get_user_model()


# ---------------------------------------------------------------------------
# seed_data command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_seed_data_command_default_count():
    out = StringIO()
    call_command("seed_data", stdout=out)
    output = out.getvalue()
    assert "Done!" in output
    assert Category.objects.count() > 0


@pytest.mark.django_db
def test_seed_data_command_explicit_count():
    out = StringIO()
    call_command("seed_data", "1", stdout=out)
    assert "Done!" in out.getvalue()


# ---------------------------------------------------------------------------
# delete_data command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_data_command_int_mode():
    seed_data(2)
    out = StringIO()
    call_command("delete_data", "3", stdout=out)
    output = out.getvalue()
    assert "Deleted" in output


@pytest.mark.django_db
def test_delete_data_command_all_mode():
    seed_data(1)
    out = StringIO()
    call_command("delete_data", "all", stdout=out)
    assert "Deleted" in out.getvalue()
    assert Item.objects.count() == 0


@pytest.mark.django_db
def test_delete_data_command_everything_mode():
    seed_data(1)
    out = StringIO()
    call_command("delete_data", "everything", stdout=out)
    assert "Deleted" in out.getvalue()
    assert Category.objects.count() == 0


@pytest.mark.django_db
def test_delete_data_command_nothing_to_delete_warns():
    out = StringIO()
    call_command("delete_data", "5", stdout=out)
    assert "Nothing to delete" in out.getvalue()


@pytest.mark.django_db
def test_delete_data_command_invalid_negative():
    err = StringIO()
    call_command("delete_data", "-1", stderr=err)
    assert "positive integer" in err.getvalue()


@pytest.mark.django_db
def test_delete_data_command_invalid_string():
    err = StringIO()
    call_command("delete_data", "garbage", stderr=err)
    assert "Invalid target" in err.getvalue()


# ---------------------------------------------------------------------------
# create_users command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_users_command_default():
    out = StringIO()
    call_command("create_users", stdout=out)
    output = out.getvalue()
    assert "Done!" in output
    assert User.objects.count() == 6


@pytest.mark.django_db
def test_create_users_command_with_count():
    out = StringIO()
    call_command("create_users", "2", stdout=out)
    assert "Done!" in out.getvalue()


# ---------------------------------------------------------------------------
# delete_users command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_users_command_int_mode():
    create_users(1)
    out = StringIO()
    call_command("delete_users", "2", stdout=out)
    assert "Deleted" in out.getvalue()


@pytest.mark.django_db
def test_delete_users_command_all_mode():
    create_users(1)
    out = StringIO()
    call_command("delete_users", "all", stdout=out)
    assert "Deleted" in out.getvalue()


@pytest.mark.django_db
def test_delete_users_command_nothing_to_delete_warns():
    out = StringIO()
    call_command("delete_users", "5", stdout=out)
    assert "Nothing to delete" in out.getvalue()


@pytest.mark.django_db
def test_delete_users_command_invalid_negative():
    err = StringIO()
    call_command("delete_users", "-1", stderr=err)
    assert "positive integer" in err.getvalue()


@pytest.mark.django_db
def test_delete_users_command_invalid_string():
    err = StringIO()
    call_command("delete_users", "garbage", stderr=err)
    assert "Invalid target" in err.getvalue()


# ---------------------------------------------------------------------------
# seed_shards command
# ---------------------------------------------------------------------------


def test_seed_shards_command_raises_when_shard_alias_missing():
    """Without FAKESHOP_SHARDED=1 the ``shard_b`` alias isn't declared — must error."""
    out = StringIO()
    with pytest.raises(CommandError, match="shard_b"):
        call_command("seed_shards", stdout=out)


@pytest.mark.django_db(databases=["default"])
def test_seed_shards_command_runs_when_shard_alias_present(settings, monkeypatch):
    """When ``shard_b`` is present in DATABASES, the command runs end-to-end against ``default`` only."""
    settings.DATABASES = {
        **settings.DATABASES,
        "shard_b": settings.DATABASES["default"],  # alias both to the same test DB
    }

    # Patch SHARD_ALIASES so we only operate against ``default`` — pytest's transactional DB
    # only reaches ``default`` and we don't want to mutate production-style files.
    from fakeshop.products.management.commands import seed_shards as seed_shards_module

    monkeypatch.setattr(seed_shards_module, "SHARD_ALIASES", ("default",))

    out = StringIO()
    call_command("seed_shards", "--count", "1", stdout=out)
    output = out.getvalue()
    assert "Shards populated." in output
