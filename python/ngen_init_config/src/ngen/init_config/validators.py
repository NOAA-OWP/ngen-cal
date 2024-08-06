from __future__ import annotations

from typing import Callable


def str_split(sep: str, *, strip: bool = False) -> Callable[[str], list[str]]:
    def inner(items: str) -> list[str]:
        split_items = items.split(sep)
        if strip:
            for idx, item in enumerate(split_items):
                split_items[idx] = item.strip()
        return split_items

    return inner
