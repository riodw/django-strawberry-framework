"""Live ``/graphql/`` auth API acceptance tests (spec-040).

The primary harness for the spec-040 session-auth surface: every
consumer-reachable ``login`` / ``logout`` / ``register`` / ``me`` behavior is
earned here over a real HTTP request against the aggregated fakeshop schema
(the ``test_query`` live-first mandate). The suite covers ONLY the canonical
AllowAny default surface - the one-declaration-per-process rule (spec-040
Decision 6) makes a second, permission-gated variant of the same fixed-payload
field unreachable in the single aggregated ``config.schema``, so ALL
permission-gate coverage lives in ``tests/auth/`` on isolated throwaway schemas
(the documented placement exception for genuinely-unreachable-live behavior).

Per AGENTS.md, every test's first line seeds via ``create_users(N)`` - including
the register / anonymous-``me`` cases, which still seed first and then exercise
the fresh-account path; no test hand-rolls a ``User``.
"""

import pytest
from apps.products.services import TEST_USER_PASSWORD, create_users
from django.contrib.auth import get_user_model
from django.test import Client
from graphql_client import assert_graphql_success as _graphql_data

# A password that passes all four fakeshop ``AUTH_PASSWORD_VALIDATORS`` and is
# unrelated to any seeded username (the similarity validator must not bite).
_STRONG_PASSWORD = "correct-horse-9battery"

_LOGIN = (
    "mutation($u: String!, $p: String!){ login(username: $u, password: $p){ "
    "node{ username email } errors{ field messages codes } } }"
)
_LOGOUT = "mutation{ logout{ ok errors{ field messages } } }"
_REGISTER = (
    "mutation($d: RegisterInput!){ register(data: $d){ "
    "node{ username email } errors{ field messages codes } } }"
)
_ME = "{ me{ username } }"


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests(reload_all_project_app_schemas):
    """Rebuild the FULL project schema around package-test registry clears.

    Delegates to the shared complete-reload helper so the whole project schema -
    every contributing app (now including ``apps.accounts.schema``, the spec-040
    ``_PROJECT_APP_SCHEMA_MODULES`` row) plus config - is rebuilt after any
    package-test ``registry.clear()``. Because ``registry.clear()`` also drains
    the auth declaration ledger, each reload re-declares the four auth fields
    from the re-executed accounts module - every test in this file therefore
    exercises the spec-040 reload-preservation contract.
    """
    reload_all_project_app_schemas()


def _login(client: Client, username: str, password: str) -> dict:
    return _graphql_data(_LOGIN, client=client, variables={"u": username, "p": password})["login"]


@pytest.mark.django_db
def test_login_happy_path_sets_session_and_me_sees_the_user():
    """A seeded user logs in: payload node + session cookie + a follow-up ``me``."""
    create_users(1)
    client = Client()
    payload = _login(client, "staff_1", TEST_USER_PASSWORD)
    assert payload["errors"] == []
    assert payload["node"]["username"] == "staff_1"
    # The session was established on THIS client (the cookie round trip).
    assert "sessionid" in client.cookies
    assert _graphql_data(_ME, client=client)["me"] == {"username": "staff_1"}


@pytest.mark.django_db
def test_wrong_password_and_unknown_username_return_identical_envelope():
    """The enumeration guard: both failures are the byte-identical non-field envelope."""
    create_users(1)
    wrong_password = _login(Client(), "staff_1", "not-the-password")
    unknown_user = _login(Client(), "no_such_user_anywhere", "not-the-password")
    assert wrong_password == unknown_user
    assert wrong_password["node"] is None
    assert wrong_password["errors"] == [
        {
            "field": "__all__",
            "messages": ["Incorrect username/password"],
            # The pinned failed-login shape carries NO error code (the spec's
            # user-facing contract is field + message only).
            "codes": [],
        },
    ]


@pytest.mark.django_db
def test_inactive_user_gets_the_same_envelope():
    """``ModelBackend`` returns ``None`` for ``is_active=False`` - same envelope."""
    create_users(1)
    user = get_user_model().objects.get(username="regular_1")
    user.is_active = False
    user.save()
    payload = _login(Client(), "regular_1", TEST_USER_PASSWORD)
    assert payload["node"] is None
    assert [error["field"] for error in payload["errors"]] == ["__all__"]
    assert payload["errors"][0]["messages"] == ["Incorrect username/password"]


