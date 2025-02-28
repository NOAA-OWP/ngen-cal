from __future__ import annotations

from ngen.config_gen._class_var_iter import (
    ClassVarIter,
    pub_cls_vars,
)


class Foo(metaclass=ClassVarIter[int | bool]):
    bar: int = 1
    baz: bool = True

    def quox(self) -> None: ...
    @classmethod
    def klass(cls) -> None: ...
    @property
    def prop(self) -> None: ...


def test_metaclass_var_collection():
    assert {name: value for name, value in Foo} == {"bar": 1, "baz": True}
    assert Foo.bar == 1


def test_pub_cls_vars():
    assert {name: value for name, value in pub_cls_vars(Foo)} == {"bar": 1, "baz": True}
