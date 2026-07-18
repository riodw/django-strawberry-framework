"""Django settings for fakeshop's SQLite, sharded-SQLite, and Postgres modes."""

import os
from pathlib import Path

# Build paths inside the example project root like this: BASE_DIR / "subdir"
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = "_$=$%eqxk$8ss4n7mtgarw^5$8^d5+c83!vwatr@i_81myb=e4"

DEBUG = True

ALLOWED_HOSTS = []

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

APPEND_SLASH = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Apps & Middleware
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    # spec-042 opt-in: django-debug-toolbar's SQL-panel window into ``/graphql/``
    # requests, wired via ``django_strawberry_framework.middleware.debug_toolbar``
    # (the MIDDLEWARE + INTERNAL_IPS entries below and ``debug_toolbar_urls()`` in
    # config/urls.py). Needs ``django.contrib.staticfiles`` (above); the framework
    # app (below) supplies the GraphiQL bridge template via the app-dirs loader.
    "debug_toolbar",
    "django_strawberry_framework",
    # NOTE(spec-039 Slice 3): `"rest_framework"` is intentionally NOT installed. The
    # products `ItemSerializer` is a flat `ModelSerializer` whose validation +
    # `UniqueTogetherValidator` need no DRF app registry (Decision 13 / spec line
    # 969); DRF being a dev-group dependency keeps it importable in the test context.
    # Local
    # spec-040 Slice 1: the schema-only accounts app supplies the example
    # ``UserType`` over ``auth.User`` so ``apps.accounts.schema`` can register it
    # and the auth ``login`` / ``logout`` surface resolves at finalize.
    "apps.accounts.apps.AccountsConfig",
    "apps.library.apps.LibraryConfig",
    "apps.products.apps.ProductsConfig",
    "apps.scalars.apps.ScalarsConfig",
    "apps.kanban.apps.KanbanConfig",
    "apps.glossary.apps.GlossaryConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # spec-042: our subclass of debug-toolbar's middleware, listed as early as
    # possible (after SecurityMiddleware, before any body-encoding middleware).
    # It REPLACES the stock ``debug_toolbar.middleware.DebugToolbarMiddleware`` --
    # listing both would run the toolbar twice.
    "django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# spec-042: django-debug-toolbar's default ``SHOW_TOOLBAR_CALLBACK`` renders the
# toolbar only when ``DEBUG`` is true (it is, above) AND the request IP is in
# ``INTERNAL_IPS`` -- so the panels appear for local ``/graphql/`` traffic only.
INTERNAL_IPS = ["127.0.0.1"]


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Database mode - additive
# ---------------------------------------------------------------------------
# Two modes, toggled by the ``FAKESHOP_SHARDED`` env var:
#
#   unset       - single-DB.  Only ``default`` (-> ``db.sqlite3``) exists.
#
#   "1"         - sharded.    ``default`` (-> ``db.sqlite3``, same file as
#                 single-DB mode) plus ``shard_b`` (-> ``db_shard_b.sqlite3``).
#                 The two modes share the same ``default`` file, so a single
#                 dev workflow (``manage.py seed_data``, etc.) populates the
#                 ``default`` alias in both modes; sharded mode only ADDS the
#                 secondary shard.
#
# Django requires a ``default`` entry; we keep that entry pointed at
# ``db.sqlite3`` in both modes. All ``Model.objects.create(...)`` calls
# without ``.using(...)`` land on the default file; explicit
# ``.using("shard_b")`` targets the secondary shard SQLite file.
#
# The library itself is agnostic to this layout - it simply honours
# whatever alias the caller queryset carries via ``queryset.db``.
#
# Usage:
#     uv run pytest                                                 # single-DB
#     FAKESHOP_SHARDED=1 uv run pytest                              # sharded
#     FAKESHOP_SHARDED=1 uv run python manage.py seed_shards        # populate shard_b
# ``DJANGO_STRAWBERRY_KANBAN_DB`` points the default SQLite alias at an alternate
# file. Used by the ``scripts/build_kanban_*`` / ``build_glossary_md`` / ``build_tree_md``
# render tooling to run against a migrated COPY of ``db.sqlite3`` without touching the
# live board file (the live file may trail the code's migration state while parallel
# sessions write it). Unset in every normal workflow, so it never changes live behavior.
_kanban_db = os.environ.get("DJANGO_STRAWBERRY_KANBAN_DB")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _kanban_db or (BASE_DIR / "db.sqlite3"),
    },
}
if os.environ.get("FAKESHOP_SHARDED") == "1":  # pragma: no cover
    DATABASES["shard_b"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_shard_b.sqlite3",
    }

# Postgres tier - additive, mutually exclusive with FAKESHOP_SHARDED.
# ``FAKESHOP_PG_DSN`` (e.g. ``postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop``)
# swaps the ``default`` alias to Postgres so the FULL suite runs against a real
# Postgres server - the vendor tier the optimizer's LATERAL-join fetch strategy
# (and any other ``connection.vendor``-sensitive behavior) is verified on.
# Local: ``docker compose -f docker-compose.postgres.yml up -d`` then
# ``FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop uv run pytest``.
# CI: the ``test-postgres`` job in ``.github/workflows/django.yml`` provides the
# server via a GitHub Actions service container.
# Requires the ``pg`` dependency group (``uv sync --group pg`` installs
# psycopg); the DSN is parsed with the stdlib so the default sqlite install
# carries no Postgres dependency.
_pg_dsn = os.environ.get("FAKESHOP_PG_DSN")
if _pg_dsn:  # pragma: no cover
    from urllib.parse import urlsplit

    _pg = urlsplit(_pg_dsn)
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _pg.path.lstrip("/"),
        "USER": _pg.username or "",
        "PASSWORD": _pg.password or "",
        "HOST": _pg.hostname or "",
        "PORT": str(_pg.port or ""),
    }


# ---------------------------------------------------------------------------
# Auth
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_REDIRECT_URL = "/graphql/"
LOGOUT_REDIRECT_URL = "/login/"


# ---------------------------------------------------------------------------
# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# https://docs.djangoproject.com/en/stable/howto/static-files/
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"


# ---------------------------------------------------------------------------
# Media files (user uploads)
# https://docs.djangoproject.com/en/stable/topics/files/
# ---------------------------------------------------------------------------
# Needed by the spec-037 ``MediaSpecimen`` FileField / ImageField columns so a
# stored file's ``url`` is built from ``MEDIA_URL``. Live upload tests override
# ``MEDIA_ROOT`` to a per-test temp dir so no files land in the repo.

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Third-party: django-strawberry-framework
# ---------------------------------------------------------------------------

DJANGO_STRAWBERRY_FRAMEWORK = {
    # Intentionally empty: fakeshop exercises package defaults; focused tests
    # override individual settings.
}
