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
We saw a simple `OptimizerConfig` in {doc}`getting-started`. Now let's look at config classes in more depth.


The `@loads` decorator
---------------------------------------

The `@yaloader.loads` decorator registers a config class so it can be loaded from YAML:

```{code-cell} python3
import yaloader

class Optimizer:
    def __init__(self, lr: float, momentum: float):
        self.lr = lr
        self.momentum = momentum

    def __repr__(self):
        return f"Optimizer(lr={self.lr}, momentum={self.momentum})"

@yaloader.loads(Optimizer)
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.01
    momentum: float = 0.9
```

The `loaded_class` argument (here `Optimizer`) tells yaloader what to create when `.load()` is called. If omitted, you must override the `load()` method yourself.


YAML tags
---------------------------------------

Each config class is identified by a YAML tag. By default, the tag is derived from the class name by removing the `Config` suffix and adding a `!` prefix:

- `OptimizerConfig` → `!Optimizer`
- `ResNetConfig` → `!ResNet`
- `DatasetConfig` → `!Dataset`

If the class name doesn't end with `Config`, registration will fail. You can set a custom tag explicitly:

```{code-cell} python3
@yaloader.loads()
class MyModel(yaloader.YAMLBaseConfig):
    _yaml_tag = "!MyModel"
    layers: int = 3
```


The `load()` method
---------------------------------------

The `load()` method creates an instance of the loaded class from the config's fields:

```{code-cell} python3
loader = yaloader.ConfigLoader()
config = loader.construct_from_string("!Optimizer {lr: 0.001}")
optimizer = config.load()
print(optimizer)
```

The default `load()` passes all config fields as keyword arguments to the loaded class.
For more control, override it. This is useful when constructing the object requires more than just passing fields — for example, conditional initialization or transforming config values:

```{code-cell} python3
class ResNet:
    def __init__(self, layers: int, pretrained_weights: str | None = None):
        self.layers = layers
        self.pretrained_weights = pretrained_weights

    def __repr__(self):
        return f"ResNet(layers={self.layers}, weights={self.pretrained_weights})"

@yaloader.loads()
class ResNetConfig(yaloader.YAMLBaseConfig):
    layers: int = 50
    pretrained: bool = False

    def load(self):
        weights = f"resnet{self.layers}.pth" if self.pretrained else None
        return ResNet(layers=self.layers, pretrained_weights=weights)
```

```{code-cell} python3
loader = yaloader.ConfigLoader()
config = loader.construct_from_string("!ResNet {layers: 101, pretrained: true}")
model = config.load()
print(model)
```

The `load()` override decouples config fields from constructor arguments — the config can have a `pretrained` boolean while the constructor takes a `pretrained_weights` path.


Type validation
---------------------------------------

`YAMLBaseConfig` inherits from Pydantic's `BaseModel`, so all field types are validated.
Wrong types are caught at YAML load time:

```{code-cell} python3
---
tags: [raises-exception]
---
try:
    loader.construct_from_string("!Optimizer {lr: 'fast', momentum: 0.9}")
except yaloader.YAMLValueError as e:
    raise e from None
```


Extra fields are forbidden
---------------------------------------

By default, `YAMLBaseConfig` sets `extra="forbid"` — any field in the YAML that isn't defined on the config class raises an error:

```{code-cell} python3
---
tags: [raises-exception]
---
try:
    loader.construct_from_string("!Optimizer {lr: 0.01, weight_decay: 0.001}")
except yaloader.YAMLValueError as e:
    raise e from None
```

This catches typos and outdated config files early.


Nested configs
---------------------------------------

Config fields can reference other config classes. When constructing, yaloader recursively resolves nested configs.
This is how you build composed pipelines — a trainer config that contains an optimizer and a model:

```{code-cell} python3
@yaloader.loads()
class TrainerConfig(yaloader.YAMLBaseConfig):
    name: str = "default"
    optimizer: OptimizerConfig = OptimizerConfig()
    model: ResNetConfig = ResNetConfig()

loader = yaloader.ConfigLoader()
result = loader.construct_from_string(
    '!Trainer {name: "run_01", optimizer: !Optimizer {lr: 0.01}, model: !ResNet {layers: 18}}'
)
print(result)
```
