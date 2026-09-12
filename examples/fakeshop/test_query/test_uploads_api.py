"""Live GraphQL HTTP tests for the spec-037 file/image wire contract.

These earn the package's ``FileField`` / ``ImageField`` coverage over a real
``/graphql/`` round-trip (the placement the ``test_query`` README reserves for
the consumer-visible contract), against the ``scalars`` app's ``MediaSpecimen``
model. They cover:

- the **read** output objects (`DjangoFileType` / `DjangoImageType`) over HTTP,
  the default-nullable SDL shape (a *required* column still renders nullable),
  populated subfield serialization, and the empty-file object-null behavior;
- the **degradation** contract each subfield carries: a backend that cannot
  produce a filesystem path nulls only ``path``, a file gone from storage nulls
  only ``size``, unparseable image bytes null ``width`` / ``height``, and a
  ``SuspiciousFileOperation`` surfaces as a reported error rather than a silent
  ``null``;
- the **write** ``Upload`` mapping: the generated ``MediaSpecimenInput`` exposes
  ``Upload`` over HTTP, and a real GraphQL **multipart** request creates a row
  with uploaded files end to end (URL routing -> view -> multipart parse ->
  schema execution -> JSON response).

The suite drives through the package's own ``TestClient`` (spec-043):
the JSON posts earn the helper's happy-path lines live, and the two multipart
mutations earn the owned path-keyed ``files=`` builder - the nested
input-object shape (``data.attachment`` / ``data.image``) combined with a named
operation is exactly the envelope the engine base's map builder cannot produce.
"""

import io
import os

import pytest
from apps.scalars import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from django_strawberry_framework.testing import TestClient

# A 5x9 PNG so the live ``width`` / ``height`` assertions read distinct,
# deterministic values rather than a square that could pass by coincidence.
_IMAGE_WIDTH = 5
_IMAGE_HEIGHT = 9

# The production error policy substitutes its own stable message for any
# exception it did not expect, so a row that asserts on the ORIGINAL message
# opens the policy's pass-through gate with ``DEBUG=True``. The toolbar
# middleware is dropped in the same override because fakeshop wires
# debug-toolbar behind ``DEBUG`` and it would inject a panel against ``djdt``
# routes the URLconf never computed.
_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}


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


def test_file_output_objects_publish_nullable_subfields_over_http():
    """Every subfield a storage read can fail is nullable; only the stored ``name`` is not.

    The divergence from upstream's all-non-null subfields, read off the live
    schema: ``size`` / ``url`` (and ``width`` / ``height`` on the image type)
    are the reads that answer ``null`` for a vanished file, a backend with no
    absolute paths, or bytes no image parser recognizes, so declaring any of
    them non-null would let one such row take the whole object down. ``name``
    is the stored column string and stays non-null.
    """
    image_fields = {
        field["name"]: field["type"]
        for field in _introspect_type(
            "DjangoImageType",
            "fields { name type { kind name } }",
        )["fields"]
    }

    assert image_fields == {
        "name": {"kind": "NON_NULL", "name": None},
        "size": {"kind": "SCALAR", "name": "Int"},
        "url": {"kind": "SCALAR", "name": "String"},
        "width": {"kind": "SCALAR", "name": "Int"},
        "height": {"kind": "SCALAR", "name": "Int"},
    }


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


