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

Best Practices
=======================================

Patterns and conventions for getting the most out of yaloader.


Config directory organization
---------------------------------------

A recommended layout that grows with your project:

**Small project** — a few config files:

```
configs/
  defaults.yaml
  experiment.yaml
```

**Medium project** — separate concerns:

```
configs/
  defaults.yaml            # team-wide defaults (priority 0)
  models/
    resnet.yaml             # model-specific defaults
    mlp.yaml
  experiments/
    exp_001.yaml            # experiment overrides (priority 10–20)
    exp_002.yaml
```

**Large project** — full layering with swappable components and machine configs:

```
configs/
  base.yaml                 # priority: 1 — shared defaults (logging, training params)
  runner.yaml                # pipeline structure with ConfigVar placeholders
  debug.yaml                 # priority: 98 — small batches, few iterations
  dataset/
    cifar10.yaml             # ConfigVarTrainDataset for CIFAR-10
    imagenet.yaml            # ConfigVarTrainDataset for ImageNet
  model/
    resnet.yaml              # ConfigVarModel for ResNet
    unet.yaml                # ConfigVarModel for U-Net
  trainer/
    adam.yaml                 # ConfigVarOptimizer for Adam
    sgd.yaml                  # ConfigVarOptimizer for SGD
  pc/
    workstation_01.yaml      # priority: 2 — machine-specific paths, worker counts
    cluster_gpu.yaml         # priority: 2 — cluster paths
```

Load the base directory, then select which components to use:

```python
loader = yaloader.ConfigLoader()
loader.load_directory(Path("configs/"))             # loads base.yaml, runner.yaml
loader.load_file(Path("configs/dataset/imagenet"))   # selects ImageNet
loader.load_file(Path("configs/model/resnet"))       # selects ResNet
loader.load_file(Path("configs/trainer/adam"))        # selects Adam
loader.load_file(Path("configs/pc/workstation_01"))  # machine paths
# loader.load_file(Path("configs/debug"))            # uncomment for debugging
```


Naming conventions
---------------------------------------

**Config classes**: Name them `<Thing>Config`. The `Config` suffix is stripped to create the YAML tag:

- `OptimizerConfig` → `!Optimizer`
- `ResNetConfig` → `!ResNet`
- `CIFAR10Config` → `!CIFAR10`

**Variable configs**: Use descriptive names after `ConfigVar` that indicate the role or implementation:

- `!ConfigVarTrainDataset` — swappable dataset implementation
- `!ConfigVarOptimizer` — swappable optimizer choice
- `!ConfigVarModel` — swappable model architecture

**YAML files**: Use lowercase with underscores. Name files after what they configure, not what they override.


Priority strategy
---------------------------------------

A recommended priority scheme:

| Priority | Purpose | Example |
|---|---|---|
| 1 | Base defaults | Shared training defaults, logging |
| 2 | Machine/environment config | Data paths, worker counts |
| 10–50 | Experiment overrides | Hyperparameter changes |
| 98 | Debug overrides | Small batches, few iterations |

Keep the range sparse — you rarely need more than 3–4 distinct priority levels. Leave gaps so you can insert new layers later.


When to use inheritance vs composition vs variable configs
---------------------------------------

**Inheritance** — when different config types share a common interface but have different fields:

```python
class ModelConfig(YAMLBaseConfig):
    name: str
    epochs: int = 10

class ResNetConfig(ModelConfig):
    layers: int = 50

class MLPConfig(ModelConfig):
    hidden_dim: int = 128
```

Use when: the variants add or override fields, or need different `load()` logic.

**Composition** — when a config contains other configs:

```python
class ExperimentConfig(YAMLBaseConfig):
    model: ModelConfig
    optimizer: OptimizerConfig
    dataset: DatasetConfig
```

Use when: the objects are independent and used together.

**Variable configs** — when you need multiple distinct configurations of the same class:

```yaml
# Two dataset instances with different splits — impossible with just !Dataset
- !ConfigVarTrainDataset {_tag: "!Dataset", name: cifar10, split: train}
- !ConfigVarTestDataset {_tag: "!Dataset", name: cifar10, split: test}
```

Use when: your pipeline needs multiple instances of the same config class, each independently configurable.


Pydantic validators
---------------------------------------

Since `YAMLBaseConfig` is a Pydantic `BaseModel`, you can add validators for cross-field constraints:

```{code-cell} python3
import yaloader
from pydantic import field_validator

@yaloader.loads()
class TrainingConfig(yaloader.YAMLBaseConfig):
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001

    @field_validator("batch_size")
    @classmethod
    def batch_size_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("batch_size must be positive")
        return v

    @field_validator("learning_rate")
    @classmethod
    def lr_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("learning_rate must be positive")
        return v
```

```{code-cell} python3
---
tags: [raises-exception]
---
try:
    loader = yaloader.ConfigLoader()
    loader.construct_from_string("!Training {batch_size: -1}")
except yaloader.YAMLValueError as e:
    raise e from None
```

Validators run at config construction time — before any training code executes.


Common mistakes
---------------------------------------

**Forgetting `.load()`** — `construct_from_string` returns a config object, not the target object:

```python
# Wrong — config is a TrainingConfig, not a Trainer
config = loader.construct_from_string("!Training {}")
train(config)  # Passing the config, not the object

# Right
config = loader.construct_from_string("!Training {}")
trainer = config.load()
train(trainer)
```

**Mutable default values** — Pydantic v2 handles mutable defaults correctly, but be explicit:

```python
# Fine — Pydantic copies the default
class Config(YAMLBaseConfig):
    tags: list[str] = []

# Also fine — use default_factory for clarity
from pydantic import Field
class Config(YAMLBaseConfig):
    tags: list[str] = Field(default_factory=list)
```

**Circular config dependencies** — avoid configs that reference each other:

```python
# Don't do this
class AConfig(YAMLBaseConfig):
    b: "BConfig"

class BConfig(YAMLBaseConfig):
    a: AConfig
```

Restructure so dependencies flow in one direction.