@pytest.mark.django_db
def test_logout_round_trip_and_anonymous_logout():
    """Authenticated logout is ``ok: true`` and ends the session; anonymous is ``ok: false``."""
    create_users(1)
    client = Client()
    _login(client, "staff_1", TEST_USER_PASSWORD)
    assert _graphql_data(_ME, client=client)["me"] is not None
    payload = _graphql_data(_LOGOUT, client=client)["logout"]
    assert payload == {"ok": True, "errors": []}
    # The session is gone: the same client's follow-up ``me`` is null.
    assert _graphql_data(_ME, client=client)["me"] is None
    # Idempotent anonymous logout: ``ok: false``, still no errors.
    anonymous = _graphql_data(_LOGOUT, client=Client())["logout"]
    assert anonymous == {"ok": False, "errors": []}


@pytest.mark.django_db
def test_register_login_me_logout_round_trip_and_hashed_storage():
    """The full fresh-account flow; the stored password is hashed, never the raw string."""
    create_users(1)
    client = Client()
    payload = _graphql_data(
        _REGISTER,
        client=client,
        variables={
            "d": {
                "username": "fresh_reg_user",
                "email": "fresh@example.com",
                "password": _STRONG_PASSWORD,
            },
        },
    )["register"]
    assert payload["errors"] == []
    assert payload["node"] == {"username": "fresh_reg_user", "email": "fresh@example.com"}

    stored = get_user_model().objects.get(username="fresh_reg_user")
    assert stored.check_password(_STRONG_PASSWORD)
    assert _STRONG_PASSWORD not in stored.password  # hashed column, no plaintext residue

    login_payload = _login(client, "fresh_reg_user", _STRONG_PASSWORD)
    assert login_payload["node"]["username"] == "fresh_reg_user"
    assert _graphql_data(_ME, client=client)["me"] == {"username": "fresh_reg_user"}
    assert _graphql_data(_LOGOUT, client=client)["logout"]["ok"] is True
    assert _graphql_data(_ME, client=client)["me"] is None


@pytest.mark.django_db
def test_duplicate_username_register_envelope_keys_to_username():
    """The model ``full_clean()`` unique check surfaces on the ``USERNAME_FIELD`` key."""
    create_users(1)
    payload = _graphql_data(
        _REGISTER,
        variables={"d": {"username": "staff_1", "password": _STRONG_PASSWORD}},
    )["register"]
    assert payload["node"] is None
    assert [error["field"] for error in payload["errors"]] == ["username"]
    assert payload["errors"][0]["messages"] == ["A user with that username already exists."]
    # The failed register wrote nothing (one seeded staff_1 remains).
    assert get_user_model().objects.filter(username="staff_1").count() == 1


@pytest.mark.django_db
def test_weak_password_register_envelope_keys_to_password_not_all():
    """Every failing validator's message lands under the single ``password`` key.

    ``validate_password`` raises a LIST-style ``ValidationError`` the generic
    mapper would key to the ``"__all__"`` sentinel; the register write step keys
    it to ``password`` directly (spec-040 Revision 5) - asserted explicitly here
    against two of fakeshop's configured validators (common + entirely-numeric).
    """
    create_users(1)
    payload = _graphql_data(
        _REGISTER,
        variables={"d": {"username": "weak_pw_user", "password": "12345678"}},
    )["register"]
    assert payload["node"] is None
    assert [error["field"] for error in payload["errors"]] == ["password"]
    messages = payload["errors"][0]["messages"]
    assert messages == ["This password is too common.", "This password is entirely numeric."]
    assert payload["errors"][0]["codes"] == ["password_too_common", "password_entirely_numeric"]
    assert not get_user_model().objects.filter(username="weak_pw_user").exists()


@pytest.mark.django_db
def test_register_decode_failure_returns_the_field_keyed_envelope():
    """A register DECODE failure (pre-write) rides the same field-keyed envelope.

    An unpaired-surrogate username is rejected by the shared decode walk before
    any password work or DB write - the register step pair short-circuits the
    decode ``FieldError`` exactly like the model flavor (spec-040 Decision 6:
    the shared skeleton's envelope short-circuits are reused, not re-spelled).
    """
    create_users(1)
    payload = _graphql_data(
        _REGISTER,
        variables={"d": {"username": "bad\ud800name", "password": _STRONG_PASSWORD}},
    )["register"]
    assert payload["node"] is None
    assert [error["field"] for error in payload["errors"]] == ["username"]
    assert payload["errors"][0]["messages"] == [
        "Text contains invalid Unicode (unpaired surrogate code points).",
    ]


