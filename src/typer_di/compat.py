import inspect
import sys
from typing import Any, Callable

if sys.version_info >= (3, 9):
    from typing import Annotated as Annotated
else:  # pragma: no cover
    from typing_extensions import Annotated as Annotated

if sys.version_info >= (3, 10):
    from typing import TypeAlias as TypeAlias
else:  # pragma: no cover
    from typing_extensions import TypeAlias as TypeAlias


if sys.version_info >= (3, 10):

    def signature(
        func: Callable[..., Any], eval_str: bool = False
    ) -> inspect.Signature:
        return inspect.signature(func, eval_str=eval_str)

else:  # pragma: no cover
    # just don't eval annotations on lower versions
    def signature(
        func: Callable[..., Any], eval_str: bool = False
    ) -> inspect.Signature:
        sig = inspect.signature(func)

        if not eval_str:
            return sig

        def eval_if_str(obj: Any) -> Any:
            if not isinstance(obj, str):
                return obj
            return eval(obj, sys.modules[func.__module__].__dict__)

        return sig.replace(
            parameters=[
                p.replace(annotation=eval_if_str(p.annotation))
                for p in sig.parameters.values()
            ],
            return_annotation=eval_if_str(sig.return_annotation),
        )
