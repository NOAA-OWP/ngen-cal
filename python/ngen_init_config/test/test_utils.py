import pytest
from typing import Dict, List, Set, Tuple, Type, Union

from ngen.init_config.utils import get_attr, merge_class_attr, try_import


class Base:
    ...


class A_List(Base):
    class I:
        field: List[int] = [1, 2, 3]


class B_List_List(A_List):
    class I:  # type: ignore
        field: List[int] = [4, 5, 6]


class C_List_Tuple(A_List):
    class I:  # type: ignore
        field = (1, 2, 3)


class D_List_Dict(A_List):
    class I:  # type: ignore
        field = {1: 2, 3: 4}


class E_List_Set(A_List):
    class I:  # type: ignore
        field = {1, 2, 3}


class F_List_Str(A_List):
    class I:  # type: ignore
        field = "value"


class G_List_Just_Child(A_List):
    ...


class H_List_Explicit_Empty(A_List):
    class I:  # type: ignore
        field = []


class A_Dict(Base):
    class I:
        field: Dict[int, int] = {1: 2, 3: 4}


class B_Dict_List(A_Dict):
    class I:  # type: ignore
        field: List[int] = [4, 5, 6]


class C_Dict_Tuple(A_Dict):
    class I:  # type: ignore
        field = (1, 2, 3)


class D_Dict_Dict(A_Dict):
    class I:  # type: ignore
        field = {5: 6}


class E_Dict_Set(A_Dict):
    class I:  # type: ignore
        field = {1, 2, 3}


class F_Dict_Str(A_List):
    class I:  # type: ignore
        field = "value"


class G_Dict_Just_Child(A_Dict):
    ...


class H_Dict_Explicit_Empty(A_Dict):
    class I:  # type: ignore
        field = {}


class A_Set(Base):
    class I:
        field: Set[int] = {1, 2, 3}


class B_Set_List(A_Set):
    class I:  # type: ignore
        field: List[int] = [4, 5, 6]


class C_Set_Tuple(A_Set):
    class I:  # type: ignore
        field = (1, 2, 3)


class D_Set_Dict(A_Set):
    class I:  # type: ignore
        field = {1: 2, 3: 4}


class E_Set_Set(A_Set):
    class I:  # type: ignore
        field = {4}


class F_Set_Str(A_List):
    class I:  # type: ignore
        field = "value"


class G_Set_Just_Child(A_Set):
    ...


class H_Set_Explicit_Empty(A_Set):
    class I:  # type: ignore
        field = set()


@pytest.mark.parametrize(
    "T, expected",
    [
        # list
        (A_List, [1, 2, 3]),
        (B_List_List, [4, 5, 6]),
        (C_List_Tuple, (1, 2, 3)),
        (D_List_Dict, {1: 2, 3: 4}),
        (E_List_Set, {1, 2, 3}),
        (F_List_Str, "value"),
        (G_List_Just_Child, [1, 2, 3]),
        (H_List_Explicit_Empty, []),
        # dict
        (A_Dict, {1: 2, 3: 4}),
        (B_Dict_List, [4, 5, 6]),
        (C_Dict_Tuple, (1, 2, 3)),
        (D_Dict_Dict, {5: 6}),
        (E_Dict_Set, {1, 2, 3}),
        (F_Dict_Str, "value"),
        (G_Dict_Just_Child, {1: 2, 3: 4}),
        (H_Dict_Explicit_Empty, {}),
        # set
        (A_Set, {1, 2, 3}),
        (B_Set_List, [4, 5, 6]),
        (C_Set_Tuple, (1, 2, 3)),
        (D_Set_Dict, {1: 2, 3: 4}),
        (E_Set_Set, {4}),
        (F_Set_Str, "value"),
        (G_Set_Just_Child, {1, 2, 3}),
        (H_Set_Explicit_Empty, set()),
    ],
)
def test_get_attr(
    T: Type[Base], expected: Union[List[int], Tuple[int], Dict[int, int], Set[int]]
):
    o = T()
    target = "I.field"
    assert get_attr(o, target) == expected


@pytest.mark.parametrize(
    "T, expected",
    [
        # list
        (A_List, [1, 2, 3]),
        (B_List_List, [1, 2, 3, 4, 5, 6]),
        (C_List_Tuple, (1, 2, 3)),
        (D_List_Dict, {1: 2, 3: 4}),
        (E_List_Set, {1, 2, 3}),
        (F_List_Str, "value"),
        (G_List_Just_Child, [1, 2, 3]),
        (H_List_Explicit_Empty, []),
        # dict
        (A_Dict, {1: 2, 3: 4}),
        (B_Dict_List, [4, 5, 6]),
        (C_Dict_Tuple, (1, 2, 3)),
        (D_Dict_Dict, {1: 2, 3: 4, 5: 6}),
        (E_Dict_Set, {1, 2, 3}),
        (F_Dict_Str, "value"),
        (G_Dict_Just_Child, {1: 2, 3: 4}),
        (H_Dict_Explicit_Empty, {}),
        # set
        (A_Set, {1, 2, 3}),
        (B_Set_List, [4, 5, 6]),
        (C_Set_Tuple, (1, 2, 3)),
        (D_Set_Dict, {1: 2, 3: 4}),
        (E_Set_Set, {1, 2, 3, 4}),
        (F_Set_Str, "value"),
        (G_Set_Just_Child, {1, 2, 3}),
        (H_Set_Explicit_Empty, set()),
    ],
)
def test_get_class_attr(
    T: Type[Base], expected: Union[List[int], Tuple[int], Dict[int, int], Set[int]]
):
    target = "I.field"
    merged_class_attr = merge_class_attr(T, target)
    assert merged_class_attr == expected
    if not isinstance(expected, (tuple, str)):
        assert id(merge_class_attr(T, target)) != id(merged_class_attr)
        assert id(merge_class_attr(T, target)) != id(get_attr(T, target))


def test_try_import_imports_std_lib_mod():
    json = try_import("json", "json")
    data = json.loads('{"it": "works"}')
    assert data == {"it": "works"}


def test_try_import_throws_import_error():
    with pytest.raises(ImportError):
        try_import("some_fake_package", extras_require_name="fake")
