"""Model field annotations agree with the fields they annotate.

basedpyright runs without the django-stubs mypy plugin, so every model field spells its solved
generic by hand (``name: models.TextField[str | Combinable, str] = models.TextField()``, directly
or through a ``TypeAlias``), mirroring the set and get types the plugin would infer. Nothing else
reads those annotations against the field, so this module does, for every annotated field of every
concrete fakeshop model (facts from the field the app registry holds) and every annotated field
declared under the test trees (facts from the field call itself, since most test models are built
inside a test function and never reach a registry this module can walk):

* the annotation's field class is the field's class;
* ``None`` is in the get type exactly when the field is ``null=True``, and in the set type exactly
  when it is ``null=True`` or a primary key with a default (an unsaved row holds ``None`` there
  until save); an argument holding ``object`` already admits ``None``; never on a
  ``ManyToManyField``, where ``null`` has no effect;
* a ``ForeignKey`` / ``OneToOneField`` is ``[Target | Combinable, Target]`` and a ``ForeignObject``
  (written through its carrier columns) ``[Target, Target]``; a string target naming an app label
  no installed app has (no class to spell) is ``models.Model``;
* a ``ManyToManyField`` is ``[Target, Through]``: the declared through model, or ``models.Model``
  for the through table Django creates (no name to spell);
* a field class whose descriptor types django-stubs spells concretely carries exactly those types.

Annotations are read from source with ``ast`` and never evaluated: Django fields have no
``__class_getitem__``, and the aliases live under ``TYPE_CHECKING``. A name in an annotation is
resolved against the module that spelled it (its globals, then the imports its ``TYPE_CHECKING``
block makes), and a generic alias is expanded by substituting its type variables in order of
first appearance. Anything the reader cannot decide fails the case instead of passing it.
"""

from __future__ import annotations

import ast
import builtins
import datetime
import decimal
import importlib
import importlib.util
import inspect
import sys
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal, TypeAlias

import pytest
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.expressions import Combinable
from django.db.models.fields.reverse_related import ManyToManyRel

REPO_ROOT = Path(__file__).resolve().parent.parent
FAKESHOP_ROOT = REPO_ROOT / "examples" / "fakeshop"
FAKESHOP_APP_LABELS = (
    "glossary",
    "kanban",
    "library",
    "products",
    "scalars",
)
FIXTURE_MODEL_FILES = ("tests/_relation_fixtures.py", "tests/optimizer/_link_models.py")
DJANGO_FIELD_MODULES = frozenset(
    {
        "django.db.models",
        "django.db.models.fields",
        "django.db.models.fields.json",
        "django.db.models.fields.related",
    },
)
RELATION_CLASS_NAMES = frozenset({"ForeignKey", "ForeignObject", "OneToOneField"})

# The descriptor types django-stubs spells on each field class (``_pyi_private_set_type``,
# ``_pyi_private_get_type``), looked up along the field class's MRO; ``None`` where the stubs
# leave the set type ``Any``, which an annotation may spell as any type that accepts every value.
StubTypes: TypeAlias = tuple[tuple[type[object], ...] | None, tuple[type[object], ...]]
STUB_TYPES: dict[str, StubTypes] = {
    "AutoField": ((Combinable, int, str), (int,)),
    "BinaryField": (None, (bytes, memoryview)),
    "BooleanField": ((bool, Combinable), (bool,)),
    "CharField": ((str, int, Combinable), (str,)),
    "DateField": ((str, datetime.date, Combinable), (datetime.date,)),
    "DateTimeField": (
        (
            str,
            datetime.datetime,
            datetime.date,
            Combinable,
        ),
        (datetime.datetime,),
    ),
    "DecimalField": (
        (
            str,
            float,
            decimal.Decimal,
            Combinable,
        ),
        (decimal.Decimal,),
    ),
    "DurationField": (None, (datetime.timedelta,)),
    "EmailField": ((str, Combinable), (str,)),
    "FloatField": (
        (
            float,
            int,
            str,
            Combinable,
        ),
        (float,),
    ),
    "IPAddressField": ((str, Combinable), (str,)),
    "IntegerField": (
        (
            float,
            int,
            str,
            Combinable,
        ),
        (int,),
    ),
    "TextField": ((str, Combinable), (str,)),
    "TimeField": (
        (
            str,
            datetime.time,
            datetime.datetime,
            Combinable,
        ),
        (datetime.time,),
    ),
    "UUIDField": ((str, uuid.UUID), (uuid.UUID,)),
}