@pytest.mark.django_db
def test_password_similar_to_username_is_rejected_with_user_context():
    """``validate_password(password, user)`` gets the constructed instance (Decision 6).

    The deliberate improvement over upstream's user-less call:
    ``UserAttributeSimilarityValidator`` compares against the SUBMITTED username,
    so a password equal to it is rejected - only possible because the write step
    passes the constructed (unsaved) user as the second argument.
    """
    create_users(1)
    payload = _graphql_data(
        _REGISTER,
        variables={"d": {"username": "verdant-orchard", "password": "verdant-orchard"}},
    )["register"]
    assert payload["node"] is None
    assert [error["field"] for error in payload["errors"]] == ["password"]
    assert payload["errors"][0]["messages"] == ["The password is too similar to the username."]


@pytest.mark.django_db
def test_anonymous_me_is_null_not_an_error():
    """An anonymous session is an expected state: ``me`` is ``null`` (Decision 7)."""
    create_users(1)
    assert _graphql_data(_ME)["me"] is None


@pytest.mark.django_db
def test_complete_reload_preserves_the_auth_surface(reload_all_project_app_schemas):
    """A ``registry.clear()`` + full reload rebuilds ``login`` / ``logout`` / ``me``.

    Pins the ``"apps.accounts.schema"`` ``_PROJECT_APP_SCHEMA_MODULES`` row
    (spec-040 Revision 7 #3): without it a post-clear rebuild raises the
    ``LazyType`` ``KeyError`` on the auth payload / ``UserType`` lazy refs or
    silently drops the auth surface. The reload runs a second time INSIDE the
    test (on top of the autouse fixture's) and the surface still answers live.
    """
    create_users(1)
    reload_all_project_app_schemas()
    client = Client()
    payload = _login(client, "staff_1", TEST_USER_PASSWORD)
    assert payload["node"]["username"] == "staff_1"
    assert _graphql_data(_ME, client=client)["me"] == {"username": "staff_1"}
    assert _graphql_data(_LOGOUT, client=client)["logout"]["ok"] is True


def _introspect_type(name: str) -> dict:
    query = (
        f'{{ __type(name: "{name}") {{ '
        "fields { name type { kind ofType { kind name } name } } "
        "inputFields { name type { kind ofType { kind name } name } } } }"
    )
    return _graphql_data(query)["__type"]


@pytest.mark.django_db
def test_generated_auth_type_shapes():
    """SDL shapes as pinned in the spec's User-facing API section.

    ``node`` is the FAKESHOP-SPECIFIC slot name (the example ``UserType``
    implements ``relay.Node``; ``payload_object_slot`` yields ``result`` for a
    non-Relay primary) - the generic contract is "the uniform object slot", so
    only this suite (whose ``UserType`` is Relay-backed) asserts ``node``.
    """
    create_users(1)
    login_payload = _introspect_type("LoginPayload")
    login_fields = {f["name"]: f["type"] for f in login_payload["fields"]}
    assert login_fields["node"]["name"] == "UserType"  # nullable object slot
    assert login_fields["errors"]["kind"] == "NON_NULL"

    logout_payload = _introspect_type("LogoutPayload")
    logout_fields = {f["name"]: f["type"] for f in logout_payload["fields"]}
    assert logout_fields["ok"] == {
        "kind": "NON_NULL",
        "ofType": {"kind": "SCALAR", "name": "Boolean"},
        "name": None,
    }
    assert logout_fields["errors"]["kind"] == "NON_NULL"
    assert "node" not in logout_fields  # model-less payload: no object slot at all

    register_input = _introspect_type("RegisterInput")
    input_fields = {f["name"]: f["type"] for f in register_input["inputFields"]}
    # username / password non-null; email optional (``EmailField(blank=True)`` -
    # the standard ``input_field_required`` rule, spec-040 Decision 6).
    assert input_fields["username"]["kind"] == "NON_NULL"
    assert input_fields["password"]["kind"] == "NON_NULL"
    assert input_fields["email"] == {"kind": "SCALAR", "ofType": None, "name": "String"}

    register_payload = _introspect_type("RegisterPayload")
    register_fields = {f["name"]: f["type"] for f in register_payload["fields"]}
    assert register_fields["node"]["name"] == "UserType"
    assert register_fields["errors"]["kind"] == "NON_NULL"
