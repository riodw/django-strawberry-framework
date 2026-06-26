"""Forms for the library app's live form-mutation surface.

These exist to earn three framework branches over a LIVE ``/graphql`` request (the
``examples/fakeshop/test_query/README.md`` discipline - any coverage line reachable
from a real query must be earned there): the raw-pk relation decode (single + multi)
and the ``to_field_name`` conversion. ``Shelf.branch`` / ``Shelf.alt_branches``
relate to the NON-Relay ``BranchType`` primary, so their generated inputs are raw pk
scalars (not ``GlobalID``); the ``branch`` field sets ``to_field_name="name"``
(``Branch.name`` is unique), so the decode resolves the visible Branch by pk and
binds it to the form by name. ``BookGenresModelForm`` adds the live FORM
partial-update M2M-preservation case over the Relay-Node ``BookType``: an omitted
required ``genres`` M2M is reconstructed from the located row rather than cleared.
``BranchWithShelfForm`` adds the model-less plain-form ``perform_mutate`` write-hook case.
"""

from __future__ import annotations

from django import forms

from apps.library import models


class ShelfRelationsForm(forms.ModelForm):
    """A ``Shelf`` ``ModelForm`` whose relations target the non-Relay ``BranchType``.

    ``branch`` (FK) and ``alt_branches`` (M2M) both point at ``Branch``, a non-Relay
    primary with a visibility ``get_queryset`` (it hides ``city="restricted"`` from
    non-staff), so the generated inputs are raw pk - exercising the single + multi
    raw-pk decode arms and the visibility-on-the-raw-pk-branch fix over a live query.
    ``branch`` declares ``to_field_name="name"`` so the decode binds the resolved
    Branch by its unique name rather than its pk (the ``to_field_name`` conversion).
    """

    branch = forms.ModelChoiceField(
        queryset=models.Branch.objects.all(),
        to_field_name="name",
    )

    class Meta:
        model = models.Shelf
        fields = (
            "code",
            "topic",
            "branch",
            "alt_branches",
        )


class BookGenresModelForm(forms.ModelForm):
    """A ``Book`` ``ModelForm`` carrying the required ``genres`` M2M + optional
    ``subtitle``, for the live FORM partial-update preservation cases.

    ``Book`` is the Relay-Node ``BookType`` primary (so the update ``id`` is a
    decodable ``GlobalID`` - unlike the non-Relay ``Shelf``, which supports create
    only). On a ``title``-only partial update two omitted shapes are reconstructed from
    the located row by ``forms/resolvers.py::_reconstruct_partial_data`` rather than
    cleared: the required ``genres`` M2M (no ``to_field_name``; the bound form would
    otherwise fail required-validation - the M2M branch) and the genuinely-optional,
    nullable ``subtitle`` scalar (``blank=True, null=True`` - distinct from a
    ``default=""`` field). ``shelf`` is intentionally NOT a form field, so the located
    row's shelf is preserved untouched by ``save()``.
    """

    class Meta:
        model = models.Book
        fields = ("title", "subtitle", "genres")


class BranchWithShelfForm(forms.Form):
    """A model-less plain ``forms.Form`` whose mutation overrides ``perform_mutate``.

    Backs ``CreateBranchWithShelf`` (a plain ``DjangoFormMutation``). A plain form has no
    ``Meta.model`` and no ``form.save()``, so the default ``perform_mutate`` is a no-op.
    The mutation overrides it to run a real multi-row ORM write - a ``Branch`` plus a
    starter ``Shelf`` under it from these two ``CharField`` values - the model-less write
    the hook exists for (a single ``ModelForm.save()`` cannot create two related rows).
    """

    branch_name = forms.CharField(max_length=200)
    shelf_code = forms.CharField(max_length=200)
