"""DRF serializers for the library serializer-mutation surface (spec-039 schema-hook + subclass live matrix).

Plain DRF ``ModelSerializer``s declared the standard DRF way (no package imports);
``apps/library/schema.py`` wraps them in the shipped ``SerializerMutation`` base so the
live ``/graphql/`` tests in ``test_query/test_library_api.py`` exercise two
consumer-visible behaviors end to end:

* ``TenantShelfSerializer`` requires a ``tenant`` constructor kwarg, so DRF's default
  no-arg schema discovery fails - the mutation overrides ``get_serializer_for_schema()``
  to supply a stable, request-independent schema-time field map AND ``get_serializer_kwargs``
  to inject the runtime tenant (the ``get_serializer_for_schema`` hook live matrix);
* ``ShelfSerializer`` / ``RenamedShelfSerializer`` back a parent serializer mutation and a
  SUBCLASS that redefines ``Meta.serializer_class`` (the subclass-validation live matrix - a
  subclass must validate against its OWN serializer, not an inherited parent snapshot).

``Shelf`` is non-Relay (``ShelfType`` lists no ``relay.Node`` interface), so the ``branch``
FK relation input is a raw pk and the payload object slot is ``result`` (not ``node``); the
model's ``unique_shelf_code_per_branch`` constraint surfaces through DRF's
``UniqueTogetherValidator``.
"""

from rest_framework import serializers

from .models import Shelf


class TenantShelfSerializer(serializers.ModelSerializer):
    """``Shelf`` serializer requiring a ``tenant`` constructor kwarg (spec-039 Decision-7 schema-hook matrix).

    DRF's default schema discovery constructs the serializer with NO args and reads its
    ``.fields``; this serializer's ``__init__`` REQUIRES a ``tenant`` kwarg, so default
    no-arg discovery raises. The mutation MUST therefore override
    ``get_serializer_for_schema()`` to supply a stable, request-independent field map AND
    override ``get_serializer_kwargs`` to inject the runtime ``tenant`` - the live test
    proves the schema-time hook and the runtime serializer construction AGREE over HTTP.
    The object ``validate()`` stamps the resolved tenant into ``topic`` (not an input
    field) so the test can pin that the injected runtime tenant reached the serializer.
    """

    class Meta:
        model = Shelf
        fields = ("code", "branch")

    def __init__(self, *args, tenant=None, **kwargs):
        # ``tenant`` is required: a no-arg construction (DRF's default ``.fields``
        # discovery) raises here, forcing the get_serializer_for_schema() override.
        if tenant is None:
            raise TypeError("TenantShelfSerializer requires a 'tenant' keyword argument.")
        self.tenant = tenant
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        # Stamp the runtime tenant into ``topic`` (not an input field) so the live HTTP
        # test can prove get_serializer_kwargs injected it - default no-arg discovery
        # could never have constructed this serializer.
        attrs["topic"] = f"tenant:{self.tenant}"
        return attrs


class ShelfSerializer(serializers.ModelSerializer):
    """Plain ``Shelf`` serializer - the subclass-mutation PARENT's serializer (spec-039 subclass validation)."""

    class Meta:
        model = Shelf
        fields = ("code", "branch")


class RenamedShelfSerializer(serializers.ModelSerializer):
    """``Shelf`` serializer with a RENAMED scalar - the subclass-mutation CHILD's serializer (spec-039).

    ``shelf_code = CharField(source="code")`` is a field of THIS serializer that the parent
    ``ShelfSerializer`` does NOT declare, so a subclass narrowing to ``("shelf_code",
    "branch")`` validates only if the child reads its OWN serializer - the default
    ``get_serializer_for_schema`` reads the mutation's own ``_mutation_meta`` (via
    ``cls.__dict__``), never the inherited parent's. The GraphQL wire name is ``shelfCode``;
    it writes through to the ``code`` column.
    """

    shelf_code = serializers.CharField(source="code")

    class Meta:
        model = Shelf
        fields = ("shelf_code", "branch")


class RejectingShelfSerializer(serializers.ModelSerializer):
    """``Shelf`` serializer whose ``save()`` raises a BARE (non-dict) DRF ``ValidationError`` (spec-039).

    A whole-object, SAVE-TIME rejection (a business rule that fires at write, after field
    validation passes): the bare ``ValidationError`` detail is a message LIST, not a field
    dict, so it reaches the recursive error flattener with an EMPTY path, which the
    flattener normalizes to the ``"__all__"`` sentinel in the error envelope. The live test
    proves that save-time bare-detail path end to end over HTTP.
    """

    class Meta:
        model = Shelf
        fields = ("code", "branch")

    def save(self, **kwargs):
        raise serializers.ValidationError("Shelf rejected by a whole-object business rule.")
