from __future__ import annotations

import inspect
import types
import typing


def pub_cls_vars(cls: type) -> typing.Iterator[tuple[str, object]]:
    for name, value in inspect.getmembers(cls):
        # ignore methods, class methods, and properties
        if name.startswith("_") or isinstance(
            value, (types.FunctionType, types.MethodType, property)
        ):
            continue
        yield name, value


_T = typing.TypeVar("_T", bound=object)


class ClassVarIter(type, typing.Generic[_T]):
    """
    ClassVarIter is a metaclass that adds an __iter__ implementation that
    yields 'public' (no leading _) class variable names and their values.
    Function, property, and method values are not yielded.

    The Generic parameter _T is type of _values_ yielded by iterator.

    Example:
      class Foo(metaclass= ClassVarIter[int | bool]):
        bar: int = 1
        baz: bool = True

        def quox(self) -> None: ...

        @classmethod
        def klass(cls) -> None: ...

        @property
        def prop(self) -> None: ...

      assert {name: value for name, value in Foo} == {'bar': 1, 'baz': True}
    """

    def __iter__(cls) -> typing.Iterator[tuple[str, _T]]:
        """
        Iterate over 'public' (not leading _) class variables yielding their
        name and value.

        Example:
          class Foo(metaclass=ClassVarIter[int | bool]):
            bar: int = 1
            baz: bool = True

          for name, value in Foo: ...
        """
        yield from pub_cls_vars(cls)  # type: ignore
