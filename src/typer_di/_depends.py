from typing import TYPE_CHECKING, Any, Callable, TypeAlias, TypeVar

__all__ = [
    "Depends",
    "typer_di",
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


def typer_di(func: Callback) -> Callback:
    """
    TODO: generate stub function with signature containing all typer annotations
        inside `Depends` function (recursively)

    This method can looks like so:
    ```
    def get_dep(dep_var: Annotated[...]): ...

    @typer_di
    def command(var: Annotated[...], dep=Depends(get_dep)): ...

    def wrapped_command(
        var: Annotated[...],
        __dep__var: Annotated[...],
    ):
        __dep = get_dep(dep_var=__dep_var)
        return command(
            var=var,
            dep=__dep,
        )
    ```
    """

    return func
