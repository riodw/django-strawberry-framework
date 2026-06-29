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

from .models import Branch, Shelf


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


class CollisionShelfSerializer(serializers.ModelSerializer):
    """Plain ``Shelf`` serializer backing TWO mutations whose schema hooks diverge (spec-039 High - the same-serializer hook-shape collision).

    Two ``SerializerMutation`` declarations share THIS one serializer class, and each
    overrides ``get_serializer_for_schema()`` to return the SAME field names plus an extra
    ``target`` relation pointed at a DIFFERENT model (see ``shelf_collision_schema_field_map``).
    Before the canonical-name fix both hook-returned shapes claimed the single
    ``CollisionShelfSerializerInput`` name and collided at materialize ("... is materialized
    by two distinct SerializerMutation input classes"); the canonical name is now reserved
    for the DEFAULT full shape only, so each divergent hook shape takes a deterministic
    descriptor-derived name that folds in the relation ``related_model`` - the two finalize
    cleanly to DISTINCT input types. The runtime write uses THIS serializer (``code`` +
    ``branch``); the schema-only ``target`` field is not one of its fields, so it never
    reaches ``validated_data`` and never persists.
    """

    class Meta:
        model = Shelf
        fields = ("code", "branch")


def shelf_collision_schema_field_map(target_model):
    """Schema-time field map of ``code`` + ``branch`` + a serializer-only ``target`` relation at ``target_model`` (spec-039 High).

    The two collision mutations' ``get_serializer_for_schema()`` hooks call this with two
    DIFFERENT ``target_model``s, so the ONLY descriptor axis differing between their
    generated inputs is the ``target`` relation's ``related_model`` - exactly the axis the
    descriptor-derived naming folds in (``rest_framework/inputs.py::_related_model_token``).
    ``target`` is a serializer-only ``PrimaryKeyRelatedField`` (no backing ``Shelf`` column),
    ``required=False`` so a write may omit it; its sole purpose is to be the divergence axis
    that proves two same-serializer hook shapes finalize to DISTINCT names instead of
    colliding on the canonical one. Built from a throwaway ``ModelSerializer`` purely for its
    BOUND ``.fields`` (never saved - ``target`` is not a ``Shelf`` column).
    """

    class _TargetedShelfSerializer(serializers.ModelSerializer):
        target = serializers.PrimaryKeyRelatedField(
            queryset=target_model._default_manager.all(),
            required=False,
        )

        class Meta:
            model = Shelf
            fields = ("code", "branch", "target")

    return dict(_TargetedShelfSerializer().fields)


class HookNarrowedShelfSerializer(serializers.ModelSerializer):
    """``Shelf`` serializer whose default field set carries an UNSUPPORTED field a schema hook narrows away (spec-039 High - unsupported-default-field recovery).

    Default no-arg discovery SUCCEEDS (the serializer constructs and ``.fields``
    materializes), but its field WALK cannot convert ``alt_branches`` - a
    ``SlugRelatedField(many=True)`` is a ``ManyRelatedField`` wrapping a non-PK child, and
    only ``PrimaryKeyRelatedField(many=True)`` is a supported relation input. The
    canonical-name gate re-walks this default full shape only to RESERVE the canonical name;
    the walk raising ``ConfigurationError`` means the default identity is treated as ABSENT
    (``inputs.py::_default_full_shape_identity`` swallows the WALK error, not only the
    discovery error), so it must NOT reject the mutation's supported hook map. The mutation's
    ``get_serializer_for_schema()`` narrows the schema-time map to the supported subset
    (``code`` + ``branch``); ``alt_branches`` is ``required=False`` so a runtime write that
    omits it still validates, and the live write proves the hook map drives BOTH the schema
    (a ``branchId`` raw-pk input, NOT an ``altBranches`` slug list) and the runtime decode.
    """

    alt_branches = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Branch.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Shelf
        fields = ("code", "branch", "alt_branches")
