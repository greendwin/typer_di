from inspect import Signature, signature
from unittest import mock

import pytest
import typer

from typer_di import Depends, TyperDIError, create_di_wrapper


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

    sig = signature(wrapper)
    assert wrapper.__name__ == func.__name__
    assert wrapper.__qualname__ == func.__qualname__

    assert sig.return_annotation == dict

    assert set(sig.parameters) == set("xyz")
    assert sig.parameters["x"].annotation == int
    assert sig.parameters["x"].default == Signature.empty
    assert sig.parameters["y"].annotation == Signature.empty
    assert sig.parameters["y"].default == 17
    assert sig.parameters["z"].annotation == str
    assert sig.parameters["z"].default == "abc"


def test_propagate_typer_params():
    def dep(z=typer.Option(42, "-z")):
        ...

    def command(x: int, y=typer.Option("test", "-y"), d=Depends(dep)) -> float:
        ...

    wrapper = create_di_wrapper(command)
    params = signature(wrapper).parameters

    # check untouched other vars
    assert params["x"].annotation == int
    assert params["y"].default.default == "test"
    assert params["y"].default.param_decls == ("-y",)

    # `d` must be replaced by its vars
    assert "d" not in params
    assert params["z"].default.default == 42
    assert params["z"].default.param_decls == ("-z",)


def test_call_dependency_callback():
    dep_mock = mock.Mock(name="dep", return_value=42)
    command_mock = mock.Mock(name="command")

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


def test_error_on_conflicting_names():
    def dep(x=typer.Option(42, "-x")):
        return x + 1

    def command(x: str, d=Depends(dep)):
        return f"{x=} {d=}"

    with pytest.raises(TyperDIError, match="Duplicated parameter name 'x'"):
        _ = create_di_wrapper(command)


# DONE: what we do on duplicated variables?
# DONE: typer annotations can be without providing actual option names, we must preserve names in this case

# DONE: handle conflicting duplicated names
# [x] *NO* rename parameters that has `params_decl` in corresponding `typer.ParamInfo`
# [x] better error reports on duplicated names

# TODO: recursive traversal can break parameters order required by Python
#       (e.g.: args with defaults can't go before args without defaults)

# TODO: deny varargs and kwargs in callbacks
# TODO: don't call callbacks twice (don't collect corresponding annotations twice!)

# TBD: replace wrapped signatures by `Signature.empty` instead of `Depends`
