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

Configuration Inheritance
=======================================

yaloader config classes can inherit from each other just like regular Python classes.
When a config is constructed, fields from its parent configs are included automatically.


Basic inheritance
---------------------------------------

```{code-cell} python3
import yaloader

@yaloader.loads()
class ModelConfig(yaloader.YAMLBaseConfig):
    name: str = "unnamed"
    epochs: int = 10

@yaloader.loads()
class ResNetConfig(ModelConfig):
    layers: int = 50
```

`ResNetConfig` inherits the `name` and `epochs` fields from `ModelConfig`. In YAML, both the parent and child tags work independently:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Set defaults for all models
loader.load_string("- !Model {epochs: 100}")

# Set defaults specific to ResNet
loader.load_string("- !ResNet {layers: 101}")

config = loader.construct_from_string("!ResNet {}")
print(f"name={config.name}, epochs={config.epochs}, layers={config.layers}")
```

The `epochs` value comes from the loaded `!Model` config — inherited fields are resolved through the class hierarchy.


Field resolution order
---------------------------------------

When constructing a config, fields are resolved from multiple sources. The full precedence (highest wins):

1. **Explicit local fields** — fields set directly in the YAML being constructed
2. **Explicit inherited fields** — explicit fields from parent config classes (left base first)
3. **Explicit loaded fields** — fields from loaded configs, ordered by priority (highest first)
4. **Default fields** — same order as above, but for fields that weren't explicitly set

"Explicit" means the field appeared in a YAML document. "Default" means it comes from the Python class definition.

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Base model config at priority 0
loader.load_string("- !Model {name: BaseModel, epochs: 50}")

# ResNet config at priority 10
loader.load_string("priority: 10\n---\n- !ResNet {layers: 152}")

config = loader.construct_from_string("!ResNet {name: MyResNet}")
print(f"name={config.name}, epochs={config.epochs}, layers={config.layers}")
```

Here `name` is "MyResNet" (explicit local), `epochs` is 50 (inherited from `!Model` loaded config), and `layers` is 152 (from `!ResNet` loaded config).


Multiple inheritance
---------------------------------------

Config classes can inherit from multiple parent configs. The left-most base has the highest priority:

```{code-cell} python3
@yaloader.loads()
class TrainerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001
    batch_size: int = 32

@yaloader.loads()
class AugmentationConfig(yaloader.YAMLBaseConfig):
    flip: bool = True
    rotate: bool = False

@yaloader.loads()
class FullTrainingConfig(TrainerConfig, AugmentationConfig):
    experiment_name: str = "default"
```

```{code-cell} python3
loader = yaloader.ConfigLoader()
loader.load_string("- !Trainer {lr: 0.01}")
loader.load_string("- !Augmentation {flip: false, rotate: true}")

config = loader.construct_from_string("!FullTraining {experiment_name: exp1}")
print(f"lr={config.lr}, batch_size={config.batch_size}, flip={config.flip}, rotate={config.rotate}")
```

Fields from `TrainerConfig` (the left-most base) take precedence over `AugmentationConfig` if there were conflicts.
