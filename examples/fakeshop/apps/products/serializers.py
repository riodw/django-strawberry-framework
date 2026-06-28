"""DRF serializers for the products live serializer-mutation surface (spec-039 Slice 3).

Plain DRF ``ModelSerializer``s declared the standard DRF way (no package imports);
``apps/products/schema.py`` wraps them in the shipped ``SerializerMutation`` base so
the live ``/graphql/`` tests in ``test_query/test_products_api.py`` exercise the
serializer-mutation pipeline end to end. ``ItemSerializer`` covers the spec's
Decision-13 live matrix:

* a ``category`` ``PrimaryKeyRelatedField`` - the relation that drives the
  ``categoryId``-through-the-serializer reverse map (GraphQL ``categoryId`` decodes
  back to the serializer's ``category`` field, target visibility via ``CategoryType``).
* a ``validate_name`` rejecting ``REJECTED_SERIALIZER_ITEM_NAME`` - the field-level
  ``serializer.errors`` case (a ``validate_<field>`` error keyed to ``name``).
* a cross-field / object ``validate()`` reading ``self.context["request"].user`` -
  the request-context PROOF (F9: a ``validate()`` branch, NOT a
  ``HiddenField(default=CurrentUserDefault())``, which is subtle under
  ``partial=True``). It rejects an item ``name`` equal to the authenticated
  username, surfacing under the ``"__all__"`` non-field bucket.
* an ``attachment`` ``FileField`` (the model column) - the multipart ``Upload``
  input (a real multipart create proving ``Upload`` routes into the serializer's
  ``data``, the DRF contrast with the form ``files=`` split).
* the model's ``unique_item_per_category`` ``UniqueConstraint`` - DRF's
  ``UniqueTogetherValidator`` surfaces it under ``"__all__"`` (the partial-update
  unique-together fire).
"""

from rest_framework import serializers

from .models import Item

# The sentinel value ``ItemSerializer.validate_name`` rejects - drives the
# field-level ``serializer.errors`` keyed-to-``name`` live case (a
# ``validate_<field>`` error).
REJECTED_SERIALIZER_ITEM_NAME = "__serializer_rejected__"


class ItemSerializer(serializers.ModelSerializer):
    """``ModelSerializer`` over ``Item`` for the create / update / partial-update live matrix.

    ``Meta.fields`` covers ``name`` / ``description`` / ``category`` / ``attachment``.
    The auto-generated ``category`` ``PrimaryKeyRelatedField`` is the relation the
    generated ``categoryId`` input writes through (the reverse map). ``validate_name``
    rejects ``REJECTED_SERIALIZER_ITEM_NAME`` so a field-level error keys to ``name``;
    the object ``validate()`` reads ``self.context["request"].user`` (the request-context
    proof, F9) and rejects a ``name`` equal to the authenticated username under
    ``"__all__"``; the model's ``unique_item_per_category`` constraint surfaces
    automatically through DRF's ``UniqueTogetherValidator`` as a ``"__all__"`` entry.
    """

    class Meta:
        model = Item
        fields = (
            "name",
            "description",
            "category",
            "attachment",
        )

    def validate_name(self, value):
        if value == REJECTED_SERIALIZER_ITEM_NAME:
            raise serializers.ValidationError("This serializer name is not allowed.")
        return value

    def validate(self, attrs):
        # The request-context proof (F9): an explicit object ``validate()`` reading
        # the injected ``context["request"].user``. Rejecting a name equal to the
        # authenticated username proves the framework-merged request context lands.
        # On partial update ``attrs`` carries only the provided fields, so guard on
        # presence (a ``name``-only partial update still exercises this branch).
        request = self.context.get("request")
        user = getattr(request, "user", None)
        name = attrs.get("name")
        if name is not None and user is not None and getattr(user, "username", None) == name:
            raise serializers.ValidationError("Item name must not equal the requesting username.")
        return attrs
