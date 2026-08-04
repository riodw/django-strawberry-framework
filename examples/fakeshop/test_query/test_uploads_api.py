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

The suite drives through the package's own ``TestClient`` (spec-043):
the JSON posts earn the helper's happy-path lines live, and the two multipart
mutations earn the owned path-keyed ``files=`` builder - the nested
input-object shape (``data.attachment`` / ``data.image``) combined with a named
operation is exactly the envelope the engine base's map builder cannot produce.
"""

import io

import pytest
from apps.scalars import models
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from django_strawberry_framework.testing import TestClient

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
    # ``assert_no_errors=True`` (the TestClient default) replaces the old
    # hand-rolled "errors" not-in-body assertion.
    res = TestClient().query(f'query {{ __type(name: "{name}") {{ {selection} }} }}')
    assert res.response.status_code == 200
    return res.data["__type"]


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


def test_default_file_output_objects_expose_no_filesystem_path_over_http():
    """Neither default output object publishes ``path`` in the live schema (spec-048 D1).

    Introspection over the real endpoint, not a rendered SDL string: this is the
    surface an untrusted client actually sees, and an absent field is exactly
    what "the server's absolute path is not client data" has to mean on the
    wire.
    """
    for type_name in ("DjangoFileType", "DjangoImageType"):
        output_type = _introspect_type(type_name, "fields { name }")
        names = {field["name"] for field in output_type["fields"]}
        assert "path" not in names, (type_name, names)
    file_names = {
        field["name"] for field in _introspect_type("DjangoFileType", "fields { name }")["fields"]
    }
    assert file_names == {"name", "size", "url"}


def test_filesystem_path_opt_in_is_absent_unless_declared_over_http():
    """The opt-in is per column and per type: only the declared column gets the path type.

    ``MediaSpecimenType`` declares no opt-in and keeps the pathless objects;
    ``MediaSpecimenWithPathType`` names ``attachment`` only, so ``attachment``
    resolves to ``DjangoFilePathType`` while its own ``image`` stays
    ``DjangoImageType`` (spec-048 Decision 2).
    """
    default_fields = {
        field["name"]: field["type"]
        for field in _introspect_type(
            "MediaSpecimenType",
            "fields { name type { kind name } }",
        )["fields"]
    }
    assert default_fields["attachment"] == {"kind": "OBJECT", "name": "DjangoFileType"}
    assert default_fields["image"] == {"kind": "OBJECT", "name": "DjangoImageType"}

    opt_in_fields = {
        field["name"]: field["type"]
        for field in _introspect_type(
            "MediaSpecimenWithPathType",
            "fields { name type { kind name } }",
        )["fields"]
    }
    assert opt_in_fields["attachment"] == {"kind": "OBJECT", "name": "DjangoFilePathType"}
    assert opt_in_fields["image"] == {"kind": "OBJECT", "name": "DjangoImageType"}

    path_field = next(
        field
        for field in _introspect_type(
            "DjangoFilePathType",
            "fields { name description }",
        )["fields"]
        if field["name"] == "path"
    )
    assert "SECURITY" in path_field["description"]


@pytest.mark.django_db
def test_opted_in_filesystem_path_resolves_over_http(tmp_path):
    """The declared column serves its real absolute path; the default type still cannot.

    Both halves matter: the opt-in has to actually work (or a consumer who needs
    the path has no supported route and forks the type), and the un-opted type
    has to remain incapable of producing one in the same request.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="p1")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.image.save("pic.png", ContentFile(_png_bytes()), save=False)
        specimen.save()

        res = TestClient().query(
            """
            query {
              allMediaSpecimensWithPath {
                label
                attachment { name path url }
                image { name url }
              }
            }
            """,
        )
        assert res.response.status_code == 200
        row = res.data["allMediaSpecimensWithPath"][0]
        assert row["attachment"]["path"] == specimen.attachment.path
        assert row["attachment"]["path"].startswith(str(tmp_path))

        # The un-opted type cannot even be asked for it.
        refused = TestClient().query(
            "query { allMediaSpecimens { attachment { path } } }",
            assert_no_errors=False,
        )
        assert refused.data is None
        assert "path" in refused.errors[0]["message"]


@pytest.mark.django_db
def test_populated_file_and_image_resolve_subfields_over_http(tmp_path):
    """A populated FileField / ImageField resolves name/size/url (+ width/height) over HTTP."""
    image_bytes = _png_bytes()
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="m1")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.image.save("pic.png", ContentFile(image_bytes), save=False)
        specimen.save()

        res = TestClient().query(
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
        assert res.response.status_code == 200
        rows = res.data["allMediaSpecimens"]
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

        res = TestClient().query(
            "{ allMediaSpecimens { label attachment { url } image { url } } }",
        )
        assert res.response.status_code == 200

    row = res.data["allMediaSpecimens"][0]
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

    The spec-043 scenario-5 vehicle: the nested two-file input object rides
    ``TestClient``'s path-keyed ``files=`` contract (each key is the variable
    path a ``None`` placeholder marks), combined with ``operation_name=`` so
    ``operationName`` is proven to land INSIDE the multipart ``operations``
    field - the exact envelope the engine base's map builder cannot produce.
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
        client = TestClient()

        with client.login(user):
            res = client.query(
                mutation,
                variables={"data": {"label": "uploaded", "attachment": None, "image": None}},
                files={
                    "data.attachment": SimpleUploadedFile(
                        "up.txt",
                        b"multipart bytes",
                        content_type="text/plain",
                    ),
                    "data.image": SimpleUploadedFile(
                        "up.png",
                        _png_bytes(),
                        content_type="image/png",
                    ),
                },
                operation_name="Create",
            )
        assert res.response.status_code == 200
        payload = res.data["createMediaSpecimen"]
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
        res = TestClient().query(
            mutation,
            variables={"data": {"label": "form-uploaded", "image": None}},
            files={
                "data.image": SimpleUploadedFile(
                    "form.png",
                    _png_bytes(),
                    content_type="image/png",
                ),
            },
            operation_name="Create",
        )
        assert res.response.status_code == 200
        payload = res.data["createMediaSpecimenImageViaForm"]
        assert payload["errors"] == []
        result = payload["result"]

        # The row landed via the FORM path with the image routed into ``files=``.
        assert models.MediaSpecimen.objects.filter(label="form-uploaded").exists()

    assert result["label"] == "form-uploaded"
    assert result["image"]["name"].endswith("form.png")
    assert result["image"]["width"] == _IMAGE_WIDTH
    assert result["image"]["height"] == _IMAGE_HEIGHT