class UndecidableError(Exception):
    """The annotation or the field call has a shape this reader cannot decide."""


@dataclass(frozen=True)
class Name:
    """A name as one module spelled it in an annotation (``models.TextField``, ``Combinable``)."""

    module: str
    dotted: str

    @property
    def last(self) -> str:
        """The last dotted component, the spelling the source-only comparison uses."""
        return self.dotted.rsplit(".", 1)[-1]


@dataclass(frozen=True)
class Generic:
    """A subscripted annotation: its base and one union-member set per type argument."""

    base: Name
    args: tuple[frozenset[Member], ...]


Member: TypeAlias = "Name | Generic | None"


@dataclass(frozen=True)
class ModuleSource:
    """What one module's source binds: aliases, type variables and imported names."""

    name: str
    aliases: dict[str, ast.expr]
    typevars: frozenset[str]
    imports: dict[str, tuple[str, str | None]]


def _absolute_module(
    module: str | None,
    level: int,
    importer: str,
    *,
    package: bool,
) -> str:
    """Resolve an ``ImportFrom`` target against the importing module's package."""
    if level == 0:
        return module or ""
    base = importer if package else importer.rpartition(".")[0]
    return importlib.util.resolve_name("." * level + (module or ""), base)


@cache
def _parsed(path: Path) -> ast.Module:
    """Parse ``path`` once per process."""
    return ast.parse(path.read_text(encoding="utf-8"))


_SOURCES: dict[str, ModuleSource] = {}


