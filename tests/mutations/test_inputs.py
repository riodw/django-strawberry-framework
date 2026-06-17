# TODO(spec-036 Slice 1): cover generated mutation inputs, payloads, and
# FieldError.
# Pseudocode:
# - declare small inline models or reuse fakeshop models as fixtures;
# - assert create-input requiredness follows default, blank, and null rules;
# - assert PartialInput fields are all optional and UNSET-defaulted;
# - assert pk, auto timestamp, editable=False, and reverse fields are excluded;
# - assert FK and OneToOne fields become ``<field>_id`` inputs;
# - assert M2M fields become lists of id-shaped values;
# - assert Relay-node targets use GlobalID and non-Relay targets use raw pk;
# - assert two mutations over one model share stable generated input types;
# - assert consumer input_class overrides preserve authored fields;
# - assert FieldError and generated payload types expose the frozen envelope.