@pytest.mark.django_db
def test_empty_image_beside_populated_file_resolves_only_the_image_to_null_over_http(tmp_path):
    """The empty-file guard is per column: an unset image is ``null`` beside a resolved file.

    Both columns are required, so a row stored with only the attachment leaves
    ``image`` holding ``""``. The generated parent resolver maps that one empty
    ``FieldFile`` to ``None`` without disturbing its populated sibling in the
    same row - the whole-row ``null`` that a shared guard would produce is the
    failure this rules out.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="file-only")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.save()

        res = TestClient().query(
            "{ allMediaSpecimens { label attachment { name } image { name } } }",
        )
        assert res.response.status_code == 200
        row = res.data["allMediaSpecimens"][0]

    assert row["label"] == "file-only"
    assert row["attachment"]["name"].endswith("doc.txt")
    assert row["image"] is None


@pytest.mark.django_db
def test_storage_without_absolute_paths_nulls_only_the_path_subfield_over_http(
    tmp_path,
    monkeypatch,
):
    """A backend that cannot produce a path nulls ``path`` alone; ``name`` / ``url`` resolve.

    ``types/converters.py::_safe_file_attr`` guards each subfield, not the parent
    object: a storage backend whose ``path`` raises ``NotImplementedError`` (the
    S3-style case, and the reason the opt-in subfield is nullable) degrades that
    one subfield while the sibling subfields of the SAME object still answer.
    All three are selected in one request, so a guard that sat on the parent
    would show up as ``attachment: null`` rather than a null ``path``.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="unpathable")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.save()

        def _no_absolute_path(self, name):
            raise NotImplementedError("This backend doesn't support absolute paths.")

        monkeypatch.setattr(FileSystemStorage, "path", _no_absolute_path)

        res = TestClient().query(
            "{ allMediaSpecimensWithPath { attachment { name path url } } }",
        )
        assert res.response.status_code == 200
        attachment = res.data["allMediaSpecimensWithPath"][0]["attachment"]

    assert attachment["path"] is None
    assert attachment["name"].endswith("doc.txt")
    # ``url`` is string-built from MEDIA_URL and never consults storage paths.
    assert attachment["url"].endswith("doc.txt")


@pytest.mark.django_db
def test_vanished_file_resolves_size_to_null_over_http(tmp_path):
    """A file gone from storage nulls ``size``; the stored ``name`` still resolves.

    ``FieldFile.size`` raises ``FileNotFoundError`` (an ``OSError``) once the
    underlying file is deleted, and the subfield guard degrades it to ``null``
    instead of failing the request. ``name`` is the stored column string, read
    without the guard, so it proves the object itself survived.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="vanished")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.save()
        os.remove(specimen.attachment.path)

        res = TestClient().query("{ allMediaSpecimens { attachment { name size } } }")
        assert res.response.status_code == 200
        attachment = res.data["allMediaSpecimens"][0]["attachment"]

    assert attachment["size"] is None
    assert attachment["name"].endswith("doc.txt")


@pytest.mark.django_db
def test_corrupt_image_resolves_width_and_height_to_null_over_http(tmp_path):
    """Unparseable image bytes resolve ``width`` / ``height`` to ``null``; ``name`` survives.

    Django answers a dimension read on bytes Pillow cannot parse with ``None``
    rather than an exception, so what carries this case is the nullability
    ``DjangoImageType`` declares on both dimensions - the deliberate divergence
    from upstream's all-non-null subfields. Declaring them non-null would turn a
    single corrupt row into a non-null execution error that takes the whole
    object down; the sibling rows read the same two subfields from a valid
    image, which is only the success half. The bytes are stored with
    ``save=False`` so nothing validates them as an image on the way to storage.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="corrupt")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.image.save("broken.png", ContentFile(b"not an image"), save=False)
        specimen.save()

        res = TestClient().query("{ allMediaSpecimens { image { name width height } } }")
        assert res.response.status_code == 200
        image = res.data["allMediaSpecimens"][0]["image"]

    assert image["width"] is None
    assert image["height"] is None
    assert image["name"].endswith("broken.png")


@pytest.mark.django_db
def test_suspicious_file_operation_is_reported_not_nulled_over_http(tmp_path, monkeypatch):
    """A ``SuspiciousFileOperation`` on a subfield is reported, never a silent ``null``.

    It is a ``SuspiciousOperation`` - not one of the storage-shaped exceptions
    the subfield guard degrades - so a path-traversal signal has to reach the
    client as an error instead of reading like an ordinary backend that cannot
    produce a path. The request runs under the ``DEBUG`` pass-through so the
    original message is readable; with the production policy in force the same
    exception would still be reported, under the policy's stable text.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path), **_ERROR_POLICY_PASS_THROUGH):
        specimen = models.MediaSpecimen(label="suspicious")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.save()

        def _suspicious_path(self, name):
            raise SuspiciousFileOperation("escaped media root")

        monkeypatch.setattr(FileSystemStorage, "path", _suspicious_path)

        res = TestClient().query(
            "{ allMediaSpecimensWithPath { attachment { path } } }",
            assert_no_errors=False,
        )
        assert res.response.status_code == 200

    assert res.errors, res.data
    assert "escaped media root" in res.errors[0]["message"], res.errors


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
