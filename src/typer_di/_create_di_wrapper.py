import inspect
from dataclasses import dataclass, field

from ._depends import Callback, DependsType
from ._method_builder import MethodBuilder, copy_func_attrs

__all__ = [
    "create_di_wrapper",
    "TyperDIError",
]


class TyperDIError(Exception):
    pass


def create_di_wrapper(func: Callback) -> Callback:
    ctx = _Context()
    _invoke_recursive(ctx, func)
    wrapper = ctx.builder.build()
    copy_func_attrs(wrapper, func)
    return wrapper


@dataclass
class _Context:
    builder: MethodBuilder = field(default_factory=MethodBuilder)
    known_invokes: dict[Callback, str] = field(default_factory=dict)


def _invoke_recursive(ctx: _Context, func: Callback) -> str:
    """
    Invoke `func` recursively and return the name of the result variable.
    """
    sig = inspect.signature(func)

    kwargs = {}

    for param in sig.parameters.values():
        arg_name = param.name
        if isinstance(param.default, DependsType):
            kwargs[arg_name] = _invoke_recursive(ctx, param.default.callback)
            continue

        # make sure that all name are unique
        if any(param.name == p.name for p in ctx.builder.params):
            raise TyperDIError(
                f"Duplicated parameter name '{param.name}'.\n"
                f"Please, make sure to have unique names in the whole dependency tree."
            )

        # add param to wrapper
        ctx.builder.add_param(
            param.name,
            param.annotation,
            default=param.default,
        )
        kwargs[arg_name] = param.name

    if func in ctx.known_invokes:
        # don't call the same dependency callback twice
        return ctx.known_invokes[func]

    result = ctx.builder.invoke(func, kwargs)
    ctx.known_invokes[func] = result
    return result
