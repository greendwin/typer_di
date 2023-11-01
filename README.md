Dependency injection for Typer
==============================

Add dependency injection functionality to [Typer](https://typer.tiangolo.com/) library. Implement the same DI behavior as in [FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/).


## Description

With `typer_di` you can easely move common parts of your commands to dependency functions.

Any dependency function can depends on other functions and etc. All args and options will be merged to interface of each command that uses corresponding dependencies.

`typer_di` ensures to call each dependency callback only *once*.


## Usage

Lets say you have a method that validates and parses a config:

```python
def get_config(config_path: Path) -> Config:
    ...
```

In case of multiple commands you need to duplicate annotation code:

```python
from typing import Annotated
from typer import Typer, Option

app = Typer()

@app.command()
def first(..., config_path: Annotated[Path, Option("--config")]):
    config = get_config(config_path)
    ...

@app.command()
def second(..., config_path: Annotated[Path, Option("--config")]):
    config = get_config(config_path)
    ...
```

With `typer_di` you can move annotations to parsing methods.

All you need is to use `Depends` annotation and replace the original `Typer` by `TyperDI` (it's a thin layer that transforms all passed functions unwrapping dependencies).

```python
from typing import Annotated
from typer_di import TyperDI, Option, Depends

app = TyperDI()

def get_config(config_path: Annotated[Path, Option("--config")]) -> Config:
    ...

@app.command()
def first(..., config: Config = Depends(get_config)]):
    ...

@app.command()
def second(..., config: Config = Depends(get_config)]):
    ...
```


## Roadmap

### MS-1
- [x] 📖 write detailed description with code examples
- [ ] 📁 push this repo to `github`
- [ ] 📁 push package to pypi (create tokens and etc., research it!)

### MS-2
- [ ] ✍️ include all `typer` declarations to `typer_di` (like in examples above)
- [ ] ✍️ support *future* `annotations`
- [ ] 🐞 dependency can be called multiple times in `callback` and `command`: we need to cache such calls through whole program execution

### MS-3
- [ ] ✍️ fix tests up to py3.8
