import inspect
from unittest import mock

import typer

from typer_di import Depends
from typer_di._create_di_wrapper import create_di_wrapper

_SIG_EMPTY = inspect.Signature.empty


def test_call_original_method():
    m = mock.Mock(return_value=42)

    def func(x, y):
        return m(x, y)

    wrapper = create_di_wrapper(func)

    r = wrapper(1, 2)
    m.assert_called_once_with(1, 2)
    assert r == 42


def test_restore_signature():
    def func(x: int, y=17, z: str = "abc") -> dict:
        ...

    wrapper = create_di_wrapper(func)

    sig = inspect.signature(wrapper)
    assert wrapper.__name__ == func.__name__
    assert wrapper.__qualname__ == func.__qualname__

    assert sig.return_annotation == dict

    assert set(sig.parameters) == set("xyz")
    assert sig.parameters["x"].annotation == int
    assert sig.parameters["x"].default is _SIG_EMPTY
    assert sig.parameters["y"].annotation is _SIG_EMPTY
    assert sig.parameters["y"].default == 17
    assert sig.parameters["z"].annotation == str
    assert sig.parameters["z"].default == "abc"


def test_propagate_typer_params():
    def dep(x=typer.Option(42, "-x")):
        ...

    def command(x: int, y=typer.Option("test", "-y"), d=Depends(dep)) -> float:
        ...

    wrapper = create_di_wrapper(command)
    sig = inspect.signature(wrapper)

    # check untouched other vars
    assert sig.parameters["x"].annotation == int
    assert sig.parameters["y"].default.default == "test"
    assert sig.parameters["y"].default.param_decls == ("-y",)

    # `d` must be replaced by its vars
    assert "d" not in sig.parameters
    assert sig.parameters["d__x"].default.default == 42
    assert sig.parameters["d__x"].default.param_decls == ("-x",)


def test_call_dependency_callback():
    dep_mock = mock.Mock(return_value=42)
    command_mock = mock.Mock()

    def dep():
        return dep_mock()

    def command(d=Depends(dep)):
        command_mock(d=d)

    wrapper = create_di_wrapper(command)
    wrapper()

    # invoke callback
    dep_mock.assert_called_once_with()

    # pass its result to the command
    command_mock.assert_called_once_with(d=42)


# TODO: require dependency method must have only a) annotated vars, b) other deps
# TODO: deny varargs and kwargs in callbacks

# TODO: topological sort for dependencies
# TODO: test callback inside callback
# TODO: don't call callbacks twice (don't collect corresponding annotations twice!)

# TODO: TBD: replace wrapped signatures by `Signature.empty` instead of `Depends`
