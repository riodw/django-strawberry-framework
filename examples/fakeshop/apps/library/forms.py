"""Forms for the library app's live form-mutation surface.

These exist to earn three framework branches over a LIVE ``/graphql`` request (the
``examples/fakeshop/test_query/README.md`` discipline - any coverage line reachable
from a real query must be earned there): the raw-pk relation decode (single + multi)
and the ``to_field_name`` conversion. ``Shelf.branch`` / ``Shelf.alt_branches``
relate to the NON-Relay ``BranchType`` primary, so their generated inputs are raw pk
scalars (not ``GlobalID``); the ``branch`` field sets ``to_field_name="name"``
(``Branch.name`` is unique), so the decode resolves the visible Branch by pk and
binds it to the form by name.
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
