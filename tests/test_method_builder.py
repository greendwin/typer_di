from inspect import signature
from unittest import mock

import pytest

from typer_di import MethodBuilder, copy_func_attrs


@pytest.fixture
def builder() -> MethodBuilder:
    return MethodBuilder()


def test_create_empty(builder: MethodBuilder):
    wr = builder.build()
    assert wr.__name__ == "func"  # just some name
    assert wr() is None  # empty body
    assert str(signature(wr)) == "()"


def test_copy_func_attrs(builder: MethodBuilder):
    def foo():
        pass

    wr = builder.build()

    copy_func_attrs(wr, foo)
    assert wr.__name__ == foo.__name__
    assert wr.__qualname__ == foo.__qualname__
    assert wr.__module__ == foo.__module__


def test_copy_func_attrs_dont_break_signature(builder: MethodBuilder):
    def foo():
        pass

    builder.add_param("x")
    builder.add_param("y")
    wr = builder.build()

    copy_func_attrs(wr, foo)

    assert str(signature(wr)) == "(x, y)"


def test_setup_parameters(builder: MethodBuilder):
    builder.add_param("a", int, default=42)
    wr = builder.build()
    assert str(signature(wr)) == "(a: int = 42)"


def test_invoke_callbacks(builder: MethodBuilder):
    callback = mock.Mock()
    builder.add_param("x")
    builder.invoke(callback, kwargs={"a": "x", "b": "x"})
    wrapper = builder.build()

    wrapper(42)

    callback.assert_called_once_with(a=42, b=42)


def test_return_last_result(builder: MethodBuilder):
    first = mock.Mock(return_value=10)
    second = mock.Mock(return_value=20)
    last = mock.Mock(return_value=30)
    builder.invoke(first, {})
    builder.invoke(second, {})
    builder.invoke(last, {})
    wrapper = builder.build()

    result = wrapper()

    # all callbacks must be invoked
    first.assert_called_once_with()
    second.assert_called_once_with()
    last.assert_called_once_with()

    # return last result
    assert result == 30


def test_setup_return_type(builder: MethodBuilder):
    def ret_int() -> int:
        ...

    builder.invoke(ret_int, {})
    wrapper = builder.build()

    assert str(signature(wrapper)) == "() -> int"


def test_complex_chain(builder: MethodBuilder):
    def add(x, y):
        return x + y

    def mul(x, y):
        return x * y

    for name in "abc":
        builder.add_param(name)

    # implement (a + b) * (a + c) + b
    r1 = builder.invoke(add, {"x": "a", "y": "b"})
    r2 = builder.invoke(add, {"x": "a", "y": "c"})
    r3 = builder.invoke(mul, {"x": r1, "y": r2})
    builder.invoke(add, {"x": r3, "y": "b"})

    wrapper = builder.build()

    # (1+2)*(1+3)+2 = 3*4+2 = 14
    assert wrapper(1, 2, 3) == 14
