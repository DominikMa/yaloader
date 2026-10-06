---
jupytext:
    text_representation:
        format_name: myst
kernelspec:
    display_name: Python 3
    name: python3
---

```{code-cell} python3
---
tags: [remove-cell]
---
import sys
import os
sys.path.insert(0, os.path.abspath('../../src/'))

import functools
ipython = get_ipython()
method_name = "showtraceback"
setattr(
    ipython,
    method_name,
    functools.partial(
        getattr(ipython, method_name),
        exception_only=True
    )
)
```

Configuration Classes
=======================================

Every yaloader configuration is a Python class that inherits from `YAMLBaseConfig` and is registered with the `@yaloader.loads` decorator.


The `@loads` decorator
---------------------------------------

The `@yaloader.loads(TargetClass)` decorator registers a config class so it can be loaded from YAML:

```{code-cell} python3
import yaloader

class Optimizer:
    def __init__(self, lr: float, momentum: float):
        self.lr = lr
        self.momentum = momentum

@yaloader.loads(Optimizer)
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.01
    momentum: float = 0.9
```

### Automatic Tag Naming
By default, the YAML tag is derived from the class name by removing the `Config` suffix and adding a `!` prefix:
*   `OptimizerConfig` → `!Optimizer`
*   `ResNetConfig` → `!ResNet`

You can also specify a custom tag: `@yaloader.loads(Optimizer, _yaml_tag="!MyOpt")`.


Customizing the `load()` method
---------------------------------------

The default `load()` method simply passes all fields as keyword arguments to the `TargetClass`. However, you can override `load()` to perform more complex initialization, such as dependency injection or runtime setup.

### Use Case: Runtime Environment Setup
Suppose your `Model` needs to be moved to a specific device (CPU/GPU) that is determined at runtime, not just from config:

```{code-cell} python3
class Model:
    def __init__(self, layers: int):
        self.layers = layers
        self.device = "cpu"
    
    def to(self, device):
        self.device = device
        return self

@yaloader.loads()
class ModelConfig(yaloader.YAMLBaseConfig):
    layers: int = 50

    def load(self, device: str = "cuda"):
        # We can pass runtime arguments to .load()
        model = Model(layers=self.layers)
        return model.to(device)

loader = yaloader.ConfigLoader()
config = loader.construct_from_string("!Model {layers: 101}")

# Pass runtime context into the loading process
model = config.load(device="cuda:0")
print(f"Model on: {model.device}")
```


Partial Validation (Abstract Configs)
---------------------------------------

A powerful feature of yaloader is that **configs don't have to be complete when they are loaded.** They only need to be complete when they are finally **constructed**.

This allows you to define "Abstract" or "Partial" configs in your base files that are missing required fields.

### Use Case: The "Missing Path" Pattern
Imagine a `Dataset` that requires a `root` directory, but you don't want to hardcode a path in your shared `base.yaml`.

```{code-cell} python3
@yaloader.loads()
class DatasetConfig(yaloader.YAMLBaseConfig):
    name: str
    root: str  # Required field, no default!

loader = yaloader.ConfigLoader()

# This is VALID during the loading phase, even though 'root' is missing.
loader.load_string("""
- !Dataset {name: imagenet}
""")

# Validation only fails if we try to CONSTRUCT the final object without the missing field.
try:
    loader.construct_from_string("!Dataset {}")
except Exception as e:
    print(f"Construction failed as expected: {e.title}")

# But it succeeds if we provide the missing field during construction.
config = loader.construct_from_string("!Dataset {root: '/data/imagenet'}")
print(f"Successfully constructed {config.name} at {config.root}")
```

This "Partial Validation" allows your `ConfigLoader` to act as a flexible repository of "templates" that are filled in as needed.


Type Safety and Constraints
---------------------------------------

Because yaloader is built on Pydantic v2, you can use advanced types and constraints:

```{code-cell} python3
from pydantic import Field

@yaloader.loads()
class TrainerConfig(yaloader.YAMLBaseConfig):
    # Field constraints are validated automatically
    lr: float = Field(0.001, gt=0, lt=1.0)
    batch_size: int = Field(32, ge=1)
    
    # Nested configs are also validated
    model: ModelConfig = ModelConfig()
```
