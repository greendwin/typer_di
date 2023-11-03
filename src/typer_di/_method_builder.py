from dataclasses import dataclass
from functools import WRAPPER_ASSIGNMENTS
from inspect import Parameter, Signature, signature
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
class ParamInfo:
    name: str
    default: Any = Signature.empty
    annotation: Any = Signature.empty

    def to_parameter(self) -> Parameter:
        return Parameter(
            self.name,
            Parameter.POSITIONAL_OR_KEYWORD,
            default=self.default,
            annotation=self.annotation,
        )


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

    def __init__(self) -> None:
        self._params: list[ParamInfo] = []
        self._invokes: list[InvokeInfo] = []

    @property
    def params(self) -> list[ParamInfo]:
        return self._params

    def add_param(
        self,
        name: str,
        annotation: type = Signature.empty,
        default: Any = Signature.empty,
    ) -> None:
        self._params.append(
            ParamInfo(name=name, default=default, annotation=annotation)
        )

    def invoke(self, callback: Callback, kwargs: dict[str, str]) -> str:
        # FIXME: validate that `kwargs.values()` are either in `params` or `calls.result`s
        result = f"__r{len(self._invokes)}"
        self._invokes.append(InvokeInfo(callback, kwargs, result))
        return result

    def build(self) -> Callback:
        program_text = self._format_func_program()
        globs = {f"__cb{idx}": p.callback for idx, p in enumerate(self._invokes)}

        try:
            exec(program_text, globs)
        except Exception as ex:
            raise MethodBuilderError(f"Compilation failed: {ex}\n\n{program_text}")

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
            invokes="".join(invokes).rstrip(),
            result=result,
        )

    def _update_signature(self, func: Callback) -> None:
        # take return type from the signature of the last callback
        return_type = Signature.empty
        if self._invokes:
            last_sig = signature(self._invokes[-1].callback, eval_str=True)
            return_type = last_sig.return_annotation

        # setup wrapper signature
        func.__signature__ = Signature(  # type: ignore
            [p.to_parameter() for p in self._params],
            return_annotation=return_type,
        )

        # setup defaults
        func.__defaults__ = tuple(
            param.default
            for param in self._params
            if param.default is not Signature.empty
        )


def copy_func_attrs(wrapper: Callback, func: Callback) -> None:
    # update all except `__annotations__`, to avoid overriding signature
    assigned = set(WRAPPER_ASSIGNMENTS)
    assigned.remove("__annotations__")

    for name in assigned:
        setattr(wrapper, name, getattr(func, name))
