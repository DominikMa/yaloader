---
jupytext:
    text_representation:
        format_name: myst
kernelspec:
    display_name: Python 3
    name: python3
---

Overview
=======================================

yaloader is a Python library for loading class instances from YAML configuration files.
It builds on [Pydantic v2](https://docs.pydantic.dev/) for validation and [PyYAML](https://pyyaml.org/) for parsing, adding:

- **Typed configuration classes** — define configs as Pydantic models, get validation and editor support for free.
- **Priority-based layering** — load configs from multiple files and merge them by priority. Base defaults in one file, environment overrides in another.
- **Configuration inheritance** — mirror your Python class hierarchy in YAML. A `ResNetConfig` that inherits from `ModelConfig` automatically inherits its fields.
- **Variable configs** — create named presets (like `!ConfigVarSmallResNet`) without writing new Python classes.
- **Cross-document anchors** — define YAML anchors in one document and reference them in another, even across multiple `load_string` calls.
- **Round-trip dumping** — serialize configs back to YAML with control over which fields are included.


Why yaloader?
---------------------------------------

Many projects end up with ad-hoc YAML loading: `yaml.safe_load()` into a dict, then manually passing values around.
This works for small projects but breaks down when you need:

- Validation that wrong types are caught early, not deep in your training loop.
- Layered configs where a base config is overridden per experiment, per environment, or per user.
- Inheritance where a family of related configs shares common fields.

yaloader gives you all of this with minimal boilerplate. You define a config class, decorate it, and load it from YAML — that's it for the simple case. The priority system and inheritance kick in when your project grows.


How it works
---------------------------------------

Using yaloader involves three steps:

1. **Define** a configuration class that inherits from `YAMLBaseConfig` and is decorated with `@yaloader.loads`.
2. **Load** YAML data into a `ConfigLoader` — from strings, files, or directories. Each source can have a priority.
3. **Construct** the final configuration by merging all loaded data and resolving inheritance.

```python
import yaloader

@yaloader.loads(MyClass)
class MyClassConfig(yaloader.YAMLBaseConfig):
    learning_rate: float = 0.001
    epochs: int = 10

loader = yaloader.ConfigLoader()
loader.load_file("base.yaml")       # priority defaults to 0
loader.load_file("overrides.yaml")  # can set higher priority

config = loader.construct_from_string("!MyClass {}")
obj = config.load()  # creates an instance of MyClass
```


Loading vs. Construction
---------------------------------------

yaloader separates two distinct phases:

**Loading** stores configuration data in the `ConfigLoader`. You can load from multiple sources, each with a priority.
Nothing is constructed yet — configs are just collected.

**Construction** takes a config reference (like `!MyClass {}`) and resolves it against all loaded data:
inherited fields, priority merging, and nested config construction all happen here.

This separation means you can load all your config files upfront, then construct individual objects on demand.
