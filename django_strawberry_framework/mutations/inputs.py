"""Input, payload, and error-envelope generation reserved by spec-036."""

# TODO(spec-036 Slice 1): implement model-driven mutation input generation and
# the shared ``FieldError`` envelope.
# Pseudocode:
# - declare public ``FieldError`` as a Strawberry type with ``field`` and
#   ``messages`` fields matching graphene-django's ErrorType shape;
# - inspect the mutation model's editable, settable fields, excluding pk,
#   ``editable=False`` fields, auto timestamps, and reverse relations;
# - narrow the field set by the mutation's own ``Meta.fields`` / ``Meta.exclude``;
# - build ``<Model>Input`` with required fields only when Django has no usable
#   ``default`` / ``blank`` / ``null`` escape, otherwise default to UNSET;
# - build ``<Model>PartialInput`` with every field optional and UNSET-defaulted;
# - map scalar fields through the read-side scalar / enum converters;
# - map FK and OneToOne fields to one ``<field>_id`` argument using GlobalID for
#   Relay-node targets and the raw pk scalar otherwise;
# - map M2M fields to a list of the same id shape;
# - honor consumer-provided ``input_class`` / ``partial_input_class`` overrides
#   without clobbering consumer-authored fields;
# - materialize generated input and payload classes as module globals so
#   Strawberry lazy references resolve at schema build;
# - if a FileField or ImageField reaches the converter before spec-037 ships,
#   fail loudly with NotImplementedError instead of emitting a wrong scalar.
