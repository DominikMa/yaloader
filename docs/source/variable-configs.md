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

Without variable configs, each config class has exactly **one tag** — `DatasetConfig` is always `!Dataset`. This means you can only configure one dataset in your config files. If your pipeline needs two — say, a `TrainDataset` and a `ValDataset` — you'd be stuck with the same settings for both.

Variable configs solve this by letting you define **multiple distinct configurations of the same class** directly in YAML, each with its own tag.


The `!ConfigVar` prefix
---------------------------------------

Any YAML tag starting with `!ConfigVar` is treated as a variable config. You specify which base config it maps to using the `_tag` field.

### Use Case: Multiple Datasets in a Pipeline

Imagine a `Trainer` that needs both a training and a validation dataset.

```{code-cell} python3
import yaloader

@yaloader.loads()
class DatasetConfig(yaloader.YAMLBaseConfig):
    name: str = "unnamed"
    split: str = "train"

@yaloader.loads()
class TrainerConfig(yaloader.YAMLBaseConfig):
    train_ds: DatasetConfig = DatasetConfig()
    val_ds: DatasetConfig = DatasetConfig()

loader = yaloader.ConfigLoader()

# pipeline.yaml — defines the structure with placeholders
loader.load_string("""
- !Trainer
    train_ds: !ConfigVarTrainDataset {_tag: "!Dataset"}
    val_ds: !ConfigVarValDataset {_tag: "!Dataset"}
""")

# dataset/cifar10.yaml — defines the specific implementations
loader.load_string("""
- !ConfigVarTrainDataset {_tag: "!Dataset", name: cifar10, split: train}
- !ConfigVarValDataset {_tag: "!Dataset", name: cifar10, split: val}
""")

config = loader.construct_from_string("!Trainer {}")
print(f"Train Dataset: {config.train_ds.name} ({config.train_ds.split})")
print(f"Val Dataset: {config.val_ds.name} ({config.val_ds.split})")
```

Both are `DatasetConfig` instances, but they have independent settings.


Layering Variable Configs
---------------------------------------

The real power of variable configs is that each tag has its own independent priority layers.

### Use Case: Per-Dataset Overrides

You can override settings for just one of the variable configs without affecting the other:

```{code-cell} python3
# debug_val.yaml (Priority 10)
loader.load_string("""
priority: 10
---
- !ConfigVarValDataset {split: 'subset'}
""")

config = loader.construct_from_string("!Trainer {}")
print(f"Train Dataset split: {config.train_ds.split}")
print(f"Val Dataset split: {config.val_ds.split}")
```

The `!ConfigVarValDataset` override didn't touch the `!ConfigVarTrainDataset` because they are treated as separate "slots" in the `ConfigLoader` registry.


Variable configs vs. Python subclasses
---------------------------------------

*   **Use Variable Configs** when you need multiple instances with different *values* (e.g., `train` vs `val` split).
*   **Use Python Subclasses** when you need different *behavior* (e.g., a `JSONDataset` vs a `CSVDataset` with different `load()` logic).


Summary
---------------------------------------

Variable configs provide a way to:
1.  Reference multiple instances of the same class in a single pipeline.
2.  Independently override those instances using the priority system.
3.  Keep your YAML organized by using descriptive, role-based tags like `!ConfigVarTrainLoader`.