def _module_source(key: str, path: Path, dotted: str) -> ModuleSource:
    """Collect the aliases, type variables and imports bound anywhere in ``path``.

    ``key`` names the module in every ``Name`` it spells; ``dotted`` is its import path, which
    relative imports resolve against.
    """
    if key in _SOURCES:
        return _SOURCES[key]
    tree = _parsed(path)
    aliases: dict[str, ast.expr] = {}
    typevars: set[str] = set()
    imports: dict[str, tuple[str, str | None]] = {}
    package = path.name == "__init__.py"
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            spelled = ast.unparse(node.annotation)
            if node.value is not None and spelled.rsplit(".", 1)[-1] == "TypeAlias":
                aliases[node.target.id] = node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            value = node.value
            if isinstance(value, ast.Call) and ast.unparse(value.func).endswith("TypeVar"):
                typevars.add(target.id)
            elif isinstance(value, ast.Subscript | ast.BinOp):
                aliases[target.id] = value
        elif isinstance(node, ast.ImportFrom):
            source = _absolute_module(node.module, node.level, dotted, package=package)
            for alias in node.names:
                imports[alias.asname or alias.name] = (source, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    imports[alias.asname] = (alias.name, None)
                else:
                    head = alias.name.split(".", 1)[0]
                    imports[head] = (head, None)
    _SOURCES[key] = ModuleSource(key, aliases, frozenset(typevars), imports)
    return _SOURCES[key]


def _source_of(module: str) -> ModuleSource | None:
    """Return the parsed source of a first-party module, or ``None`` for a module without one."""
    if module in _SOURCES:
        return _SOURCES[module]
    loaded = sys.modules.get(module)
    origin = loaded.__file__ if loaded is not None else None
    if origin is None:
        try:
            spec = importlib.util.find_spec(module)
        except ModuleNotFoundError:
            return None
        origin = spec.origin if spec is not None else None
    if origin is None or not origin.endswith(".py"):
        return None
    path = Path(origin)
    if REPO_ROOT not in path.resolve().parents:
        return None
    return _module_source(module, path, module)


def _alias(src: ModuleSource, name: str) -> tuple[ModuleSource, ast.expr] | None:
    """Return the alias ``name`` denotes in ``src``, following a first-party import."""
    if name in src.aliases:
        return src, src.aliases[name]
    imported = src.imports.get(name)
    if imported is None or imported[1] is None:
        return None
    other = _source_of(imported[0])
    if other is None or imported[1] not in other.aliases:
        return None
    return other, other.aliases[imported[1]]


def _typevar_order(src: ModuleSource, expr: ast.expr) -> list[str]:
    """Return the alias's type variables in order of first appearance, PEP 484's parameter order."""
    names = sorted(
        (node for node in ast.walk(expr) if isinstance(node, ast.Name)),
        key=lambda node: (node.lineno, node.col_offset),
    )
    order: list[str] = []
    for node in names:
        if node.id in src.typevars and node.id not in order:
            order.append(node.id)
    return order


def _subscript_args(node: ast.Subscript) -> list[ast.expr]:
    """Return a subscript's arguments, one per comma-separated slot."""
    return list(node.slice.elts) if isinstance(node.slice, ast.Tuple) else [node.slice]


def expand(
    node: ast.expr,
    src: ModuleSource,
    subst: dict[str, frozenset[Member]] | None = None,
) -> frozenset[Member]:
    """Expand an annotation expression to its union members, aliases and type variables resolved."""
    bound = subst or {}
    if isinstance(node, ast.Constant):
        if node.value is None:
            return frozenset({None})
        if isinstance(node.value, str):
            return expand(ast.parse(node.value, mode="eval").body, src, bound)
        raise UndecidableError(ast.unparse(node))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return expand(node.left, src, bound) | expand(node.right, src, bound)
    if isinstance(node, ast.Name):
        if node.id in bound:
            return bound[node.id]
        aliased = _alias(src, node.id)
        if aliased is not None:
            return expand(aliased[1], aliased[0])
        return frozenset({Name(src.name, node.id)})
    if isinstance(node, ast.Attribute):
        return frozenset({Name(src.name, ast.unparse(node))})
    if isinstance(node, ast.Subscript):
        args = _subscript_args(node)
        if isinstance(node.value, ast.Name) and node.value.id not in bound:
            aliased = _alias(src, node.value.id)
            if aliased is not None:
                alias_src, alias_expr = aliased
                params = _typevar_order(alias_src, alias_expr)
                if len(params) != len(args):
                    raise UndecidableError(ast.unparse(node))
                values = {
                    param: expand(arg, src, bound) for param, arg in zip(params, args, strict=True)
                }
                return expand(alias_expr, alias_src, values)
        base = ast.unparse(node.value)
        last = base.rsplit(".", 1)[-1]
        if last == "Optional":
            return expand(args[0], src, bound) | {None}
        if last == "Union":
            union: frozenset[Member] = frozenset()
            for arg in args:
                union |= expand(arg, src, bound)
            return union
        members = tuple(expand(arg, src, bound) for arg in args)
        return frozenset({Generic(Name(src.name, base), members)})
    raise UndecidableError(ast.unparse(node))


def _field_generic(members: frozenset[Member]) -> Generic | None:
    """Return the annotation as one subscripted generic, or ``None`` for any other shape."""
    if len(members) != 1:
        return None
    (member,) = members
    return member if isinstance(member, Generic) else None


@cache
def _module_namespace(module: str) -> dict[str, object]:
    """Return ``module``'s run-time globals."""
    return dict(vars(importlib.import_module(module)))


def resolve(name: Name) -> object:
    """Resolve a spelled name the way the checker reads it: globals, then any import, then builtins."""
    head, _, rest = name.dotted.partition(".")
    namespace = _module_namespace(name.module)
    if head in namespace:
        obj = namespace[head]
    else:
        src = _source_of(name.module)
        imported = src.imports.get(head) if src is not None else None
        if imported is not None:
            target = importlib.import_module(imported[0])
            obj = target if imported[1] is None else getattr(target, imported[1])
        elif hasattr(builtins, head):
            obj = getattr(builtins, head)
        else:
            raise UndecidableError(f"{name.module}: cannot resolve {name.dotted!r}")
    for part in rest.split(".") if rest else ():
        obj = getattr(obj, part)
    return obj


@dataclass(frozen=True)
class Expect:
    """One expected type: its class name and, where the facts come from run time, the class."""

    name: str
    obj: object = None


@dataclass(frozen=True)
class Facts:
    """What the field declares, from the registry's field or from the field call."""

    field_class: Expect
    stub_types: StubTypes | None
    null: bool
    kind: Literal["relation", "m2m", "plain"]
    target: Expect | None
    through: Expect | None
    pk_default: bool = False

    @property
    def set_null(self) -> bool:
        """Whether the set type admits ``None``: a nullable column, or a defaulted primary key.

        An unsaved row may hold ``None`` in a primary key whose default fills it on save, so
        the set type of a defaulted primary key carries ``None`` even when the column does not.
        """
        return self.null or self.pk_default


Matcher: TypeAlias = Callable[[Name, Expect], bool]
OBJECT = Expect("object", object)
# The second ``ManyToManyField`` argument when Django creates the through table itself.
AUTO_THROUGH = Expect("Model", models.Model)
# The target of a relation whose ``"app_label.Model"`` string names an app no installed app has.
UNRESOLVABLE_TARGET = Expect("Model", models.Model)


def _by_identity(member: Name, expected: Expect) -> bool:
    """Run-time comparison: the spelled name resolves to the expected class itself."""
    return resolve(member) is expected.obj


def _by_name(member: Name, expected: Expect) -> bool:
    """Source-only comparison: the spelled name's last component is the expected class name."""
    return member.last == expected.name


def _stub_types_of(field_class: type[object]) -> StubTypes | None:
    """Return the django-stubs descriptor types of the first Django class along the MRO."""
    for klass in field_class.__mro__:
        if klass.__module__.startswith("django.db.models") and klass.__name__ in STUB_TYPES:
            return STUB_TYPES[klass.__name__]
    return None


def _expects(classes: tuple[type[object], ...]) -> tuple[Expect, ...]:
    """Wrap stub classes as expectations."""
    return tuple(Expect(klass.__name__, klass) for klass in classes)


def _members_match(
    members: frozenset[Member],
    expected: tuple[Expect, ...],
    *,
    null: bool,
    match: Matcher,
) -> bool:
    """Whether a union is exactly ``expected`` plus ``None`` when, and only when, ``null``."""
    if (None in members) != null:
        return False
    names = [member for member in members if isinstance(member, Name)]
    if len(names) != len(members) - (1 if null else 0) or len(names) != len(expected):
        return False
    return all(any(match(name, want) for name in names) for want in expected)


def _null_agrees(members: frozenset[Member], *, null: bool, match: Matcher) -> bool:
    """Whether ``None`` is in the union exactly when ``null``.

    A union holding ``object`` already admits ``None``, so it agrees either way.
    """
    if any(isinstance(member, Name) and match(member, OBJECT) for member in members):
        return True
    return (None in members) == null


def problems(annotation: Generic, facts: Facts, match: Matcher) -> list[str]:
    """List every way ``annotation`` disagrees with ``facts`` (empty when it agrees)."""
    found: list[str] = []
    if not match(annotation.base, facts.field_class):
        found.append(f"annotates {annotation.base.dotted}, field is {facts.field_class.name}")
    args = annotation.args
    if facts.kind == "m2m":
        if len(args) != 2:
            return [*found, f"ManyToManyField takes [To, Through], got {len(args)} args"]
        if any(None in arg for arg in args):
            found.append("ManyToManyField arguments never include None")
        if facts.target is not None and not _members_match(
            args[0],
            (facts.target,),
            null=False,
            match=match,
        ):
            found.append(f"target is {facts.target.name}")
        if facts.through is not None and not _members_match(
            args[1],
            (facts.through,),
            null=False,
            match=match,
        ):
            found.append(f"through model is {facts.through.name}")
        return found
    if len(args) != 2:
        return [*found, f"expected [set type, get type], got {len(args)} args"]
    set_arg, get_arg = args
    if not _null_agrees(set_arg, null=facts.set_null, match=match):
        found.append(
            f"set type needs None exactly when null or a defaulted primary key ({facts.set_null})",
        )
    if not _null_agrees(get_arg, null=facts.null, match=match):
        found.append(f"get type needs None exactly when null={facts.null}")
    if facts.kind == "relation" and facts.target is not None:
        # A ForeignObject is written through its carrier columns, never an expression.
        settable = (
            (facts.target,)
            if facts.field_class.name == "ForeignObject"
            else (facts.target, Expect("Combinable", Combinable))
        )
        if not _members_match(set_arg, settable, null=facts.set_null, match=match):
            found.append(f"set type must be {' | '.join(e.name for e in settable)}")
        if not _members_match(get_arg, (facts.target,), null=facts.null, match=match):
            found.append(f"get type must be {facts.target.name}")
    elif facts.stub_types is not None:
        set_types, get_types = facts.stub_types
        if set_types is not None and not _members_match(
            set_arg,
            _expects(set_types),
            null=facts.set_null,
            match=match,
        ):
            found.append(f"set type must be {' | '.join(t.__name__ for t in set_types)}")
        if not _members_match(get_arg, _expects(get_types), null=facts.null, match=match):
            found.append(f"get type must be {' | '.join(t.__name__ for t in get_types)}")
    return found


@dataclass(frozen=True)
class Case:
    """One annotated field declaration to check."""

    id: str
    origin: str
    module: str
    class_name: str
    field_name: str
    statement: ast.AnnAssign
    model: type[models.Model] | None


def _annotated_fields(cls: ast.ClassDef) -> Iterator[tuple[str, ast.AnnAssign]]:
    """Yield the class body's ``name: <annotation> = <call>`` statements."""
    for stmt in cls.body:
        if (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and isinstance(stmt.value, ast.Call)
        ):
            yield stmt.target.id, stmt


def _fakeshop_cases() -> list[Case]:
    """Every annotated field on every concrete fakeshop model and its fakeshop model bases."""
    cases: list[Case] = []
    for label in FAKESHOP_APP_LABELS:
        for model in apps.get_app_config(label).get_models():
            for klass in model.__mro__:
                if not klass.__module__.startswith("apps."):
                    continue
                path = inspect.getsourcefile(klass)
                if path is None:
                    continue
                tree = _parsed(Path(path))
                cls = next(
                    node
                    for node in tree.body
                    if isinstance(node, ast.ClassDef) and node.name == klass.__qualname__
                )
                inherited = "" if klass is model else f" (declared on {klass.__name__})"
                cases.extend(
                    Case(
                        id=f"{model._meta.label}.{field_name}{inherited}",
                        origin=label,
                        module=klass.__module__,
                        class_name=klass.__name__,
                        field_name=field_name,
                        statement=stmt,
                        model=model,
                    )
                    for field_name, stmt in _annotated_fields(cls)
                )
    return cases


def _test_files() -> Iterator[tuple[str, Path]]:
    """Yield ``(dotted module, path)`` for every Python file of the test trees."""
    for path in sorted((REPO_ROOT / "tests").rglob("*.py")):
        yield ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts), path
    for path in sorted(FAKESHOP_ROOT.rglob("*.py")):
        rel = path.relative_to(FAKESHOP_ROOT)
        if {"tests", "test_query"} & set(rel.parts[:-1]):
            yield ".".join(rel.with_suffix("").parts), path


