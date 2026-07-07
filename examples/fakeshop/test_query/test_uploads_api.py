"""Live GraphQL HTTP tests for the spec-037 file/image wire contract.

These earn the package's ``FileField`` / ``ImageField`` coverage over a real
``/graphql/`` round-trip (the placement the ``test_query`` README reserves for
the consumer-visible contract), against the ``scalars`` app's ``MediaSpecimen``
model. They cover:

- the **read** output objects (`DjangoFileType` / `DjangoImageType`) over HTTP,
  the default-nullable SDL shape (a *required* column still renders nullable),
  populated subfield serialization, and the empty-file object-null behavior;
- the **write** ``Upload`` mapping: the generated ``MediaSpecimenInput`` exposes
  ``Upload`` over HTTP, and a real GraphQL **multipart** request creates a row
  with uploaded files end to end (URL routing -> view -> multipart parse ->
  schema execution -> JSON response).

Storage-backend fault injection and corrupt-image dimension edges stay in the
package-internal ``tests/types/test_resolvers.py`` (they need a mocked
non-filesystem backend, unreachable from a live request).
"""

import io
import json

import pytest
from apps.scalars import models
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from graphql_client import post_graphql as _post_graphql


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests(reload_all_project_app_schemas):
    """Recreate imported DjangoType classes if package tests cleared the registry.

    Rebuilds the FULL project schema (every contributing app + config + the
    multipart-enabled GraphQLView via config.urls), not just ``apps.scalars.schema``:
    ``config.schema`` aggregates all five apps, so a scalars-only reload left the
    other apps unregistered after a package ``registry.clear()`` and the combined
    build raised a ``LazyType`` ``KeyError`` under collection orders that did not
    pre-materialize them. See ``conftest.py``. Django model classes stay stable.
    """
    reload_all_project_app_schemas()


# A 5x9 PNG so the live ``width`` / ``height`` assertions read distinct,
# deterministic values rather than a square that could pass by coincidence.
_IMAGE_WIDTH = 5
_IMAGE_HEIGHT = 9


def _png_bytes() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (_IMAGE_WIDTH, _IMAGE_HEIGHT)).save(buffer, format="PNG")
    return buffer.getvalue()


def _introspect_type(name: str, selection: str) -> dict:
    response = _post_graphql(
        f'query {{ __type(name: "{name}") {{ {selection} }} }}',
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    return body["data"]["__type"]


# ---------------------------------------------------------------------------
# Read side (DjangoFileType / DjangoImageType output objects)
# ---------------------------------------------------------------------------


def test_media_specimen_output_sdl_is_default_nullable_over_http():
    """A *required* FileField / ImageField renders as a NULLABLE output object.

    The columns are ``null=False, blank=False`` yet the live SDL exposes
    ``attachment: DjangoFileType`` / ``image: DjangoImageType`` (OBJECT, not
    NON_NULL) - the spec-037 Decision 4 default-nullable object contract, proven
    over the wire via introspection.
    """
    media_type = _introspect_type(
        "MediaSpecimenType",
        "fields { name type { kind name } }",
    )
    by_name = {f["name"]: f["type"] for f in media_type["fields"]}
    assert by_name["attachment"] == {"kind": "OBJECT", "name": "DjangoFileType"}
    assert by_name["image"] == {"kind": "OBJECT", "name": "DjangoImageType"}


@pytest.mark.django_db
def test_populated_file_and_image_resolve_subfields_over_http(tmp_path):
    """A populated FileField / ImageField resolves name/size/url (+ width/height) over HTTP."""
    image_bytes = _png_bytes()
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="m1")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.image.save("pic.png", ContentFile(image_bytes), save=False)
        specimen.save()

        response = _post_graphql(
            """
            query {
              allMediaSpecimens {
                label
                attachment { name size url }
                image { name size url width height }
              }
            }
            """,
        )
        assert response.status_code == 200
        body = response.json()
        assert "errors" not in body, body
        rows = body["data"]["allMediaSpecimens"]
        assert len(rows) == 1, rows
        row = rows[0]

    assert row["label"] == "m1"
    assert row["attachment"]["name"].endswith("doc.txt")
    assert row["attachment"]["size"] == len(b"hello bytes")
    # ``url`` is string-built from MEDIA_URL (+ the stored name); it never raises.
    assert row["attachment"]["url"].startswith("/media/")
    assert row["attachment"]["url"].endswith("doc.txt")
    assert row["image"]["name"].endswith("pic.png")
    assert row["image"]["size"] == len(image_bytes)
    assert row["image"]["url"].startswith("/media/")
    assert row["image"]["url"].endswith("pic.png")
    assert row["image"]["width"] == _IMAGE_WIDTH
    assert row["image"]["height"] == _IMAGE_HEIGHT


