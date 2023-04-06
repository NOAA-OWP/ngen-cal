from typing import Protocol, Callable


class IntoStr(Protocol):
    def __str__(self) -> str:
        ...


def validate_str_len_lt(n: int) -> Callable[[IntoStr], IntoStr]:
    """
    Return a reusable validator that asserts a type castable into `str` is strictly less than some
    length `n`.

    Example:
        ```python
        from pydantic import BaseModel, validator

        class Foo(BaseModel):
            foo: Path

            _validate_path_len = validator("foo", pre=True, allow_reuse=True)(
                validate_str_len(20)
            )
        ```
    """

    def validate(s: IntoStr) -> IntoStr:
        assert len(str(s)) < n
        return s

    return validate