def _declares_a_field(stmt: ast.AnnAssign, src: ModuleSource) -> bool:
    """Whether a class-body statement declares a Django field or annotates one.

    An annotation the reader cannot decide counts, so its case fails instead of being dropped.
    """
    value = stmt.value
    if isinstance(value, ast.Call) and _django_field_class(value.func, src) is not None:
        return True
    try:
        generic = _field_generic(expand(stmt.annotation, src))
    except UndecidableError:
        return True
    return _is_django_field_annotation(generic, src)


def _test_tree_cases() -> list[Case]:
    """Every field declaration that carries an annotation, in any class under the test trees."""
    cases: list[Case] = []
    for module, path in _test_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        src = _module_source(rel, path, module.removesuffix(".__init__"))
        for node in ast.walk(_parsed(path)):
            if isinstance(node, ast.ClassDef):
                cases.extend(
                    Case(
                        id=f"{rel}:{node.lineno}::{node.name}.{field_name}",
                        origin=rel,
                        module=rel,
                        class_name=node.name,
                        field_name=field_name,
                        statement=stmt,
                        model=None,
                    )
                    for field_name, stmt in _annotated_fields(node)
                    if _declares_a_field(stmt, src)
                )
    return cases


def _runtime_facts(model: type[models.Model], field_name: str) -> Facts | None:
    """Facts from the registry's field, or ``None`` when ``field_name`` names no model field."""
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None
    if not isinstance(field, models.Field):
        return None
    field_class: type[object] = type(field)
    related = field.related_model
    target = Expect(related.__name__, related) if isinstance(related, type) else None
    if field.many_to_many:
        rel = field.remote_field
        through = rel.through if isinstance(rel, ManyToManyRel) else None
        through_expect = (
            None
            if through is None
            else AUTO_THROUGH
            if through._meta.auto_created
            else Expect(through.__name__, through)
        )
        return Facts(
            Expect(field_class.__name__, field_class),
            None,
            False,
            "m2m",
            target,
            through_expect,
        )
    kind: Literal["relation", "plain"] = "relation" if field.is_relation else "plain"
    return Facts(
        Expect(field_class.__name__, field_class),
        _stub_types_of(field_class),
        field.null,
        kind,
        target,
        None,
        pk_default=field.primary_key and field.has_default(),
    )


