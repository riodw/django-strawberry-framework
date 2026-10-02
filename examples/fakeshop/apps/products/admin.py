"""Admin registrations and shortcuts for inspecting, seeding, and deleting catalog data and test users."""

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from typing_extensions import override

from apps.products.models import Category, Entry, Item, Property
from apps.products.services import create_users, delete_data, delete_users, seed_data

User = get_user_model()


# --- Custom UserAdmin with create_users / delete_users via query params ---
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin[AbstractBaseUser]):
    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
    )
    list_display_links = ("id", "username")
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "user_permissions",
    )

    @override
    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, object] | None = None,
    ) -> HttpResponse:
        # --- create_users ---
        create_count = request.GET.get("create_users")
        if create_count:
            try:
                count = int(create_count)
                if count > 0:
                    result = create_users(count)
                    self.message_user(
                        request,
                        f"Created {result['users']} test users.",
                        messages.SUCCESS,
                    )
                new_get = request.GET.copy()
                new_get.pop("create_users")
                return redirect(f"{request.path}?{new_get.urlencode()}")
            except (ValueError, TypeError):
                self.message_user(
                    request,
                    "Invalid value for create_users. Must be an integer.",
                    messages.ERROR,
                )

        # --- delete_users ---
        delete_target = request.GET.get("delete_users")
        if delete_target:
            try:
                result = delete_users(delete_target)
                self.message_user(
                    request,
                    f"Deleted {result['users']} users."
                    if result["users"]
                    else "Nothing to delete.",
                    messages.SUCCESS if result["users"] else messages.WARNING,
                )
                new_get = request.GET.copy()
                new_get.pop("delete_users")
                return redirect(f"{request.path}?{new_get.urlencode()}")
            except (ValueError, TypeError):
                self.message_user(
                    request,
                    'Invalid value for delete_users. Use an integer or "all".',
                    messages.ERROR,
                )

        return super().changelist_view(request, extra_context=extra_context)


class ItemInline(admin.TabularInline[Item, Category]):
    model = Item
    extra = 0
    show_change_link = True


class PropertyInline(admin.TabularInline[Property, Category]):
    model = Property
    extra = 0
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin[Category]):
    list_display = (
        "name",
        "description",
        "created_date",
        "updated_date",
    )
    search_fields = ("name", "description")
    inlines = [PropertyInline, ItemInline]


class EntryInline(admin.TabularInline[Entry, Item]):
    model = Entry
    extra = 1
    autocomplete_fields = ["property"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin[Item]):
    list_display = (
        "name",
        "description",
        "category",
        "created_date",
        "updated_date",
    )
    list_filter = ("category", "created_date")
    search_fields = ("name", "description")
    inlines = [EntryInline]
    autocomplete_fields = ["category"]

    @override
    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, object] | None = None,
    ) -> HttpResponse:
        # --- seed_data ---
        seed_count = request.GET.get("seed_data")
        if seed_count:
            try:
                count = int(seed_count)
                if count > 0:
                    result = seed_data(count)
                    self.message_user(
                        request,
                        f"Created {result['categories']} categories, "
                        f"{result['properties']} properties, "
                        f"{result['items']} items, "
                        f"{result['entries']} entries.",
                        messages.SUCCESS,
                    )
                new_get = request.GET.copy()
                new_get.pop("seed_data")
                return redirect(f"{request.path}?{new_get.urlencode()}")
            except (ValueError, TypeError):
                self.message_user(
                    request,
                    "Invalid value for seed_data. Must be an integer.",
                    messages.ERROR,
                )

        # --- delete_data ---
        delete_target = request.GET.get("delete_data")
        if delete_target:
            try:
                result = delete_data(delete_target)
                parts = []
                if result["categories"]:
                    parts.append(f"{result['categories']} categories")
                if result["properties"]:
                    parts.append(f"{result['properties']} properties")
                if result["items"]:
                    parts.append(f"{result['items']} items")
                if result["entries"]:
                    parts.append(f"{result['entries']} entries")
                summary = ", ".join(parts) if parts else "nothing"
                self.message_user(request, f"Deleted {summary}.", messages.SUCCESS)
                new_get = request.GET.copy()
                new_get.pop("delete_data")
                return redirect(f"{request.path}?{new_get.urlencode()}")
            except (ValueError, TypeError):
                self.message_user(
                    request,
                    'Invalid value for delete_data. Use an integer, "all", or "everything".',
                    messages.ERROR,
                )

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin[Property]):
    list_display = (
        "name",
        "description",
        "category",
        "created_date",
        "updated_date",
    )
    list_filter = ("category", "created_date")
    search_fields = ("name", "description")
    autocomplete_fields = ["category"]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin[Entry]):
    list_display = (
        "value",
        "description",
        "property",
        "item",
        "created_date",
        "updated_date",
    )
    list_filter = ("property__category", "property", "created_date")
    search_fields = (
        "value",
        "description",
        "item__name",
        "property__name",
    )
    autocomplete_fields = ["property", "item"]
