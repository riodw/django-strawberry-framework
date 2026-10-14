"""Django app configuration for the fakeshop products domain."""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """App configuration for the products app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"
