import inspect
from functools import WRAPPER_ASSIGNMENTS
from inspect import Parameter, Signature
from itertools import chain
from typing import NamedTuple, cast

from ._depends import Callback, DependsType

_TEMPLATE = """\
def wrapper({vars}):
    {di_calls}
    return __func({func_args})
"""


class _Dep(NamedTuple):
    name: str
    callback: Callback
    params: dict[str, str]  # orign - renamed


class _RecursiveSignature(NamedTuple):
    orig_params: list[Parameter]  # original command params
    dep_params: list[Parameter]  # new params from recursive traversal
    deps: list[_Dep]  # dependencies


def _collect_params_recursive(
    sig: Signature,
) -> _RecursiveSignature:
    orig_params: list[Parameter] = []
    dep_params: list[Parameter] = []
    deps: list[_Dep] = []
    for p in sig.parameters.values():
        if isinstance(p.default, DependsType):
            _collect_deps_to(p.name, p.default.callback, dep_params, deps)
            continue

        orig_params.append(p)

    return _RecursiveSignature(orig_params, dep_params, deps)


def _collect_deps_to(
    name: str, callback: Callback, out_params: list[Parameter], out_deps: list[_Dep]
):
    sig = inspect.signature(callback)

    dep_params: dict[str, str] = {}
    dep = _Dep(name, callback, dep_params)
    out_deps.append(dep)

    for p in sig.parameters.values():
        if isinstance(p.default, DependsType):
            _collect_deps_to(p.name, p.default.callback, out_params, out_deps)
            continue

        renamed = f"{name}__{p.name}"
        dep_params[p.name] = renamed
        out_params.append(p.replace(name=renamed))


def create_di_wrapper(func: Callback) -> Callback:
    sig = inspect.signature(func)
    orig_params, dep_params, deps = _collect_params_recursive(sig)
    all_params = orig_params + dep_params

    globs = {
        "__func": func,
        **{f"__dep__{idx}": d.callback for idx, d in enumerate(deps)},
    }

    dep_invoke_args = [
        ", ".join(f"{orig}={renamed}" for orig, renamed in d.params.items())
        for d in deps
    ]

    func_text = _TEMPLATE.format(
        vars=", ".join(p.name for p in all_params),
        di_calls="; ".join(
            f"{d.name}=__dep__{idx}({args})"
            for idx, (d, args) in enumerate(zip(deps, dep_invoke_args))
        ),
        func_args=", ".join(
            chain(
                (f"{p.name}={p.name}" for p in orig_params),
                (f"{d.name}={d.name}" for d in deps),
            )
        ),
    )

    exec(
        func_text,
        globs,
    )
    wrapper = globs["wrapper"]

    assigned = set(WRAPPER_ASSIGNMENTS)
    assigned.remove("__annotations__")
    for name in assigned:
        setattr(wrapper, name, getattr(func, name))

    # setup wrapper signature
    wrapper.__signature__ = Signature(
        all_params,
        return_annotation=sig.return_annotation,
    )

    return cast(Callback, wrapper)