@pytest.mark.django_db
def test_empty_required_file_resolves_to_null_over_http(tmp_path):
    """An empty value on a required FileField / ImageField resolves the object to ``null``.

    A row created with no files stores ``""`` (the legacy / direct-create edge);
    because the generated SDL is nullable by default, the object resolves to
    ``null`` over HTTP instead of raising a non-null execution error.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        models.MediaSpecimen.objects.create(label="empty")

        response = _post_graphql(
            "{ allMediaSpecimens { label attachment { url } image { url } } }",
        )
        assert response.status_code == 200
        body = response.json()

    assert "errors" not in body, body
    row = body["data"]["allMediaSpecimens"][0]
    assert row["label"] == "empty"
    assert row["attachment"] is None
    assert row["image"] is None


# ---------------------------------------------------------------------------
# Write side (Upload mutation-input mapping + real multipart transport)
# ---------------------------------------------------------------------------


def test_media_specimen_input_exposes_upload_over_http():
    """The generated ``MediaSpecimenInput`` maps file/image columns to NON_NULL ``Upload``."""
    input_type = _introspect_type(
        "MediaSpecimenInput",
        "inputFields { name type { kind name ofType { kind name } } }",
    )
    by_name = {f["name"]: f["type"] for f in input_type["inputFields"]}
    # The columns are required (no null / blank / default), so the input field is
    # ``Upload!``. Assert the DIRECT wrapper is NON_NULL -> Upload: a nullable
    # ``Upload`` (kind SCALAR at the top) must NOT pass.
    for field in ("attachment", "image"):
        assert by_name[field] == {
            "kind": "NON_NULL",
            "name": None,
            "ofType": {"kind": "SCALAR", "name": "Upload"},
        }


@pytest.mark.django_db
def test_multipart_create_uploads_real_files_over_http(tmp_path):
    """A real GraphQL multipart request creates a ``MediaSpecimen`` with uploaded files.

    Exercises the full transport the resolver-level ``SimpleUploadedFile`` tests
    cannot: URL routing -> GraphQLView (``multipart_uploads_enabled=True``) ->
    multipart request parse -> schema execution -> JSON response. The caller is a
    superuser so the default ``DjangoModelPermission`` ``add_mediaspecimen`` gate
    passes (write-auth is exercised on its own in the products suite).
    """
    mutation = """
    mutation Create($data: MediaSpecimenInput!) {
      createMediaSpecimen(data: $data) {
        result {
          label
          attachment { name size url }
          image { name width height }
        }
        errors { field messages }
      }
    }
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        user = get_user_model().objects.create_superuser("uploader", "uploader@example.com", "pw")
        client = Client()
        client.force_login(user)

        operations = {
            "query": mutation,
            "variables": {"data": {"label": "uploaded", "attachment": None, "image": None}},
        }
        file_map = {"0": ["variables.data.attachment"], "1": ["variables.data.image"]}
        response = client.post(
            "/graphql/",
            data={
                "operations": json.dumps(operations),
                "map": json.dumps(file_map),
                "0": SimpleUploadedFile("up.txt", b"multipart bytes", content_type="text/plain"),
                "1": SimpleUploadedFile("up.png", _png_bytes(), content_type="image/png"),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "errors" not in body, body
        payload = body["data"]["createMediaSpecimen"]
        assert payload["errors"] == []
        result = payload["result"]

        # The row landed in the database with both files attached.
        assert models.MediaSpecimen.objects.filter(label="uploaded").exists()

    assert result["label"] == "uploaded"
    assert result["attachment"]["name"].endswith("up.txt")
    assert result["attachment"]["size"] == len(b"multipart bytes")
    assert result["attachment"]["url"].endswith("up.txt")
    assert result["image"]["name"].endswith("up.png")
    assert result["image"]["width"] == _IMAGE_WIDTH
    assert result["image"]["height"] == _IMAGE_HEIGHT


@pytest.mark.django_db
def test_multipart_create_media_specimen_image_via_form_over_http(tmp_path):
    """The spec-038 FORM path maps an ``ImageField`` to ``Upload`` over a live multipart request.

    The form-mutation twin of ``test_multipart_create_uploads_real_files_over_http`` (the
    spec-037 model path): ``createMediaSpecimenImageViaForm`` wraps ``MediaSpecimenImageForm``
    (a ``ModelForm`` over the ``image`` ``ImageField``), so the converter maps ``image`` ->
    ``Upload``, the resolver routes the upload into the bound form's ``files=``, and the bound
    ``ImageField`` validates it as a real image (Pillow). Asserts the stored image's
    width/height - the dimension proof the products ``FileField`` form test skips. The form
    opts out of write-auth (``permission_classes = []``), so no perm / login is needed.
    """
    mutation = """
    mutation Create($data: MediaSpecimenImageFormInput!) {
      createMediaSpecimenImageViaForm(data: $data) {
        result {
          label
          image { name width height }
        }
        errors { field messages }
      }
    }
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        operations = {
            "query": mutation,
            "variables": {"data": {"label": "form-uploaded", "image": None}},
        }
        file_map = {"0": ["variables.data.image"]}
        response = Client().post(
            "/graphql/",
            data={
                "operations": json.dumps(operations),
                "map": json.dumps(file_map),
                "0": SimpleUploadedFile("form.png", _png_bytes(), content_type="image/png"),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "errors" not in body, body
        payload = body["data"]["createMediaSpecimenImageViaForm"]
        assert payload["errors"] == []
        result = payload["result"]

        # The row landed via the FORM path with the image routed into ``files=``.
        assert models.MediaSpecimen.objects.filter(label="form-uploaded").exists()

    assert result["label"] == "form-uploaded"
    assert result["image"]["name"].endswith("form.png")
    assert result["image"]["width"] == _IMAGE_WIDTH
    assert result["image"]["height"] == _IMAGE_HEIGHT
