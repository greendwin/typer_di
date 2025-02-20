from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

import typer

from ._create_di_wrapper import create_di_wrapper

__all__ = ["TyperDI"]


class TyperDI(typer.Typer):
    # we only patch existing methods, so do it silently without affecting type checker

    if not TYPE_CHECKING:

        def __init__(self, *args, **kwargs):
            if "callback" in kwargs:
                kwargs["callback"] = create_di_wrapper(kwargs["callback"])
            super().__init__(*args, **kwargs)

        def callback(self, *args, **kwargs):
            decor = super().callback(*args, **kwargs)
            return wrap_typer_decorator(decor)

        def command(self, *args, **kwargs):
            decor = super().command(*args, **kwargs)
            return wrap_typer_decorator(decor)


def wrap_typer_decorator(decor: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(decor)
    def inner(func: Callable[..., Any]) -> Callable[..., Any]:
        # pass wrapper to the typer
        decor(create_di_wrapper(func))

        # return untouched func
        return func

    return inner
