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


class TargetedShelfSerializer(serializers.ModelSerializer):
    """``Shelf`` serializer whose WRITE-ONLY ``target`` relation is pointed at a RUNTIME-supplied model (spec-039 High - the same-serializer hook-shape collision).

    ONE serializer class backs TWO ``SerializerMutation`` declarations; each constructs it
    with a different ``target_model`` (``Patron`` vs ``Loan``) via BOTH
    ``get_serializer_for_schema()`` (the schema-time field map) AND ``get_serializer_kwargs``
    (the per-request construction), so the only descriptor axis differing between their
    generated inputs is ``target``'s ``related_model`` - exactly the axis the descriptor-
    derived naming folds in (``rest_framework/inputs.py::_related_model_token``). Before the
    canonical-name fix both hook shapes claimed the single canonical input name and collided
    at materialize; the canonical name is now reserved for the (here unused) DEFAULT full
    shape (``code`` + ``branch``, no ``target`` - the no-arg construction), so each hook shape
    takes a DISTINCT descriptor-derived name.

    ``target`` is a REAL runtime field (not schema-only): a write-only
    ``PrimaryKeyRelatedField`` over ``target_model``, so the resolver DECODES ``targetId``
    against the bind-stashed ``InputFieldSpec.related_model`` (``Patron`` vs ``Loan``) BEFORE
    constructing the serializer, then DRF RE-VALIDATES it against this same queryset. Posting
    a pk that exists only in ``Patron`` therefore SUCCEEDS for the Patron mutation but is a
    ``targetId`` relation error for the Loan mutation - proving each decodes against its OWN
    target model (the differentiating relation decode, not just the generated name). It is
    ``required=False`` (a write may omit it) and is popped before the model write (``Shelf``
    has no ``target`` column). ``target_model=None`` (the no-arg DEFAULT discovery) builds
    only ``code`` + ``branch``, which is what reserves the canonical name away from the hook
    shapes.
    """

    def __init__(self, *args, target_model=None, **kwargs):
        self._target_model = target_model
        super().__init__(*args, **kwargs)

    class Meta:
        model = Shelf
        fields = ("code", "branch")

    def get_fields(self):
        fields = super().get_fields()
        if self._target_model is not None:
            fields["target"] = serializers.PrimaryKeyRelatedField(
                queryset=self._target_model._default_manager.all(),
                required=False,
                write_only=True,
            )
        return fields

    def create(self, validated_data):
        # ``target`` was decoded + validated (proving the relation decode used the right
        # related_model), then dropped - ``Shelf`` has no ``target`` column.
        validated_data.pop("target", None)
        return super().create(validated_data)


def shelf_collision_schema_field_map(target_model):
    """Schema-time field map of ``code`` + ``branch`` + the write-only ``target`` relation at ``target_model`` (spec-039 High).

    The two collision mutations' ``get_serializer_for_schema()`` hooks call this with two
    DIFFERENT ``target_model``s, AGREEING with their ``get_serializer_kwargs`` runtime
    construction (same ``target_model``), so the schema-time shape and the runtime serializer
    decode the SAME ``target`` relation. Returns the BOUND ``.fields`` of a
    ``TargetedShelfSerializer`` constructed with ``target_model`` - including the write-only
    ``target`` ``PrimaryKeyRelatedField`` over ``target_model._default_manager`` - so
    ``target``'s ``related_model`` is the only axis differing between the two generated
    inputs.
    """
    return dict(TargetedShelfSerializer(target_model=target_model).fields)


def nullability_schema_field_map(*, allow_null):
    """Schema-time field map of ``code`` + ``branch`` + a same-name ``note`` differing ONLY in ``allow_null`` (spec-039 High / M2).

    The two nullability mutations' ``get_serializer_for_schema()`` hooks call this with
    ``allow_null=False`` vs ``allow_null=True`` over the SAME serializer (``ShelfSerializer``),
    so the only descriptor axis differing between their generated inputs is ``note``'s EMITTED
    nullability: ``required=True, allow_null=False`` is a non-null ``String!``, while
    ``required=True, allow_null=True`` is a nullable, omittable ``String`` (M2 - GraphQL
    cannot express required-AND-nullable, so it is omittable and DRF enforces presence). The
    descriptor identity + the descriptor-derived name must capture that EMITTED nullability,
    or the second declaration silently reuses the first's cached input class (giving one
    mutation the other's nullability - the High bug this pins). ``note`` is a serializer-only
    scalar (no backing ``Shelf`` column), decoded then dropped by the runtime
    ``ShelfSerializer`` (``code`` + ``branch``); its sole purpose is the nullability axis.
    Built from a throwaway ``ModelSerializer`` purely for its BOUND ``.fields``.
    """

    class _NullabilityShelfSerializer(serializers.ModelSerializer):
        note = serializers.CharField(required=True, allow_null=allow_null)

        class Meta:
            model = Shelf
            fields = ("code", "branch", "note")

    return dict(_NullabilityShelfSerializer().fields)


class BlankCodeShelfSerializer(serializers.ModelSerializer):
    """``Shelf`` serializer with an ``allow_blank=True`` required ``code`` (spec-039 M2 - allow_blank pinned).

    ``allow_blank`` is NOT a GraphQL concern (spec-039 Decision 7 / M2): a required
    ``allow_blank=True`` ``CharField`` is still a non-null ``String!`` in the generated SDL
    (``allow_blank`` is absent from the schema), and the empty-string acceptance is enforced
    by the serializer at runtime. The live test introspects the ``code`` input as a non-null
    ``String`` AND posts ``code: ""`` to prove the serializer accepts + writes it (a plain
    required ``CharField`` would reject the blank with a field error).
    """

    code = serializers.CharField(allow_blank=True)

    class Meta:
        model = Shelf
        fields = ("code", "branch")


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
