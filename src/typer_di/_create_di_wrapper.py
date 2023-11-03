from dataclasses import dataclass, field
from inspect import Parameter, Signature, signature

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
    _sort_params(ctx)
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

    if func in ctx.known_invokes:
        # don't call the same dependency callback twice
        return ctx.known_invokes[func]

    result = ctx.builder.invoke(func, kwargs)
    ctx.known_invokes[func] = result
    return result


def _parse_dependency(param: Parameter) -> DependsType | None:
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
