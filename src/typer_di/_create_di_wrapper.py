from dataclasses import dataclass, field
from inspect import Parameter, Signature
from typing import Dict, Optional, Union

from ._depends import Callback, DependsType
from ._method_builder import MethodBuilder, copy_func_attrs
from .compat import signature

__all__ = [
    "create_di_wrapper",
    "TyperDIError",
]


class TyperDIError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def create_di_wrapper(func: Callback) -> Callback:
    ctx = _Context()
    _invoke_recursive(ctx, func)
    _sort_params(ctx)
    wrapper = ctx.builder.build()
    copy_func_attrs(wrapper, func)
    return wrapper


@dataclass
class _Context:
    builder: MethodBuilder = field(default_factory=MethodBuilder)
    known_invokes: Dict[Callback, Union[str, None]] = field(default_factory=dict)


def _invoke_recursive(ctx: _Context, func: Callback) -> str:
    """
    Invoke `func` recursively and return the name of the result variable.
    """
    # don't call the same dependency callback twice
    if func in ctx.known_invokes:
        result = ctx.known_invokes[func]
        if result is None:
            # cycle found
            raise TyperDIError(
                f'Found cycle in dependency graph around method "{func.__qualname__}"'
            )

        return result

    ctx.known_invokes[func] = None  # mark this dependency as being processed

    sig = signature(func, eval_str=True)

    kwargs = {}

    for param in sig.parameters.values():
        arg_name = param.name
        depends_type = _parse_dependency(param)
        if depends_type is not None:
            kwargs[arg_name] = _invoke_recursive(ctx, depends_type.callback)
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

    result = ctx.builder.invoke(func, kwargs)
    ctx.known_invokes[func] = result
    return result


def _parse_dependency(param: Parameter) -> Optional[DependsType]:
    if isinstance(param.default, DependsType):
        return param.default

    metadata = getattr(param.annotation, "__metadata__", ())
    for p in metadata:
        if isinstance(p, DependsType):
            return p

    return None


def _sort_params(ctx: _Context) -> None:
    # move params with defaults to the end
    ctx.builder.params.sort(
        key=lambda p: p.default != Signature.empty,
    )
