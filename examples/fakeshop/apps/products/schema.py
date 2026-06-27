"""GraphQL schema for the fakeshop products app.

A bidirectional graph over `Category` / `Item` / `Property` / `Entry`
using the shipped `DjangoType` surface, with connections-only root fields
(the `django-graphene-filters` cookbook mirror). Each root field is a
`DjangoConnectionField`, so `DjangoOptimizerExtension` (wired in
`config.schema`) plans `select_related` / `prefetch_related` / `only()`
across nested selections - and windowed `Prefetch`es for nested
relation-connection siblings - without per-resolver boilerplate.

The module also exposes a `Mutation` type (spec-036 Slice 4): the
`DjangoMutation` create / update / delete write surface over `Item` plus a
`Category` create, each surfaced as an unannotated `DjangoMutationField`. The
defaults apply - `DjangoModelPermission` write authorization and the post-write
optimizer re-fetch under the `spec-035` G2 mutation gate.

The eventual `1.0.0` shape - Relay-node types with the cookbook-shaped
filter / order / aggregate / fields / search / permissions surface, a
1-to-1 port of the `django-graphene-filters` cookbook recipe - is
tracked in `KANBAN.md` under the Layer-3 cards (`DONE-027-0.0.8`
filters, `DONE-028-0.0.8` orders, `DONE-030-0.0.9` `DjangoConnectionField`,
`DONE-034-0.0.10` permissions, `TODO-BETA-046-0.1.1` fieldsets,
`TODO-BETA-047-0.1.2` search, `TODO-BETA-049-0.1.3` aggregates). The
shipped `filterset_class` + `orderset_class` + permissions surface is wired below;
each `*Type` class still carries commented-out future-shape Meta keys
and methods - uncomment each line as the corresponding card ships.
Sidecar keys `filterset_class` / `orderset_class` are backed by the
present `filters.py` / `orders.py` modules; `aggregate_class` /
`fields_class` additionally need their cards plus an `aggregates.py` /
`fields.py` module under this app (`fields.py` is present;
`aggregates.py` is not yet).
"""

# Future imports (uncomment as Layer-3 subsystems ship):
#
# from apps.products import aggregates                               # TODO-BETA-049-0.1.3 (aggregates)
# from apps.products import fields as fieldsets                      # TODO-BETA-046-0.1.1

import strawberry
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoFormMutation,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
    apply_cascade_permissions,
)

from . import filters, forms, models, orders

# TODO(spec-039 Slice 3): Import `SerializerMutation` and
# `apps.products.serializers` when the serializer resolver lands in the same
# commit as the live products surface.
# Pseudo flow:
#   - Import `SerializerMutation` from the package root.
#   - Import the products `serializers` module beside the existing forms/models.
#
# Keep this in products, not a new acceptance app: the live `/graphql/` suite
# already owns package-reachable write behavior for model and form mutations.