def _spelled_field_class(dotted: str, src: ModuleSource) -> type[object] | None:
    """Return the Django field class ``dotted`` spells in ``src`` (``models.TextField``), else ``None``."""
    head, _, attr = dotted.partition(".")
    imported = src.imports.get(head)
    if imported is None:
        return None
    if (
        attr
        and "." not in attr
        and imported in {("django.db", "models"), ("django.db.models", None)}
    ):
        name = attr
    elif not attr and imported[0] in DJANGO_FIELD_MODULES and imported[1]:
        name = imported[1]
    else:
        return None
    found: object = getattr(models, name, None)
    return found if isinstance(found, type) and issubclass(found, models.Field) else None


def _django_field_class(func: ast.expr, src: ModuleSource) -> type[object] | None:
    """Return the Django field class a call spells, else ``None``."""
    if isinstance(func, ast.Name | ast.Attribute):
        return _spelled_field_class(ast.unparse(func), src)
    return None


def _target_text(node: ast.expr, owner: str) -> str:
    """Return the class name a relation's ``to`` argument spells (``"app.Model"`` -> ``Model``)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        name = node.value.rsplit(".", 1)[-1]
        return owner if name == "self" else name
    raise UndecidableError(f"relation target {ast.unparse(node)}")


def _target_expect(node: ast.expr, owner: str) -> Expect:
    """Return what a relation's ``to`` argument resolves to, ``models.Model`` when nothing can.

    Only an ``"app_label.Model"`` string whose app label no installed app has is unresolvable;
    every other target keeps the strict by-name comparison.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and "." in node.value:
        app_label = node.value.split(".", 1)[0]
        try:
            apps.get_app_config(app_label)
        except LookupError:
            return UNRESOLVABLE_TARGET
    return Expect(_target_text(node, owner))


