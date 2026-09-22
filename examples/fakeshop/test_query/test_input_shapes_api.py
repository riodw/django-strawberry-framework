"""Live GraphQL HTTP tests for the relation-id and payload-slot shapes of generated write inputs.

Each row introspects a generated ``DjangoMutation`` input or payload over
``/graphql`` and reads one shape the input generator decides from the related
model's primary ``DjangoType``:

- a forward key to a Relay-Node primary is a ``GlobalID`` (``ItemInput.categoryId``),
  to a plain primary the target's raw pk scalar (``BookInput.shelfId``);
- a forward many-to-many to a Relay-Node primary is a list of ``GlobalID``
  (``BookInput.genres``), to a plain primary a list of raw pks
  (``createShelf``'s ``altBranches``), and is optional either way;
- a payload over a Relay-Node primary carries the row in a nullable ``node``
  slot (``CreateBookViaCustomInputPayload``), over a plain primary in a
  nullable ``result`` slot (``createShelf``'s payload), beside the
  ``errors: [FieldError!]!`` list either way.
"""

from graphql_client import assert_graphql_success

_TYPE_REF = "kind name ofType { kind name ofType { kind name ofType { kind name } } }"


def _input_fields(type_name: str) -> dict[str, dict]:
    """Return ``{field name: type tree}`` for the input object ``type_name`` over HTTP."""
    data = assert_graphql_success(
        f'{{ __type(name: "{type_name}") {{ inputFields {{ name type {{ {_TYPE_REF} }} }} }} }}',
    )
    return {field["name"]: field["type"] for field in data["__type"]["inputFields"]}


def _mutation_data_input_name(field_name: str) -> str:
    """Return the named input type of mutation ``field_name``'s ``data`` argument."""
    data = assert_graphql_success(
        '{ __type(name: "Mutation") { fields { name args { name type { kind name '
        "ofType { kind name } } } } } }",
    )
    field = next(f for f in data["__type"]["fields"] if f["name"] == field_name)
    arg_type = next(arg for arg in field["args"] if arg["name"] == "data")["type"]
    return arg_type["name"] or arg_type["ofType"]["name"]


def _non_null(inner: dict) -> dict:
    return {"kind": "NON_NULL", "name": None, "ofType": inner}


def _scalar(name: str) -> dict:
    return {"kind": "SCALAR", "name": name, "ofType": None}


def _list_of_non_null(name: str) -> dict:
    return {
        "kind": "LIST",
        "name": None,
        "ofType": {
            "kind": "NON_NULL",
            "name": None,
            "ofType": {"kind": "SCALAR", "name": name, "ofType": None},
        },
    }


def test_forward_key_to_a_relay_primary_is_a_required_global_id():
    """``ItemInput.categoryId`` is ``ID!``: ``CategoryType`` is a Relay node."""
    fields = _input_fields("ItemInput")

    assert fields["categoryId"] == _non_null(_scalar("ID")), fields


def test_forward_key_to_a_plain_primary_is_the_raw_pk_scalar():
    """``BookInput.shelfId`` is ``Int!``: ``ShelfType`` is not a Relay node.

    ``shelf`` is a required key, so the raw pk scalar is non-null; the
    ``<field>_id`` spelling is what a key maps to on a generated input.
    """
    fields = _input_fields("BookInput")

    assert fields["shelfId"] == _non_null(_scalar("Int")), fields
    assert "shelf" not in fields, fields


def test_many_to_many_to_a_relay_primary_is_an_optional_global_id_list():
    """``BookInput.genres`` is ``[ID!]``: ``GenreType`` is a Relay node through ``Meta.interfaces``.

    The outer list is nullable: a many-to-many is optional on create whatever
    its column says.
    """
    fields = _input_fields("BookInput")

    assert fields["genres"] == _list_of_non_null("ID"), fields


def test_many_to_many_to_a_plain_primary_is_an_optional_raw_pk_list():
    """``createShelf``'s ``altBranches`` is ``[Int!]``: ``BranchType`` is not a Relay node."""
    fields = _input_fields(_mutation_data_input_name("createShelf"))

    assert fields["altBranches"] == _list_of_non_null("Int"), fields


def _payload_fields(type_name: str) -> dict[str, dict]:
    """Return ``{field name: type tree}`` for the payload object ``type_name`` over HTTP."""
    data = assert_graphql_success(
        f'{{ __type(name: "{type_name}") {{ fields {{ name type {{ {_TYPE_REF} }} }} }} }}',
    )
    return {field["name"]: field["type"] for field in data["__type"]["fields"]}


def _mutation_payload_name(field_name: str) -> str:
    """Return the named payload type mutation ``field_name`` returns."""
    data = assert_graphql_success(
        '{ __type(name: "Mutation") { fields { name type { kind name ofType { kind name } } } } }',
    )
    field_type = next(f for f in data["__type"]["fields"] if f["name"] == field_name)["type"]
    return field_type["name"] or field_type["ofType"]["name"]


_FIELD_ERRORS = _non_null(
    {
        "kind": "LIST",
        "name": None,
        "ofType": {
            "kind": "NON_NULL",
            "name": None,
            "ofType": {"kind": "OBJECT", "name": "FieldError"},
        },
    },
)


def test_payload_of_a_relay_primary_carries_a_nullable_node_slot():
    """``CreateBookViaCustomInputPayload`` exposes a nullable ``node`` and no ``result``.

    ``BookType`` is a Relay node, so ``payload_object_slot`` names the object
    slot ``node``; the slot is nullable because a refused write returns no row.
    """
    fields = _payload_fields("CreateBookViaCustomInputPayload")

    assert fields["node"] == {"kind": "OBJECT", "name": "BookType", "ofType": None}, fields
    assert fields["errors"] == _FIELD_ERRORS, fields
    assert "result" not in fields, fields


def test_payload_of_a_plain_primary_carries_a_nullable_result_slot():
    """``createShelf``'s payload exposes a nullable ``result`` and no ``node``.

    ``ShelfType`` is not a Relay node, so the object slot is the uniform
    ``result``, never ``node`` and never a model-derived name.
    """
    fields = _payload_fields(_mutation_payload_name("createShelf"))

    assert fields["result"] == {"kind": "OBJECT", "name": "ShelfType", "ofType": None}, fields
    assert fields["errors"] == _FIELD_ERRORS, fields
    assert "node" not in fields, fields
    assert "shelf" not in fields, fields
