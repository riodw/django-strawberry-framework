"""Django app configuration for the schema-only accounts surface."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configure the schema-only accounts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
