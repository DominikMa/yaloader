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

The `@yaloader.loads` decorator registers a config class so it can be loaded from YAML:

```{code-cell} python3
from dataclasses import dataclass
import yaloader

@dataclass
class Optimizer:
    lr: float
    momentum: float

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
- `UserConfig` → `!User`
- `ResNet50Config` → `!ResNet50`

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
For more control, override it:

```{code-cell} python3
@yaloader.loads()
class CustomOptimizerConfig(yaloader.YAMLBaseConfig):
    _yaml_tag = "!CustomOptimizer"
    lr: float = 0.01
    momentum: float = 0.9

    def load(self):
        print(f"Creating optimizer with lr={self.lr}")
        return Optimizer(lr=self.lr, momentum=self.momentum)
```


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

Config fields can reference other config classes. When constructing, yaloader recursively resolves nested configs:

```{code-cell} python3
@yaloader.loads()
class LayerConfig(yaloader.YAMLBaseConfig):
    units: int = 64

@yaloader.loads()
class NetworkConfig(yaloader.YAMLBaseConfig):
    name: str = "default"
    layer: LayerConfig = LayerConfig()

loader = yaloader.ConfigLoader()
result = loader.construct_from_string('!Network {name: "mynet", layer: !Layer {units: 128}}')
print(result)
```
