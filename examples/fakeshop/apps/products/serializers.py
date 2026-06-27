# TODO(spec-039 Slice 3): Add DRF ModelSerializer classes for the live products
# serializer-mutation surface.
# Pseudo flow:
#   - Import DRF serializers and the products `Item` model.
#   - Define a reusable rejected-name sentinel for field-level validation tests.
#   - `ItemSerializer` exposes `name`, `description`, `category`, and `attachment`.
#   - `validate_name(...)` rejects the sentinel with a DRF validation error.
#   - Object-level `validate(...)` reads `self.context["request"]` and rejects an
#     item name equal to the authenticated username.
#
# Live-test obligations:
#   - `attachment` proves Upload values are routed into serializer `data`.
#   - `validate()` proves `context={"request": ...}` reaches the serializer.
#   - The model's `unique_item_per_category` validator supplies the `"__all__"`
#     envelope case during partial update.
