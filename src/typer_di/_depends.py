from typing import TYPE_CHECKING, Any, Callable, TypeVar

from ._compat import TypeAlias

__all__ = [
    "Depends",
    "DependsType",
]


Callback: TypeAlias = Callable[..., Any]


class DependsType:
    def __init__(self, callback: Callback) -> None:
        self.callback = callback


if TYPE_CHECKING:
    _T = TypeVar("_T")

    def Depends(func: Callable[..., _T]) -> _T:
        ...

else:

    def Depends(func: Callback):
        return DependsType(func)  # type: ignore
