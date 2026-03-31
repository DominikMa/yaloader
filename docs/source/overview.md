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

In machine learning projects, configuration drives everything — model architecture, optimizer choice, data pipeline, training schedule.
A single typo in a config can waste hours of GPU time.
yaloader lets you define these configurations as typed Python classes and load them from YAML, with full validation, layered merging, and object instantiation built in.

yaloader is a Python library for loading class instances from YAML configuration files.
It builds on [Pydantic v2](https://docs.pydantic.dev/) for validation and [PyYAML](https://pyyaml.org/) for parsing, adding:

- **Typed configuration classes** — define configs as Pydantic models, get validation and editor support for free.
- **Priority-based layering** — load configs from multiple files and merge them by priority. Base defaults in one file, experiment overrides in another.
- **Configuration inheritance** — mirror your Python class hierarchy in YAML. A `ResNetConfig` that inherits from `ModelConfig` automatically inherits its fields.
- **Variable configs** — create named presets (like `!ConfigVarSmallResNet`) without writing new Python classes.
- **Cross-document anchors** — define YAML anchors in one document and reference them in another, even across multiple `load_string` calls.
- **Round-trip dumping** — serialize configs back to YAML so every experiment is fully reproducible.


Why yaloader?
---------------------------------------

Many projects start with ad-hoc YAML loading: `yaml.safe_load()` into a dict, then manually passing values around.
This works for small projects but breaks down when you need:

- **Validation** that catches a misspelled activation function or a wrong learning-rate type before a 12-hour training run — not deep inside the training loop.
- **Layered configs** where team-wide defaults live in one file, project settings in another, and per-experiment overrides in a third.
- **Inheritance** where a family of related model configs (ResNet, VGG, MLP) shares common training parameters but differs in architecture.

yaloader gives you all of this with minimal boilerplate. You define a config class, decorate it, and load it from YAML — that's it for the simple case. The priority system and inheritance kick in when your project grows.


How it works
---------------------------------------

Using yaloader involves three steps:

1. **Define** a configuration class that inherits from `YAMLBaseConfig` and is decorated with `@yaloader.loads`.
2. **Load** YAML data into a `ConfigLoader` — from strings, files, or directories. Each source can have a priority.
3. **Construct** the final configuration by merging all loaded data and resolving inheritance.

```python
import yaloader

class Model:
    def __init__(self, hidden_dim: int, learning_rate: float):
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate

@yaloader.loads(Model)
class ModelConfig(yaloader.YAMLBaseConfig):
    hidden_dim: int = 128
    learning_rate: float = 0.001

loader = yaloader.ConfigLoader()
loader.load_file("base")          # priority defaults to 0
loader.load_file("experiment_01") # can set higher priority

config = loader.construct_from_string("!Model {}")
model = config.load()  # creates an instance of Model
```


Loading vs. Construction
---------------------------------------

yaloader separates two distinct phases:

**Loading** stores configuration data in the `ConfigLoader`. You can load from multiple sources, each with a priority.
Nothing is constructed yet — configs are just collected.

**Construction** takes a config reference (like `!Model {}`) and resolves it against all loaded data:
inherited fields, priority merging, and nested config construction all happen here.

This separation means you can load all your config files upfront, then construct individual objects on demand.

The rest of this guide builds a complete ML training pipeline configuration system, one feature at a time.
