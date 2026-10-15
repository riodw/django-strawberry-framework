"""Tests for the shared field-directives containment (``utils/directives.py``).

``validated_field_directives`` raises at field construction. Per-factory call
sites stay in ``tests/test_list_field.py`` / ``tests/mutations/test_fields.py``;
consumer fields over HTTP live in ``examples/fakeshop/test_query/test_list_field_api.py``.
"""

from collections.abc import Iterator
from typing import NoReturn

import pytest
from django.utils.functional import SimpleLazyObject
from typing_extensions import Self, override

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
def test_char_wise_sequences_are_rejected_typed(value: object, type_name: str) -> None:
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


def test_label_names_the_consuming_factory() -> None:
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
def test_ordinary_sequences_pass_through_as_tuples(supplied: tuple[str, ...] | list[str]) -> None:
    """Benign input is returned as a tuple with its contents and order intact."""
    assert validated_field_directives("DjangoListField", supplied) == tuple(supplied)


def test_generator_directives_are_materialized_once() -> None:
    """A single-pass iterable is consumed exactly once and handed back materialized.

    Returning the generator itself would let Strawberry's lazy read find it
    already exhausted, silently dropping every directive from the SDL.
    """
    seen: list[str] = []

    def _gen() -> Iterator[str]:
        for tag in ("a", "b"):
            seen.append(tag)
            yield tag

    result = validated_field_directives("DjangoListField", _gen())

    assert result == ("a", "b")
    assert seen == ["a", "b"]
    # Re-reading the RESULT does not re-drive the source generator.
    assert tuple(result) == ("a", "b")
    assert seen == ["a", "b"]


def test_non_iterable_raises_configuration_error_chaining_the_typeerror() -> None:
    """A non-iterable detonated as a raw TypeError inside ``strawberry.field`` pre-fix."""
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", 42)
    assert str(exc.value) == "DjangoListField directives could not be read (TypeError)."
    assert isinstance(exc.value.__cause__, TypeError)


def test_hostile_iterator_raising_runtimeerror_is_contained() -> None:
    """The drift the enumerated ``except`` tuple left open.

    The two inline copies this helper replaced caught only
    TypeError/ValueError/AttributeError/KeyError/IndexError, so an iterator
    raising anything else - `RuntimeError` here - walked straight through the
    containment and escaped raw. The containment is `Exception`-wide now.
    """

    class HostileDirectives:
        def __iter__(self) -> Self:
            return self

        def __next__(self) -> NoReturn:
            raise RuntimeError("hostile iterator detonated")

    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoMutationField", HostileDirectives())
    assert str(exc.value) == "DjangoMutationField directives could not be read (RuntimeError)."
    assert isinstance(exc.value.__cause__, RuntimeError)


def test_iterator_raising_midway_is_contained() -> None:
    """A container that yields real entries and then raises still rejects typed."""

    class ExplodingDirectives:
        def __iter__(self) -> Iterator[str]:
            yield "a"
            raise ValueError("detonated midway")

    with pytest.raises(ConfigurationError, match=r"directives could not be read") as exc:
        validated_field_directives("DjangoNodesField", ExplodingDirectives())
    assert isinstance(exc.value.__cause__, ValueError)


def test_baseexception_from_iteration_is_not_swallowed() -> None:
    """`KeyboardInterrupt` / `SystemExit` must keep propagating through the containment.

    The `except` is deliberately `Exception`-wide, not `BaseException`-wide: an
    interrupt is not a configuration defect and must never be reported as one.
    """

    class Interrupting:
        def __iter__(self) -> Iterator[str]:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        validated_field_directives("DjangoListField", Interrupting())


def _raising_class_value(raised: type[BaseException]) -> object:
    """A value whose ``__class__`` read raises ``raised`` (so a bare ``isinstance`` raises)."""

    class RaisingClass:
        @property
        @override
        # basedpyright: deliberately a read-only ``__class__`` that raises: the hostile object
        # is the guard's input
        def __class__(self) -> NoReturn:  # pyright: ignore[reportIncompatibleMethodOverride]
            raise raised("hostile __class__")

    return RaisingClass()


class _ClaimsStr:
    """A non-``str`` value whose ``__class__`` claims ``str``."""

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__``: the forged type is the guard's input
    def __class__(self) -> type[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return str


@pytest.mark.parametrize("raised", [RuntimeError, ValueError])
def test_value_whose_class_read_raises_is_the_typed_unreadable_reject(
    raised: type[Exception],
) -> None:
    """The text-or-bytes check reads ``__class__``; that read is inside the containment.

    Dropping the check from the ``try`` lets the value's own exception escape raw.
    """
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", _raising_class_value(raised))
    assert str(exc.value) == (f"DjangoListField directives could not be read ({raised.__name__}).")
    assert isinstance(exc.value.__cause__, raised)


@pytest.mark.parametrize("raised", [KeyboardInterrupt, SystemExit])
def test_interrupt_from_a_class_read_is_not_swallowed(raised: type[BaseException]) -> None:
    """The containment stays ``Exception``-wide for the class read too.

    Routing the check through ``_safe_predicate`` (``BaseException`` to ``False``) fails here.
    """
    with pytest.raises(raised):
        validated_field_directives("DjangoListField", _raising_class_value(raised))


@pytest.mark.parametrize(
    ("value", "type_name"),
    [(SimpleLazyObject(lambda: "@deprecated"), "SimpleLazyObject"), (_ClaimsStr(), "_ClaimsStr")],
    ids=["lazy-proxy", "claims-str"],
)
def test_value_claiming_text_through_its_class_is_still_rejected_as_text(
    value: object,
    type_name: str,
) -> None:
    """The check stays a proxy-aware ``isinstance``: a lazy ``str`` is text, not directives.

    A real-type predicate would let ``tuple()`` iterate the proxy's characters and the
    raw ``AttributeError`` at schema build would return.
    """
    with pytest.raises(ConfigurationError) as exc:
        validated_field_directives("DjangoListField", value)
    assert str(exc.value) == (
        f"DjangoListField directives must be a sequence of directive instances; got {type_name}."
    )
