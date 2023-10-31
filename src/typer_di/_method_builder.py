from dataclasses import dataclass
from functools import WRAPPER_ASSIGNMENTS
from inspect import Parameter, Signature, _ParameterKind, signature
from typing import Any

from ._depends import Callback

__all__ = [
    "MethodBuilder",
    "MethodBuilderError",
    "copy_func_attrs",
]


class MethodBuilderError(Exception):
    pass


@dataclass
class InvokeInfo:
    callback: Callback
    kwargs: dict[str, str]  # arguments `k=v` that will be passed to the callback
    result: str  # variable that holds invocation result


_METHOD_TEMPLATE = """\
def func({vars}):
{invokes}
{result}
"""

_INVOKE_TEMPLATE = """\
    {result} = {callback}({args})
"""

_RESULT_TEMPLATE = """\
    return {result}
"""


class MethodBuilder:
    """
    Construct wrapper method in form

    def func({params}):
        {invokes}   # x = foo(y, z)
        return {final_invoke}

    This allows us to bake whole dependency tree to a single function.

    Builder preserves:
     * params type annotations
     * return type annotation and other `wraps` props from `func`
    """

    def __init__(self):
        self._params: list[Parameter] = []
        self._invokes: list[InvokeInfo] = []

    @property
    def params(self) -> list[Parameter]:
        return self._params

    def add_param(
        self,
        name: str,
        annotation: type = Signature.empty,
        *,
        default: Any = Signature.empty,
        kind: _ParameterKind = Parameter.POSITIONAL_OR_KEYWORD,
    ):
        self._params.append(
            Parameter(
                name,
                kind,
                default=default,
                annotation=annotation,
            )
        )

    def invoke(self, callback: Callback, kwargs: dict[str, str]) -> str:
        # TODO: validate that `kwargs.values()` are either in `params` or `calls.result`s
        result = f"__r{len(self._invokes)}"
        self._invokes.append(InvokeInfo(callback, kwargs, result))
        return result

    def build(self) -> Callback:
        program_text = self._format_func_program()
        globs = {f"__cb{idx}": p.callback for idx, p in enumerate(self._invokes)}

        try:
            exec(program_text, globs)
        except Exception as ex:
            raise MethodBuilderError(
                f"Compilation failed: {ex}\nProgram text:\n{program_text}"
            )

        func = globs["func"]
        self._update_signature(func)
        return func

    def _format_func_program(self) -> str:
        invokes = []
        for idx, invoke_info in enumerate(self._invokes):
            invokes.append(
                _INVOKE_TEMPLATE.format(
                    result=invoke_info.result,
                    callback=f"__cb{idx}",
                    args=", ".join(f"{k}={v}" for k, v in invoke_info.kwargs.items()),
                )
            )

        if self._invokes:
            # use result of last invokation
            result = _RESULT_TEMPLATE.format(result=self._invokes[-1].result)
        else:
            result = _RESULT_TEMPLATE.format(result="")

        return _METHOD_TEMPLATE.format(
            vars=", ".join(p.name for p in self._params),
            invokes="".join(invokes),
            result=result,
        )

    def _update_signature(self, func: Callback):
        # take return type from the signature of the last callback
        return_type = Signature.empty
        if self._invokes:
            last_sig = signature(self._invokes[-1].callback)
            return_type = last_sig.return_annotation

        # setup wrapper signature
        func.__signature__ = Signature(
            self._params,
            return_annotation=return_type,
        )


def copy_func_attrs(wrapper: Callback, func: Callback):
    # update all except `__annotations__`, to avoid overriding signature
    assigned = set(WRAPPER_ASSIGNMENTS)
    assigned.remove("__annotations__")

    for name in assigned:
        setattr(wrapper, name, getattr(func, name))
