"""Tests for the shared field-directives containment (``utils/directives.py``).

Every field factory in the package routes its consumer-supplied ``directives=``
through ``validated_field_directives`` before handing it to
``strawberry.field()``. The rows here pin the containment itself; the per-factory
tests (``tests/test_list_field.py``, ``tests/mutations/test_fields.py``,
``tests/test_relay_node_field.py``, ``tests/auth/``) pin that each factory
actually calls it and interpolates its own label.
"""

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.directives import validated_field_directives


@pytest.mark.parametrize(
    ("value", "type_name"),
    [
        ("@deprecated", "str"),
        (b"@deprecated", "bytes"),
        (bytearray(b"@deprecated"), "bytearray"),
        (memoryview(b"@deprecated"), "memoryview"),
    ],
)
def test_char_wise_sequences_are_rejected_typed(value, type_name):
    """The four Iterable-but-not-directives types reject at the construction line.

    A bare `str` iterates into characters and a `bytes` / `bytearray` /
    `memoryview` into ints; Strawberry consumes the iterable lazily, so an
    unvalidated value builds a field out of chars or ints and detonates at
    schema build or SDL render instead of here.
    """
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", value)
    assert str(exc.value) == (
        f"DjangoListField directives must be a sequence of directive instances; got {type_name}."
    )


def test_label_names_the_consuming_factory():
    """The label is interpolated so the message points at the assignment site."""
    with pytest.raises(ConfigurationError, match=r"^auth field directives must be"):
        validated_field_directives("auth field", "oops")


@pytest.mark.parametrize(
    "supplied",
    [
        (),
        [],
        ("a", "b"),
        ["a", "b"],
    ],
)
def test_ordinary_sequences_pass_through_as_tuples(supplied):
    """Benign input is returned as a tuple with its contents and order intact."""
    assert validated_field_directives("DjangoListField", supplied) == tuple(supplied)


def test_generator_directives_are_materialized_once():
    """A single-pass iterable is consumed exactly once and handed back materialized.

    Returning the generator itself would let Strawberry's lazy read find it
    already exhausted, silently dropping every directive from the SDL.
    """
    seen = []

    def _gen():
        for tag in ("a", "b"):
            seen.append(tag)
            yield tag

    result = validated_field_directives("DjangoListField", _gen())

    assert result == ("a", "b")
    assert seen == ["a", "b"]
    # Re-reading the RESULT does not re-drive the source generator.
    assert tuple(result) == ("a", "b")
    assert seen == ["a", "b"]


def test_non_iterable_raises_configuration_error_chaining_the_typeerror():
    """A non-iterable detonated as a raw TypeError inside ``strawberry.field`` pre-fix."""
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", 42)
    assert str(exc.value) == "DjangoListField directives could not be read (TypeError)."
    assert isinstance(exc.value.__cause__, TypeError)


def test_hostile_iterator_raising_runtimeerror_is_contained():
    """The drift the enumerated ``except`` tuple left open.

    The two inline copies this helper replaced caught only
    TypeError/ValueError/AttributeError/KeyError/IndexError, so an iterator
    raising anything else - `RuntimeError` here - walked straight through the
    containment and escaped raw. The containment is `Exception`-wide now.
    """

    class HostileDirectives:
        def __iter__(self):
            return self

        def __next__(self):
            raise RuntimeError("hostile iterator detonated")

    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoMutationField", HostileDirectives())
    assert str(exc.value) == "DjangoMutationField directives could not be read (RuntimeError)."
    assert isinstance(exc.value.__cause__, RuntimeError)


def test_iterator_raising_midway_is_contained():
    """A container that yields real entries and then raises still rejects typed."""

    class ExplodingDirectives:
        def __iter__(self):
            yield "a"
            raise ValueError("detonated midway")

    with pytest.raises(ConfigurationError, match=r"directives could not be read") as exc:
        validated_field_directives("DjangoNodesField", ExplodingDirectives())
    assert isinstance(exc.value.__cause__, ValueError)


def test_baseexception_from_iteration_is_not_swallowed():
    """`KeyboardInterrupt` / `SystemExit` must keep propagating through the containment.

    The `except` is deliberately `Exception`-wide, not `BaseException`-wide: an
    interrupt is not a configuration defect and must never be reported as one.
    """

    class Interrupting:
        def __iter__(self):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        validated_field_directives("DjangoListField", Interrupting())