def _call_facts(call: ast.Call, owner: str, src: ModuleSource) -> Facts:
    """Facts from the field call itself, for a model class no registry walk reaches."""
    if any(keyword.arg is None for keyword in call.keywords):
        raise UndecidableError(f"{ast.unparse(call)}: ** arguments hide null / to")
    kwargs = {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg}
    null_node = kwargs.get("null")
    if null_node is not None and not (
        isinstance(null_node, ast.Constant) and isinstance(null_node.value, bool)
    ):
        raise UndecidableError(f"null={ast.unparse(null_node)}")
    null = isinstance(null_node, ast.Constant) and null_node.value is True
    field_class = _django_field_class(call.func, src)
    class_name = ast.unparse(call.func).rsplit(".", 1)[-1]
    expect = Expect(class_name, field_class)
    to_node = call.args[0] if call.args else kwargs.get("to")
    if class_name == "ManyToManyField":
        if to_node is None:
            raise UndecidableError(ast.unparse(call))
        through_node = kwargs.get("through")
        through = (
            AUTO_THROUGH if through_node is None else Expect(_target_text(through_node, owner))
        )
        return Facts(expect, None, False, "m2m", _target_expect(to_node, owner), through)
    if class_name in RELATION_CLASS_NAMES:
        if to_node is None:
            raise UndecidableError(ast.unparse(call))
        return Facts(expect, None, null, "relation", _target_expect(to_node, owner), None)
    stub_types = _stub_types_of(field_class) if field_class is not None else None
    primary_key = kwargs.get("primary_key")
    pk_default = (
        isinstance(primary_key, ast.Constant) and primary_key.value is True and "default" in kwargs
    )
    return Facts(expect, stub_types, null, "plain", None, None, pk_default=pk_default)


