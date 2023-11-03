from typing import List
from unittest import mock

import pytest
import typer
from typer.testing import CliRunner

from tests.helpers import assert_words_in_message
from typer_di import Depends, TyperDI
from typer_di.compat import Annotated


class TestAssignDepends:
    @pytest.fixture
    def command_mock(self) -> mock.Mock:
        return mock.Mock(name="command_mock")

    @pytest.fixture
    def app(self, command_mock: mock.Mock) -> TyperDI:
        app = TyperDI()

        def get_config(x=typer.Option(None, "--config")):
            # do some work, e.g. wrap to list
            return [x]

        @app.command()
        def command(cfg=Depends(get_config)):
            command_mock(cfg=cfg)

        return app

    def test_show_option_in_help(self, app: TyperDI):
        r = CliRunner().invoke(app, "--help")

        assert r.exit_code == 0
        assert_words_in_message("--config TEXT", r.output, require_same_line=True)

    def test_run_deps_and_pass_args(self, app: TyperDI, command_mock: mock.Mock):
        r = CliRunner().invoke(app, "--config test/path")

        assert r.exit_code == 0
        command_mock.assert_called_once_with(cfg=["test/path"])


class TestAnnotationDepends:
    @pytest.fixture
    def command_mock(self) -> mock.Mock:
        return mock.Mock(name="command_mock")

    @pytest.fixture
    def app(self, command_mock: mock.Mock) -> TyperDI:
        app = TyperDI()

        def get_config(x: Annotated[str, typer.Option("--config")]):
            # do some work, e.g. wrap to list
            return [x]

        @app.command()
        def command(cfg: Annotated[List[str], Depends(get_config)]):
            command_mock(cfg=cfg)

        return app

    def test_show_option_in_help(self, app: TyperDI):
        r = CliRunner().invoke(app, "--help")

        assert r.exit_code == 0
        assert_words_in_message("--config TEXT", r.output, require_same_line=True)

    def test_run_deps_and_pass_args(self, app: TyperDI, command_mock: mock.Mock):
        r = CliRunner().invoke(app, "--config test/path")

        assert r.exit_code == 0
        command_mock.assert_called_once_with(cfg=["test/path"])


class TestTyperCallbacks:
    @pytest.fixture
    def my_callback_mock(self) -> mock.Mock:
        return mock.Mock(name="my_callback_mock")

    @pytest.fixture
    def app(self, my_callback_mock: mock.Mock) -> TyperDI:
        app = TyperDI()

        def get_config(x: Annotated[str, typer.Option("--config")]):
            # do some work, e.g. wrap to list
            return [x]

        @app.command("hello")
        def cmd_hello():
            pass

        @app.callback()
        def my_callback(cfg=Depends(get_config)):
            my_callback_mock(cfg=cfg)

        return app

    def test_show_option_in_help(self, app: TyperDI):
        r = CliRunner().invoke(app, "--help")

        assert r.exit_code == 0
        assert_words_in_message("--config TEXT", r.output, require_same_line=True)

    def test_run_deps_and_pass_args(self, app: TyperDI, my_callback_mock: mock.Mock):
        r = CliRunner().invoke(app, "--config test/path hello")

        assert r.exit_code == 0
        my_callback_mock.assert_called_once_with(cfg=["test/path"])


class TestTyperCallbacksInConstructor:
    @pytest.fixture
    def my_callback_mock(self) -> mock.Mock:
        return mock.Mock(name="my_callback_mock")

    @pytest.fixture
    def app(self, my_callback_mock: mock.Mock) -> TyperDI:
        def get_config(x: Annotated[str, typer.Option("--config")]):
            # do some work, e.g. wrap to list
            return [x]

        def my_callback(cfg=Depends(get_config)):
            my_callback_mock(cfg=cfg)

        app = TyperDI(callback=my_callback)

        @app.command("hello")
        def cmd_hello():
            pass

        return app

    def test_show_option_in_help(self, app: TyperDI):
        r = CliRunner().invoke(app, "--help")

        assert r.exit_code == 0
        assert_words_in_message("--config TEXT", r.output, require_same_line=True)

    def test_run_deps_and_pass_args(self, app: TyperDI, my_callback_mock: mock.Mock):
        r = CliRunner().invoke(app, "--config test/path hello")

        assert r.exit_code == 0
        my_callback_mock.assert_called_once_with(cfg=["test/path"])
