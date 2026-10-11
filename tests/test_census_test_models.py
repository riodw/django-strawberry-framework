"""Script tests for the test-model census's name resolution.

``scripts/census_test_models.py`` decides whether a class is a model by
resolving its bases. A bare base name resolves lexically, by the class
declaration the enclosing scopes bind, so a same-named class in a sibling
function, or a plain class shadowing a model or an import, never borrows
another declaration's model-ness. The sources are synthetic strings; the
script measures the test tree, it is not reached by a query.
"""

import ast
import importlib
from pathlib import Path
from types import ModuleType

import pytest

from scripts import _bench_common

SCRIPTS = Path(_bench_common.__file__).resolve().parent


@pytest.fixture
def census(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Import ``scripts/census_test_models.py`` the way it runs: scripts dir on ``sys.path``."""
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("census_test_models")


SIBLING_SAME_NAME = """
def a():
    class Row(models.Model):
        pass

def b():
    class Row:
        pass
"""

SIBLING_BASES = """
def a():
    class Base(models.Model):
        pass

    class Child(Base):
        pass

def b():
    class Base:
        pass

    class Other(Base):
        pass
"""

LOCAL_CLASS_SHADOWS_IMPORT = """
from django.db.models import Model

def a():
    class Model:
        pass

    class Node(Model):
        pass
"""

INNER_PLAIN_SHADOWS_MODULE_MODEL = """
class Base(models.Model):
    pass

def a():
    class Base:
        pass

    class Other(Base):
        pass
"""

MODEL_CHAIN = """
class Base(models.Model):
    pass

class Child(Base):
    pass
"""

TOP_LEVEL_PLAIN_NESTED_MODEL = """
class Row:
    pass

def a():
    class Row(models.Model):
        pass
"""

IMPORT_SHADOWED_BY_OWN_CLASS = """
from django.db.models import Model

class Model(Model):
    pass
"""

SUBCLASS_BEFORE_REBINDING = """
class X(models.Model):
    pass

class Y(X):
    pass

class X:
    pass
"""

REBINDING_AFTER_USE_CHAIN = """
class X(models.Model):
    pass

class Y(X):
    pass

class X(Y):
    pass
"""

BASE_DECLARED_AFTER_USE = """
class Y(X):
    pass

class X(models.Model):
    pass
"""

METHOD_SKIPS_CLASS_SCOPE = """
class Base(models.Model):
    pass

class Container:
    class Base:
        pass

    def build(self):
        class Child(Base):
            pass
"""

METHOD_SEES_MODULE_NOT_CLASS_MODEL = """
class Base:
    pass

class Container:
    class Base(models.Model):
        pass

    def build(self):
        class Child(Base):
            pass
"""

CLASS_BODY_BASE_SEES_CLASS_BODY = """
class Base:
    pass

class Container:
    class Base(models.Model):
        pass

    class Child(Base):
        pass
"""

DOUBLY_NESTED_SKIPS_OUTER_CLASS = """
class Base(models.Model):
    pass

class A:
    class Base:
        pass

    class B:
        class C(Base):
            pass
"""

FUNCTION_SEES_FINAL_MODULE_BINDING = """
def f():
    class C(Base):
        pass

class Base(models.Model):
    pass
"""

TYPE_CALL_IN_METHOD_SKIPS_CLASS_SCOPE = """
class Base(models.Model):
    pass

class Container:
    class Base:
        pass

    def build(self):
        return type("Child", (Base,), {})
"""

TYPE_CALL_BEFORE_REBINDING = """
class Base(models.Model):
    pass

T = type("T", (Base,), {})

class Base:
    pass
"""

TYPE_CALL_BEFORE_DECLARATION = """
T = type("T", (Base,), {})

class Base(models.Model):
    pass
"""

HEADER_DEFAULT = """
class Container:
    class Base(models.Model):
        pass

    def make(self, k=type("Child", (Base,), {})):
        pass
"""

HEADER_KW_DEFAULT = """
class Container:
    class Base(models.Model):
        pass

    def make(self, *, k=type("Child", (Base,), {})):
        pass
"""

HEADER_DECORATOR = """
class Container:
    class Base(models.Model):
        pass

    @type("Child", (Base,), {})
    def make(self):
        pass
"""

CLASS_HEADER_BASES = """
class Container:
    class Base(models.Model):
        pass

    class Plain(type("Child", (Base,), {})):
        pass
"""

CLASS_HEADER_KEYWORDS = """
class Container:
    class Base(models.Model):
        pass

    class Plain(metaclass=type("Child", (Base,), {})):
        pass
"""

CLASS_HEADER_DECORATOR = """
class Container:
    class Base(models.Model):
        pass

    @type("Child", (Base,), {})
    class Plain:
        pass
"""

HEADER_SEES_CLASS_PLAIN_NOT_MODULE_MODEL = """
class Base(models.Model):
    pass

class Container:
    class Base:
        pass

    def make(self, k=type("Child", (Base,), {})):
        pass
"""

FACTORY_BEFORE_REBINDING_SEES_FINAL = """
class Base(models.Model):
    pass

def f():
    class Child(Base):
        pass

f()

class Base:
    pass
"""


@pytest.mark.parametrize(
    ("source", "models", "top_level"),
    [
        pytest.param(SIBLING_SAME_NAME, ["Row"], set(), id="sibling-same-name"),
        pytest.param(SIBLING_BASES, ["Base", "Child"], set(), id="sibling-bases"),
        pytest.param(LOCAL_CLASS_SHADOWS_IMPORT, [], set(), id="local-class-shadows-import"),
        pytest.param(
            INNER_PLAIN_SHADOWS_MODULE_MODEL,
            ["Base"],
            {"Base"},
            id="inner-plain-shadows-module-model",
        ),
        pytest.param(MODEL_CHAIN, ["Base", "Child"], {"Base", "Child"}, id="model-chain"),
        pytest.param(
            TOP_LEVEL_PLAIN_NESTED_MODEL,
            ["Row"],
            set(),
            id="top-level-plain-nested-model",
        ),
        pytest.param(
            IMPORT_SHADOWED_BY_OWN_CLASS,
            ["Model"],
            {"Model"},
            id="import-shadowed-by-own-class",
        ),
        pytest.param(
            SUBCLASS_BEFORE_REBINDING,
            ["X", "Y"],
            {"Y"},
            id="subclass-before-rebinding",
        ),
        pytest.param(
            REBINDING_AFTER_USE_CHAIN,
            ["X", "Y", "X"],
            {"X", "Y"},
            id="rebinding-after-use-chain",
        ),
        pytest.param(BASE_DECLARED_AFTER_USE, ["X"], {"X"}, id="base-declared-after-use"),
        pytest.param(
            METHOD_SKIPS_CLASS_SCOPE,
            ["Base", "Child"],
            {"Base"},
            id="method-skips-class-scope",
        ),
        pytest.param(
            METHOD_SEES_MODULE_NOT_CLASS_MODEL,
            ["Base"],
            set(),
            id="method-sees-module-not-class-model",
        ),
        pytest.param(
            CLASS_BODY_BASE_SEES_CLASS_BODY,
            ["Base", "Child"],
            set(),
            id="class-body-base-sees-class-body",
        ),
        pytest.param(
            DOUBLY_NESTED_SKIPS_OUTER_CLASS,
            ["Base", "C"],
            {"Base"},
            id="doubly-nested-skips-outer-class",
        ),
        pytest.param(
            FUNCTION_SEES_FINAL_MODULE_BINDING,
            ["Base", "C"],
            {"Base"},
            id="function-sees-final-module-binding",
        ),
        pytest.param(
            TYPE_CALL_IN_METHOD_SKIPS_CLASS_SCOPE,
            ["Base", "Child"],
            {"Base"},
            id="type-call-in-method-skips-class-scope",
        ),
        pytest.param(
            TYPE_CALL_BEFORE_REBINDING,
            ["Base", "T"],
            set(),
            id="type-call-before-rebinding",
        ),
        pytest.param(
            TYPE_CALL_BEFORE_DECLARATION,
            ["Base"],
            {"Base"},
            id="type-call-before-declaration",
        ),
        pytest.param(HEADER_DEFAULT, ["Base", "Child"], set(), id="header-default"),
        pytest.param(HEADER_KW_DEFAULT, ["Base", "Child"], set(), id="header-kw-default"),
        pytest.param(HEADER_DECORATOR, ["Base", "Child"], set(), id="header-decorator"),
        pytest.param(CLASS_HEADER_BASES, ["Base", "Child"], set(), id="class-header-bases"),
        pytest.param(CLASS_HEADER_KEYWORDS, ["Base", "Child"], set(), id="class-header-keywords"),
        pytest.param(
            CLASS_HEADER_DECORATOR,
            ["Base", "Child"],
            set(),
            id="class-header-decorator",
        ),
        pytest.param(
            HEADER_SEES_CLASS_PLAIN_NOT_MODULE_MODEL,
            ["Base"],
            {"Base"},
            id="header-sees-class-plain-not-module-model",
        ),
        pytest.param(
            FACTORY_BEFORE_REBINDING_SEES_FINAL,
            ["Base"],
            set(),
            id="factory-before-rebinding-sees-final",
        ),
    ],
)
def test_bare_base_names_resolve_by_enclosing_scope(
    census: ModuleType,
    source: str,
    models: list[str],
    top_level: set[str],
):
    """Each class's bases resolve against its own scope chain, never another scope's class."""
    tree = ast.parse("from django.db import models\n" + source)
    found, top = census._census_tree(tree, None)
    assert [census.model_name(node) for node in found] == models
    assert top == top_level
