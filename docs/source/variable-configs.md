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

Variable Configs
=======================================

The problem
---------------------------------------

Without variable configs, each config class has exactly **one tag** — `OptimizerConfig` is always `!Optimizer`. That means you can only configure one optimizer in your config files. If your pipeline needs two — say, one for training and one for fine-tuning — you'd have to pass the differences at the `construct_from_string` call, which defeats the purpose of file-based configuration.

Variable configs solve this by letting you define **multiple distinct configurations of the same class** directly in YAML, each with its own tag.


The `!ConfigVar` prefix
---------------------------------------

Any YAML tag starting with `!ConfigVar` is treated as a variable config. You specify which base config it maps to using the `_tag` field:

```{code-cell} python3
import yaloader

@yaloader.loads()
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001
    momentum: float = 0.9

loader = yaloader.ConfigLoader()

# Define two distinct optimizer configurations
loader.load_string(
    """
    - !ConfigVarTrainOptimizer {_tag: "!Optimizer", lr: 0.01, momentum: 0.9}
    - !ConfigVarFineTuneOptimizer {_tag: "!Optimizer", lr: 0.0001, momentum: 0.0}
    """
)
```

Now your pipeline can reference each one independently:

```{code-cell} python3
train_opt = loader.construct_from_string('!ConfigVarTrainOptimizer {_tag: "!Optimizer"}')
finetune_opt = loader.construct_from_string('!ConfigVarFineTuneOptimizer {_tag: "!Optimizer"}')
print(f"Train: lr={train_opt.lr}, momentum={train_opt.momentum}")
print(f"Fine-tune: lr={finetune_opt.lr}, momentum={finetune_opt.momentum}")
```

Both are `OptimizerConfig` instances, but configured differently — and each can be independently overridden via priority layering.


Multiple instances in a pipeline
---------------------------------------

This is essential when a pipeline needs multiple instances of the same class. For example, a training runner that uses separate dataset configs for training and testing:

```{code-cell} python3
@yaloader.loads()
class DatasetConfig(yaloader.YAMLBaseConfig):
    name: str = "unnamed"
    root: str = "/data"
    split: str = "train"

@yaloader.loads()
class RunnerConfig(yaloader.YAMLBaseConfig):
    name: str = "default"
    train_dataset: DatasetConfig = DatasetConfig()
    test_dataset: DatasetConfig = DatasetConfig()

loader = yaloader.ConfigLoader()

# runner.yaml — references two distinct dataset configs
loader.load_string(
    """
    - !Runner
        train_dataset: !ConfigVarTrainDataset {_tag: "!Dataset"}
        test_dataset: !ConfigVarTestDataset {_tag: "!Dataset"}
    """
)

# dataset/cifar10.yaml — configures both splits
loader.load_string(
    """
    - !ConfigVarTrainDataset {_tag: "!Dataset", name: cifar10, root: /data/cifar10, split: train}
    - !ConfigVarTestDataset {_tag: "!Dataset", name: cifar10, root: /data/cifar10, split: test}
    """
)

runner = loader.construct_from_string("!Runner {name: experiment_01}")
print(f"Train: {runner.train_dataset.name} ({runner.train_dataset.split})")
print(f"Test: {runner.test_dataset.name} ({runner.test_dataset.split})")
```

Without variable configs, both datasets would share a single `!Dataset` config — you couldn't set different splits.

To switch to a different dataset, just load a different file that redefines `!ConfigVarTrainDataset` and `!ConfigVarTestDataset`:

```{code-cell} python3
# dataset/imagenet.yaml — same ConfigVar tags, different implementation
loader.load_string(
    """
    - !ConfigVarTrainDataset {_tag: "!Dataset", name: imagenet, root: /data/imagenet, split: train}
    - !ConfigVarTestDataset {_tag: "!Dataset", name: imagenet, root: /data/imagenet, split: val}
    """
)

runner = loader.construct_from_string("!Runner {name: experiment_02}")
print(f"Train: {runner.train_dataset.name} ({runner.train_dataset.split})")
print(f"Test: {runner.test_dataset.name} ({runner.test_dataset.split})")
```


Chaining variable configs
---------------------------------------

Variable configs can reference other variable configs, creating a chain:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Base preset
loader.add_single_config_string("!ConfigVarBase {_tag: '!Optimizer', lr: 0.05}", priority=1)

# Derived preset — inherits lr from Base, sets momentum
loader.add_single_config_string("!ConfigVarDerived {_tag: '!ConfigVarBase', momentum: 0.99}", priority=1)

result = loader.construct_from_string("!ConfigVarDerived {_tag: '!ConfigVarBase'}")
print(f"lr={result.lr}, momentum={result.momentum}")
```


Variable configs vs Python subclasses
---------------------------------------

When should you use a variable config vs a Python subclass?

- **Variable config** — when you need multiple configurations of the same class. The `load()` logic stays the same, only field values differ. Each variant gets its own tag that can be independently configured via priority layering.
- **Python subclass** — when the variant changes behavior (different `load()` logic or additional fields). For example, a `DatasetLoaderConfig` whose `load()` method transforms nested configs into loaded objects differently than its parent.

Rule of thumb: if you need multiple instances with different values, use variable configs. If you need different behavior, write a subclass.


Validation
---------------------------------------

Variable configs follow the same validation rules as their base config. Extra fields and type errors are caught:

```{code-cell} python3
---
tags: [raises-exception]
---
try:
    loader.construct_from_string("!ConfigVarBad {_tag: '!Optimizer', unknown_field: 1}")
except yaloader.YAMLValueError as e:
    raise e from None
```