class CategoryType(DjangoType):
    class Meta:
        model = models.Category
        fields = (
            "id",
            "name",
            "description",
            "items",
            "properties",
            "is_private",
            "created_date",
            "updated_date",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.CategoryFilter
        orderset_class = orders.CategoryOrder
        # Future Layer-3 additions - uncomment each as the relevant card ships:
        # search_fields = ("name", "description")           # needs TODO-BETA-047-0.1.2
        # aggregate_class = aggregates.CategoryAggregate    # needs TODO-BETA-049-0.1.3 + aggregates.py
        # fields_class = fieldsets.CategoryFieldSet         # needs TODO-BETA-046-0.1.1 + fields.py

    @classmethod
    def get_queryset(cls, queryset, info):
        """Staff see everything; everyone else (incl. view_category holders) sees public rows.

        Category has no cascadable forward edge, so the cascade is a no-op here - it
        keeps the four-hook policy uniform (every non-staff branch narrows so a nested
        non-null FK selection can never reach a target the viewer cannot see).
        """
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        elif user and user.has_perm("products.view_category"):
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = (
            "id",
            "name",
            "description",
            "category",
            "entries",
            "is_private",
            "created_date",
            "updated_date",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.ItemFilter
        orderset_class = orders.ItemOrder
        # Future Layer-3 additions - uncomment each as the relevant card ships:
        # search_fields = ("name", "description", "category__name", "category__description")  # needs TODO-BETA-047-0.1.2
        # aggregate_class = aggregates.ItemAggregate     # needs TODO-BETA-049-0.1.3 + aggregates.py
        # fields_class = fieldsets.ItemFieldSet          # needs TODO-BETA-046-0.1.1 + fields.py

    @classmethod
    def get_queryset(cls, queryset, info):
        """Staff see everything; everyone else (incl. view_item holders) sees public Items under a visible Category.

        The view_item branch cascades just like the anonymous fallback: a non-staff
        viewer only sees Items whose ``category`` target is itself visible to them, so
        selecting the non-null ``category { ... }`` can never hit a hidden target and
        raise ``RelatedObjectDoesNotExist`` (feedback H1). Only staff bypass the cascade.
        """
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        elif user and user.has_perm("products.view_item"):
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


class PropertyType(DjangoType):
    class Meta:
        model = models.Property
        fields = (
            "id",
            "name",
            "description",
            "category",
            "entries",
            "is_private",
            "created_date",
            "updated_date",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.PropertyFilter
        orderset_class = orders.PropertyOrder
        # Future Layer-3 additions - uncomment each as the relevant card ships:
        # search_fields = ("name", "description", "category__name", "category__description")  # needs TODO-BETA-047-0.1.2
        # aggregate_class = aggregates.PropertyAggregate  # needs TODO-BETA-049-0.1.3 + aggregates.py
        # fields_class = fieldsets.PropertyFieldSet       # needs TODO-BETA-046-0.1.1 + fields.py

    @classmethod
    def get_queryset(cls, queryset, info):
        """Staff see everything; everyone else (incl. view_property holders) sees public Properties under a visible Category.

        Like ItemType, the view_property branch cascades through the non-null
        ``category`` edge so a nested ``category { ... }`` selection can never reach a
        hidden target. Only staff bypass the cascade (feedback H1).
        """
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        elif user and user.has_perm("products.view_property"):
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


class EntryType(DjangoType):
    class Meta:
        model = models.Entry
        fields = (
            "id",
            "value",
            "description",  # Future: drop this entry to exercise field-level permission gating (TODO-BETA-046-0.1.1 FieldSet read gates)
            "property",
            "item",
            "is_private",
            "created_date",
            "updated_date",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.EntryFilter
        orderset_class = orders.EntryOrder
        # Future Layer-3 additions - uncomment each as the relevant card ships:
        # search_fields = ("value", "property__name", "item__name") # needs TODO-BETA-047-0.1.2
        # aggregate_class = aggregates.EntryAggregate  # needs TODO-BETA-049-0.1.3 + aggregates.py
        # fields_class = fieldsets.EntryFieldSet       # needs TODO-BETA-046-0.1.1 + fields.py

    @classmethod
    def get_queryset(cls, queryset, info):
        """Staff see everything; everyone else (incl. view_entry holders) sees public Entries whose item and property are visible.

        The view_entry branch cascades through both non-null FK edges (``item`` and
        ``property``), so a non-staff viewer only sees Entries whose targets are visible
        to them - selecting ``item { ... }`` / ``property { ... }`` can never hit a hidden
        target and raise ``RelatedObjectDoesNotExist`` (feedback H1). Only staff bypass.
        """
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        elif user and user.has_perm("products.view_entry"):
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


@strawberry.type
class Query:
    """Fakeshop products app root fields - connections-only (the cookbook mirror).

    Each root field is a `DjangoConnectionField`, the 1-to-1 mirror of the
    `django-graphene-filters` cookbook Query
    (`all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)`,
    no list resolvers). `DjangoConnectionField` synthesizes the `filter:` /
    `orderBy:` arguments from each type's `Meta.filterset_class` /
    `Meta.orderset_class` sidecars and runs the same
    `visibility -> filter -> order -> deterministic-order -> optimizer`
    composition the hand-written resolvers used to spell out, capping the
    default page at `relay_max_results` and appending the deterministic
    `ORDER BY pk`. The four types are Relay-Node-shaped, so their relation
    siblings (`itemsConnection`, `entriesConnection`, ...) already exist live
    and plan through windowed `Prefetch`es.

    Still deferred to `TODO-BETA-053-0.1.5` (the fakeshop-activation card): the
    root `node(id:)` / `nodes(ids:)` Relay entry points and any `Meta.connection`
    (`totalCount`) opt-ins. This conversion intentionally adds neither.
    """

    all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)
    all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)
    all_properties: DjangoConnection[PropertyType] = DjangoConnectionField(PropertyType)
    all_entries: DjangoConnection[EntryType] = DjangoConnectionField(EntryType)


class CreateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "create"


class UpdateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "update"


class DeleteItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "delete"


class CreateCategory(DjangoMutation):
    class Meta:
        model = models.Category
        operation = "create"


# --------------------------------------------------------------------------- #
# Form-mutation write surface (spec-038 Slice 4 / Decision 12)
# --------------------------------------------------------------------------- #


class CreateItemViaForm(DjangoModelFormMutation):
    """Create an ``Item`` through ``ItemModelForm`` (the ``ModelForm`` create flavor)."""

    class Meta:
        form_class = forms.ItemModelForm
        operation = "create"


class UpdateItemViaForm(DjangoModelFormMutation):
    """Update an ``Item`` through ``ItemModelForm`` (the partial-update flavor)."""

    class Meta:
        form_class = forms.ItemModelForm
        operation = "update"


class CreateItemWithFileViaForm(DjangoModelFormMutation):
    """Create an ``Item`` through ``ItemFileModelForm`` - the multipart ``Upload`` form.

    The form's ``attachment`` ``FileField`` maps to the ``Upload`` scalar in the
    generated input; the resolver routes the uploaded value into the form's ``files=``,
    proving the ``data=`` / ``files=`` split (the P1 file-routing contract).
    """

    class Meta:
        form_class = forms.ItemFileModelForm
        operation = "create"


class CreateStampedItemViaForm(DjangoModelFormMutation):
    """Create an ``Item`` through ``StampedItemModelForm``, injecting ``user`` (the P2 case).

    ``StampedItemModelForm.__init__`` REQUIRES a ``user`` kwarg, so this mutation
    overrides ``get_form_kwargs`` to inject ``user=info.context.request.user`` at
    runtime. The override also waives the create-required-narrowing guard at bind. The
    injected user stamps the created row's ``description``, so the live test can pin that
    the user actually reached the form (and that schema-time ``base_fields`` discovery
    never instantiated the kwarg-requiring form).
    """

    class Meta:
        form_class = forms.StampedItemModelForm
        operation = "create"

    def get_form_kwargs(
        self,
        info,
        *,
        data,
        files,
        instance=None,
    ):
        kwargs = super().get_form_kwargs(info, data=data, files=files, instance=instance)
        kwargs["user"] = info.context.request.user
        return kwargs


class SubmitContact(DjangoFormMutation):
    """Submit a model-less ``ContactForm`` (the plain-form ``{ ok, errors }`` flavor).

    No ``operation`` (a plain base rejects any ``Meta.operation``). A plain form has no
    model default, so the success path is opened to any caller with the framework-native
    allow-any opt-out - an explicit empty ``permission_classes = []`` (spec-038 Decision 11
    documents ``[]`` as the allow-any posture for both flavors) - rather than a hand-rolled
    allow-all class.
    """

    class Meta:
        form_class = forms.ContactForm
        permission_classes = []


class SubmitPing(DjangoFormMutation):
    """A model-less plain form that declares NO ``permission_classes`` (deny-by-default).

    The sibling of ``SubmitContact`` that does NOT opt into the explicit ``[]`` allow-any
    posture: a plain
    ``DjangoFormMutation`` has no model, so an unset ``Meta.permission_classes`` falls
    to the ``DenyAll`` deny-by-default default (spec-038 Decision 11). Every live call
    is rejected with a top-level ``GraphQLError`` before the form runs, so the deny
    posture is earned over a real ``/graphql`` request rather than only in package
    tests (``docs/feedback.md`` - live deny-default coverage).
    """

    class Meta:
        form_class = forms.PingForm


# TODO(spec-039 Slice 3): Add create/update serializer mutations over
# `serializers.ItemSerializer` here, then expose both via `DjangoMutationField`
# below.
# Pseudo flow:
#   - Define `CreateItemViaSerializer` with `SerializerMutation.Meta` pointing to
#     `serializers.ItemSerializer` and `operation = "create"`.
#   - Define `UpdateItemViaSerializer` with the same serializer and
#     `operation = "update"`.
#
# The resolver and this live surface must land together so reachable resolver
# lines are covered by `test_products_api.py`, not package-only tests.
@strawberry.type
class Mutation:
    """Fakeshop products app write surface - the `DjangoMutation` + form-mutation writes.

    Each field is an unannotated `DjangoMutationField` (spec-036 Decision 7): the
    return `<Name>Payload` is materialized at finalization and cannot be named at
    import, so the factory types the field via a `strawberry.lazy` forward-ref. The
    `DjangoMutation` `Item` writes cover create / update / delete; `createCategory`
    exercises a second model end to end. No `permission_classes` override - the default
    `DjangoModelPermission` (the Django `add` / `change` / `delete` model perms) is
    exactly what the live write-authorization tests exercise (spec-036 Decision 15).

    The form-mutation surface (spec-038 Slice 4) adds the `DjangoModelFormMutation`
    create / update over `Item` via `ItemModelForm` (`createItemViaForm` /
    `updateItemViaForm`), the file-backed `Upload` form (`createItemWithFileViaForm`),
    the `get_form_kwargs`-injects-`user` form (`createStampedItemViaForm`), and the
    model-less plain `DjangoFormMutation` (`submitContact`). The `ModelForm` flavors
    inherit the same `DjangoModelPermission` default (codenames `add_item` /
    `change_item`); the plain form opts in with an explicit empty `permission_classes = []`.
    """

    create_item = DjangoMutationField(CreateItem)
    update_item = DjangoMutationField(UpdateItem)
    delete_item = DjangoMutationField(DeleteItem)
    create_category = DjangoMutationField(CreateCategory)
    create_item_via_form = DjangoMutationField(CreateItemViaForm)
    update_item_via_form = DjangoMutationField(UpdateItemViaForm)
    create_item_with_file_via_form = DjangoMutationField(CreateItemWithFileViaForm)
    create_stamped_item_via_form = DjangoMutationField(CreateStampedItemViaForm)
    submit_contact = DjangoMutationField(SubmitContact)
    submit_ping = DjangoMutationField(SubmitPing)
    # TODO(spec-039 Slice 3): Add `create_item_via_serializer` and
    # `update_item_via_serializer` fields here in the same commit as
    # `rest_framework/resolvers.py`.


__all__ = ("Mutation", "Query")