def _is_django_field_annotation(generic: Generic | None, src: ModuleSource) -> bool:
    """Whether an expanded annotation subscripts a Django field class."""
    if generic is None:
        return False
    base_src = _source_of(generic.base.module) or src
    return _spelled_field_class(generic.base.dotted, base_src) is not None


def _require_source(module: str) -> ModuleSource:
    """Return the module's parsed source; every case's module is first-party."""
    src = _source_of(module)
    assert src is not None, f"no source for {module}"
    return src


FAKESHOP_CASES = _fakeshop_cases()
TEST_TREE_CASES = _test_tree_cases()


@pytest.mark.parametrize("case", FAKESHOP_CASES, ids=[case.id for case in FAKESHOP_CASES])
def test_fakeshop_field_annotation_agrees_with_the_field(case: Case) -> None:
    src = _require_source(case.module)
    generic = _field_generic(expand(case.statement.annotation, src))
    assert case.model is not None
    facts = _runtime_facts(case.model, case.field_name)
    if facts is None:
        assert generic is None or not _is_django_field_annotation(generic, src), (
            f"{case.id}: a field annotation on a name that is no model field"
        )
        return
    assert generic is not None, f"{case.id}: a model field annotated without its field generic"
    assert problems(generic, facts, _by_identity) == []


@pytest.mark.parametrize("case", TEST_TREE_CASES, ids=[case.id for case in TEST_TREE_CASES])
def test_test_tree_field_annotation_agrees_with_the_field_call(case: Case) -> None:
    src = _require_source(case.module)
    value = case.statement.value
    assert isinstance(value, ast.Call)
    generic = _field_generic(expand(case.statement.annotation, src))
    assert generic is not None, f"{case.id}: a model field annotated without its field generic"
    facts = _call_facts(value, case.class_name, src)
    assert problems(generic, facts, _by_name) == []


def test_the_gate_reaches_every_fakeshop_app_and_both_fixture_modules() -> None:
    assert {case.origin for case in FAKESHOP_CASES} == set(FAKESHOP_APP_LABELS)
    assert set(FIXTURE_MODEL_FILES) <= {case.origin for case in TEST_TREE_CASES}
