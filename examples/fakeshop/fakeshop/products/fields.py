import strawberry
from graphql import GraphQLError

import django_strawberry_framework as fieldsets

from . import models


def _user(info):
    """Extract the user from info.context, or None."""
    return getattr(info.context, "user", None)


def _resolve_date(dt, info, perm):
    """Tiered date visibility via truncated datetime objects.

    Staff         → full datetime (as-is)
    view_<model>  → day precision (time zeroed)
    Authenticated → month precision (day=1, time zeroed)
    Anonymous     → year precision (month=1, day=1, time zeroed)
    """
    user = _user(info)
    if user and user.is_staff:
        return dt
    if user and user.has_perm(perm):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if user and user.is_authenticated:
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------


class CategoryFieldSet(fieldsets.AdvancedFieldSet):
    display_name: str = strawberry.field(description="Computed: {id} - {name}")

    class Meta:
        model = models.Category

    def resolve_description(self, root, info):
        """Staff sees description; non-staff gets empty string."""
        user = _user(info)
        if user and user.is_staff:
            return root.description
        return ""

    def resolve_display_name(self, root, info):
        """Computed field: '{id} - {name}'. Visible to all signed-in users."""
        user = _user(info)
        if user and user.is_authenticated:
            return f"{root.id} - {root.name}"
        return None

    def resolve_created_date(self, root, info):
        return _resolve_date(root.created_date, info, "products.view_category")

    def check_updated_date_permission(self, info):
        """Gate: anonymous users cannot see updated_date at all."""
        user = _user(info)
        if not user or not user.is_authenticated:
            raise GraphQLError("Login required to view updated date.")

    def resolve_updated_date(self, root, info):
        """Tiered updated_date. If gate denied (anonymous), this still runs
        as fallback for non-nullable fields — returns year precision.
        """
        return _resolve_date(root.updated_date, info, "products.view_category")


# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------


class ItemFieldSet(fieldsets.AdvancedFieldSet):
    display_name: str = strawberry.field(description="Computed: {id} - {name}")

    class Meta:
        model = models.Item

    def resolve_is_private(self, root, info):
        """Staff sees is_private; non-staff gets False."""
        user = _user(info)
        if user and user.is_staff:
            return root.is_private
        return False

    def resolve_display_name(self, root, info):
        """Computed field: '{id} - {name}'. Visible to all signed-in users."""
        user = _user(info)
        if user and user.is_authenticated:
            return f"{root.id} - {root.name}"
        return None

    def resolve_created_date(self, root, info):
        return _resolve_date(root.created_date, info, "products.view_item")

    def check_updated_date_permission(self, info):
        """Gate: anonymous users cannot see updated_date."""
        user = _user(info)
        if not user or not user.is_authenticated:
            raise GraphQLError("Login required to view updated date.")

    def resolve_updated_date(self, root, info):
        return _resolve_date(root.updated_date, info, "products.view_item")


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------


class PropertyFieldSet(fieldsets.AdvancedFieldSet):
    display_name: str = strawberry.field(description="Computed: {id} - {name}")

    class Meta:
        model = models.Property

    def resolve_display_name(self, root, info):
        """Computed field: '{id} - {name}'. Visible to all signed-in users."""
        user = _user(info)
        if user and user.is_authenticated:
            return f"{root.id} - {root.name}"
        return None

    def resolve_created_date(self, root, info):
        return _resolve_date(root.created_date, info, "products.view_property")

    def check_updated_date_permission(self, info):
        """Gate: anonymous users cannot see updated_date."""
        user = _user(info)
        if not user or not user.is_authenticated:
            raise GraphQLError("Login required to view updated date.")

    def resolve_updated_date(self, root, info):
        return _resolve_date(root.updated_date, info, "products.view_property")


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------


class EntryFieldSet(fieldsets.AdvancedFieldSet):
    display_name: str = strawberry.field(description="Computed: {id} - {value}")

    class Meta:
        model = models.Entry

    def resolve_display_name(self, root, info):
        """Computed field: '{id} - {value}'. Visible to all signed-in users."""
        user = _user(info)
        if user and user.is_authenticated:
            return f"{root.id} - {root.value}"
        return None

    def resolve_created_date(self, root, info):
        return _resolve_date(root.created_date, info, "products.view_entry")

    # def check_updated_date_permission(self, info):
    #     """Gate: anonymous users cannot see updated_date."""
    #     user = _user(info)
    #     if not user or not user.is_authenticated:
    #         raise GraphQLError("Login required to view updated date.")

    def resolve_updated_date(self, root, info):
        """Permission + content in one method (no check_ gate).

        Demonstrates that resolve_ can handle denial directly:
        anonymous → None (nullable) or raise (non-nullable).
        Since updatedDate is non-nullable DateTime!, we use
        _resolve_date which returns year-precision for anonymous.
        """
        user = _user(info)
        if not user or not user.is_authenticated:
            raise GraphQLError("Login required to view updated date.")
        return _resolve_date(root.updated_date, info, "products.view_entry")
