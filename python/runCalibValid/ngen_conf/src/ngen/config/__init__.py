from ._version import __version__

# Monkey patch some types required to support python 3.7
try:
    from typing import Literal
except ImportError:
    import typing
    from typing_extensions import Literal
    typing.Literal = Literal