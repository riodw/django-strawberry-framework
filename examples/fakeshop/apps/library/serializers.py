"""DRF serializers for library mutation hooks, input shapes, visibility, locking, and nested writes.

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
from rest_framework.validators import UniqueValidator

# The serializer-field converter-registry surface (spec-039 rev6 #11) is resolved by
# NAME through the root ``__getattr__`` (the DRF soft-dependency guard), like
# ``SerializerMutation``.
from django_strawberry_framework import (
    SerializerFieldConversion,
    register_serializer_field_converter,
)

from .models import Book, Branch, Shelf


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


class OptionalCodeShelfSerializer(serializers.ModelSerializer):
    """Plain ``Shelf`` serializer used to prove mutation ``Meta.optional_fields`` over HTTP.

    ``code`` is required by DRF. One live mutation leaves that strict shape alone while
    another applies mutation-level ``optional_fields = ("code",)`` so GraphQL accepts
    omission and DRF returns the required error in-band.
    """

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


class NoteShelfSerializer(serializers.ModelSerializer):
    """``Shelf`` serializer with a serializer-only ``note`` whose ``allow_null`` is RUNTIME-supplied (spec-039 High / M2 + rev6 #1).

    ONE serializer class backs TWO ``SerializerMutation`` declarations; each constructs it with
    a different ``note_allow_null`` via BOTH ``get_serializer_for_schema()`` (the schema-time
    field map) AND ``get_serializer_kwargs`` (the per-request construction), so the schema-time
    ``note`` shape and the runtime ``note`` field AGREE (rev6 #1 - no schema-only
    decode-then-drop the agreement guard now forbids). The only descriptor axis differing
    between the two generated inputs is ``note``'s EMITTED nullability: ``required=True,
    allow_null=False`` is a non-null ``String!``, while ``required=True, allow_null=True`` is a
    nullable, OMITTABLE ``String`` (M2 - GraphQL cannot express required-AND-nullable, so it is
    omittable and null-accepting, DRF enforcing presence/validity in-band). The descriptor
    identity + the descriptor-derived name must capture that EMITTED nullability, or the second
    declaration silently reuses the first's cached input class (giving one mutation the other's
    nullability - the High bug this pins).

    ``note`` is a serializer-only WRITE-ONLY field (no backing ``Shelf`` column), decoded +
    validated then popped in ``create()``. ``note_allow_null=None`` (the no-arg DEFAULT
    discovery) omits it, building only ``code`` + ``branch`` - which reserves the canonical name
    away from the two hook shapes.
    """

    def __init__(self, *args, note_allow_null=None, **kwargs):
        self._note_allow_null = note_allow_null
        super().__init__(*args, **kwargs)

    class Meta:
        model = Shelf
        fields = ("code", "branch")

    def get_fields(self):
        fields = super().get_fields()
        if self._note_allow_null is not None:
            fields["note"] = serializers.CharField(
                required=True,
                allow_null=self._note_allow_null,
                write_only=True,
            )
        return fields

    def create(self, validated_data):
        # ``note`` was decoded + validated (proving the emitted nullability), then dropped -
        # ``Shelf`` has no ``note`` column.
        validated_data.pop("note", None)
        return super().create(validated_data)


def nullability_schema_field_map(*, allow_null):
    """Schema-time field map of ``code`` + ``branch`` + a ``note`` differing ONLY in ``allow_null`` (spec-039 High / M2).

    The two nullability mutations' ``get_serializer_for_schema()`` hooks call this with
    ``allow_null=False`` vs ``allow_null=True`` over the SAME ``NoteShelfSerializer``; each
    mutation's ``get_serializer_kwargs`` constructs the runtime serializer with the SAME
    ``note_allow_null``, so the schema-time ``note`` shape and the runtime ``note`` field AGREE
    (rev6 #1). Returns the BOUND ``.fields`` of a ``NoteShelfSerializer(note_allow_null=...)``.
    """
    return dict(NoteShelfSerializer(note_allow_null=allow_null).fields)


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


class HexColorField(serializers.Field):
    """A custom DRF field with NO supported converter ancestor (spec-039 rev6 #11 - live proof).

    A bare ``serializers.Field`` subclass, so ``convert_serializer_field`` would FAIL LOUD on
    it (no base-``Field`` catch-all) - UNTIL ``register_serializer_field_converter`` maps it
    (below). The library app registers the converter at import, so the live
    ``createShelfViaMetadataSerializer`` input can carry an ``accentColor: String`` field
    driven by the SANCTIONED converter registry, proving a consumer field maps over
    ``/graphql/`` without patching the framework (and an UNregistered custom field still
    raises - the package converter test pins that half).
    """

    def to_internal_value(self, data):
        # Accept the wire string as-is; a real field would validate ``#rrggbb``.
        return str(data)

    def to_representation(self, value):  # pragma: no cover - write-only, never serialized out.
        return value


# spec-039 rev6 #11: register the converter for the custom ``HexColorField`` -> ``str`` at
# import time (before ``finalize_django_types`` builds the schema), so the MRO walk in
# ``convert_serializer_field`` resolves it and ``ShelfMetadataSerializer`` below can use it.
register_serializer_field_converter(
    HexColorField,
    lambda field: SerializerFieldConversion(annotation=str, required=field.required),
)


class ShelfMetadataSerializer(serializers.ModelSerializer):
    """A ``Shelf`` serializer exercising the rev6 type-system improvements live (spec-039 rev6 #6 / #7 / #11).

    Three serializer-only WRITE-ONLY fields prove the expanded input type system over
    ``/graphql/``:

    * ``priority`` - a serializer-only ``ChoiceField`` -> a GENERATED GraphQL enum (rev6 #6),
      not the graphene-django ``String``;
    * ``attributes`` - a ``DictField`` -> ``strawberry.scalars.JSON`` (rev6 #7);
    * ``accent_color`` - a custom ``HexColorField`` mapped ONLY via the public converter
      registry (rev6 #11) -> ``String``.

    All three are ``write_only`` + ``required=False`` serializer-only extras (no ``Shelf``
    column), decoded + validated then popped in ``create()`` (``Shelf`` has no such columns);
    the resolved ``priority`` is stamped into ``topic`` so the live test can read the effect.
    ``code`` + ``branch`` are the ordinary model-backed columns (auto-generated, so the rev6
    #8 conflict policy leaves them alone).
    """

    priority = serializers.ChoiceField(
        choices=[("low", "Low"), ("normal", "Normal"), ("high", "High")],
        required=False,
        write_only=True,
    )
    attributes = serializers.DictField(required=False, write_only=True)
    accent_color = HexColorField(required=False, write_only=True)
    # rev6 #9: ``help_text`` + validation constraints thread into the input field's SDL
    # description (documentation only - DRF still enforces ``max_length`` at runtime).
    label = serializers.CharField(
        help_text="A short human label for the shelf.",
        max_length=40,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Shelf
        fields = (
            "code",
            "branch",
            "priority",
            "attributes",
            "accent_color",
            "label",
        )

    def create(self, validated_data):
        # The serializer-only extras were decoded + validated (proving the enum / JSON /
        # registered-converter / described inputs), then dropped - ``Shelf`` has no such
        # columns. The resolved ``priority`` is stamped into ``topic`` so the live test can
        # read the effect.
        priority = validated_data.pop("priority", None)
        validated_data.pop("attributes", None)
        validated_data.pop("accent_color", None)
        validated_data.pop("label", None)
        if priority is not None:
            validated_data["topic"] = f"priority:{priority}"
        return super().create(validated_data)


class OwnerStampShelfSerializer(serializers.ModelSerializer):
    """A ``Shelf`` serializer with a REQUIRED ``topic`` a mutation narrows away + INJECTS (spec-039 rev6 #2).

    ``topic`` is declared ``required=True`` (the ``Shelf.topic`` column is ``blank=True,
    default=""``, so DRF would otherwise make it optional). A ``SerializerMutation`` can then
    narrow the input to ``("code", "branch")`` - dropping the required ``topic`` - and declare
    ``Meta.injected_fields = ("topic",)`` + a ``get_serializer_injected_data`` override that
    supplies ``topic``; the framework merges it into the serializer data itself. The
    create-required guard SUBTRACTS the declared injected field (so the narrowing does not
    raise), and the resolver enforces the hook's keys exactly match the declaration - the
    auditable, per-field replacement for the removed blanket waiver.
    """

    topic = serializers.CharField(required=True)

    class Meta:
        model = Shelf
        fields = ("code", "branch", "topic")


class AltBranchesShelfSerializer(serializers.ModelSerializer):
    """A ``Shelf`` serializer exposing the raw-pk M2M ``alt_branches`` (spec-039 rev6 #3 - batched multi-relation visibility).

    ``alt_branches`` is auto-generated by ``ModelSerializer`` as a
    ``PrimaryKeyRelatedField(many=True)`` over the non-Relay ``BranchType`` primary, so the
    generated input is a raw-pk list. The serializer decode confirms the WHOLE list's
    visibility in ONE batched ``pk__in`` query (through ``BranchType.get_queryset``, which
    hides ``city="restricted"`` from non-staff), and DRF's own re-validation runs against the
    SAME visibility-scoped queryset - so a hidden member is a ``altBranches`` relation error
    and never attached. ``required=False`` (M2M ``blank=True``), so a write may omit it.
    """

    class Meta:
        model = Shelf
        fields = ("code", "branch", "alt_branches")


class BookSerializer(serializers.ModelSerializer):
    """A ``Book`` (Relay-Node) serializer backing the UPDATE + row-lock live matrix (spec-039 rev6 #14).

    ``BookType`` is Relay-Node, so an update mutation's ``id`` is a decodable ``GlobalID`` and its
    payload slot is ``node``. A ``SerializerMutation`` with ``operation="update"`` +
    ``Meta.select_for_update = True`` locks the located row (``SELECT ... FOR UPDATE``) inside the
    pipeline transaction, after visibility filtering. Scalars only (``title`` / ``subtitle`` /
    ``circulation_status``) keep the update partial-input simple.
    """

    class Meta:
        model = Book
        fields = ("title", "subtitle", "circulation_status")


class BookGenresSerializer(serializers.ModelSerializer):
    """A ``Book`` serializer exposing the ``genres`` M2M for the update list-relation matrix (hardening).

    Backs the live proofs that a serializer UPDATE's list relation follows the
    replace-on-provide / unchanged-on-omit contract: DRF's own ``ModelSerializer.update``
    ``set()``s a provided ``genres`` list atomically inside the pipeline transaction, and an
    omitted ``genres`` (``partial=True``) leaves the stored set untouched. ``genres`` targets
    the Relay-Node ``GenreType`` primary, so the generated input carries a ``GlobalID`` list.
    """

    class Meta:
        model = Book
        fields = ("title", "genres")


class AliasValidatedBookSerializer(serializers.ModelSerializer):
    """A ``Book`` serializer whose title validator performs a queryset lookup."""

    title = serializers.CharField(
        validators=[
            UniqueValidator(queryset=Book.objects.all()),
        ],
    )

    class Meta:
        model = Book
        fields = ("title",)


class NestedShelfSerializer(serializers.ModelSerializer):
    """A nested ``Shelf`` serializer for the opt-in nested-write matrix (spec-039 rev6 #17).

    Backs the nested ``shelves`` field of ``BranchWithShelvesSerializer``: scalar ``code`` /
    ``topic`` plus the raw-pk M2M ``alt_branches`` (auto-generated as a
    ``PrimaryKeyRelatedField(many=True)`` over the non-Relay ``BranchType`` primary). A nested
    ``alt_branches`` id is visibility-decoded (through ``BranchType.get_queryset``, hiding
    ``city="restricted"``) at EVERY nesting level - proving the recursive relation decode. A
    ``validate_code`` business rule rejects the sentinel ``"BANNED"`` so the live test can prove a
    nested DRF validation error flattens to the structured ``shelves.<i>.code`` path.
    """

    class Meta:
        model = Shelf
        fields = ("code", "topic", "alt_branches")

    def validate_code(self, value):
        # A post-coercion nested business rule (a valid String at the GraphQL boundary that DRF
        # rejects) so the live test exercises nested error path flattening (``shelves.0.code``).
        if value == "BANNED":
            raise serializers.ValidationError("This shelf code is not allowed.")
        return value


class BranchWithShelvesSerializer(serializers.ModelSerializer):
    """A ``Branch`` serializer with an EXPLICIT opt-in nested writable ``shelves`` list (spec-039 rev6 #17).

    The fail-loud opt-in nested-write demonstration: the mutation declares
    ``Meta.nested_fields = {"shelves": NestedSerializerConfig()}``, and THIS serializer implements
    ``create()`` to perform the nested write ITSELF - the framework decodes + validates the nested
    ``shelves`` (visibility-checking each nested ``alt_branches`` pk, flattening nested validation
    errors to structured paths) but NEVER auto-saves the nested relation. ``name`` is unique;
    ``city`` is optional (``blank=True``).
    """

    shelves = NestedShelfSerializer(many=True)

    class Meta:
        model = Branch
        fields = ("name", "city", "shelves")

    def create(self, validated_data):
        # The nested write is the serializer author's own (the framework never auto-saves it):
        # decode + validation already produced the nested shelf dicts (with ``alt_branches`` as
        # resolved Branch instances), and this create() persists the branch + each shelf.
        shelves_data = validated_data.pop("shelves", [])
        branch = Branch.objects.create(**validated_data)
        for shelf_data in shelves_data:
            alt_branches = shelf_data.pop("alt_branches", [])
            shelf = Shelf.objects.create(branch=branch, **shelf_data)
            if alt_branches:
                shelf.alt_branches.set(alt_branches)
        return branch
