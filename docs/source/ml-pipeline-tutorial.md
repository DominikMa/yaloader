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

ML Pipeline Tutorial
=======================================

This tutorial ties together all yaloader features to build a complete configuration system for an image classification pipeline.
We'll define a config hierarchy, layer configs with priorities, use variable configs to swap dataset and optimizer implementations, share an image size via anchors, and dump the final config for reproducibility.


Step 1: Define the pipeline classes
---------------------------------------

The Python classes that make up our pipeline. In a real project these would be PyTorch modules, dataloaders, etc.

```{code-cell} python3
class Dataset:
    def __init__(self, name: str, root: str, image_size: int):
        self.name = name
        self.root = root
        self.image_size = image_size

    def __repr__(self):
        return f"Dataset(name={self.name!r}, root={self.root!r}, image_size={self.image_size})"

class Model:
    def __init__(self, name: str, input_size: int, layers: int):
        self.name = name
        self.input_size = input_size
        self.layers = layers

    def __repr__(self):
        return f"Model(name={self.name!r}, input_size={self.input_size}, layers={self.layers})"

class Optimizer:
    def __init__(self, lr: float, momentum: float):
        self.lr = lr
        self.momentum = momentum

    def __repr__(self):
        return f"Optimizer(lr={self.lr}, momentum={self.momentum})"

class Experiment:
    def __init__(self, name: str, dataset: Dataset, model: Model, optimizer: Optimizer):
        self.name = name
        self.dataset = dataset
        self.model = model
        self.optimizer = optimizer

    def __repr__(self):
        return f"Experiment(name={self.name!r})"
```


Step 2: Define the config classes
---------------------------------------

Each config class knows how to create its corresponding object:

```{code-cell} python3
import yaloader

@yaloader.loads(Dataset)
class DatasetConfig(yaloader.YAMLBaseConfig):
    name: str = "unnamed"
    root: str = "/data"
    image_size: int = 32

@yaloader.loads(Model)
class ModelConfig(yaloader.YAMLBaseConfig):
    name: str = "unnamed"
    input_size: int = 32
    layers: int = 3

@yaloader.loads(Optimizer)
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001
    momentum: float = 0.9

@yaloader.loads()
class ExperimentConfig(yaloader.YAMLBaseConfig):
    name: str = "baseline"
    dataset: DatasetConfig = DatasetConfig()
    model: ModelConfig = ModelConfig()
    optimizer: OptimizerConfig = OptimizerConfig()

    def load(self):
        return Experiment(
            name=self.name,
            dataset=self.dataset.load(),
            model=self.model.load(),
            optimizer=self.optimizer.load(),
        )
```

`ExperimentConfig` overrides `load()` to recursively load its nested configs into real objects.


Step 3: Use variable configs for multiple instances
---------------------------------------

Without variable configs, each config class has only one tag — you can't configure two different datasets or optimizers separately in YAML. Variable configs give each instance its own tag, so you can configure them independently and swap implementations by loading different files:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# runner.yaml — the pipeline structure with placeholder variable configs
loader.load_string(
    """
    - !Experiment
        dataset: !ConfigVarTrainDataset {_tag: "!Dataset"}
        model: !ConfigVarModel {_tag: "!Model"}
        optimizer: !ConfigVarOptimizer {_tag: "!Optimizer"}
    """
)

# dataset/cifar10.yaml — one dataset implementation
loader.load_string(
    """
    - !ConfigVarTrainDataset {_tag: "!Dataset", name: cifar10, root: /data/cifar10, image_size: 32}
    """
)

# dataset/imagenet.yaml — another (would override the above if loaded after)
# loader.load_string(
#     """
#     - !ConfigVarTrainDataset {_tag: "!Dataset", name: imagenet, root: /data/imagenet, image_size: 224}
#     """
# )
```

To switch datasets, just load a different dataset file.


Step 4: Layer configs with priorities
---------------------------------------

Add base defaults and machine-specific settings:

```{code-cell} python3
# base.yaml (priority 1) — shared defaults
loader.load_string(r"""
priority: 1
---
- !Model {layers: 50}
- !Optimizer {lr: 0.001, momentum: 0.9}
""")

# trainer/adam.yaml — optimizer choice
loader.load_string(
    """
    - !ConfigVarOptimizer {_tag: "!Optimizer", lr: 0.0001, momentum: 0.0}
    """
)

# pc/workstation.yaml (priority 2) — machine-specific paths
loader.load_string(r"""
priority: 2
---
- !Dataset {root: "/ssd1/datasets"}
""")
```


Step 5: Share values with anchors
---------------------------------------

Use cross-document anchors to keep the image size consistent between dataset and model:

```{code-cell} python3
loader2 = yaloader.ConfigLoader()

loader2.load_string(r"""
anchors:
  image_size: &img_size 224
---
- !Dataset {name: imagenet, root: /data/imagenet, image_size: *img_size}
- !Model {name: resnet, input_size: *img_size, layers: 50}
- !Optimizer {lr: 0.001, momentum: 0.9}
""")

ds = loader2.construct_from_string("!Dataset {}")
model = loader2.construct_from_string("!Model {}")
print(f"Dataset image_size={ds.image_size}, Model input_size={model.input_size}")
```

Change `&img_size` once, both configs update.


Step 6: Construct and run the experiment
---------------------------------------

Bring it all together — construct the full experiment and create the objects:

```{code-cell} python3
experiment = loader.construct_from_string("!Experiment {name: exp_001}")
print("Config:")
print(f"  name: {experiment.name}")
print(f"  dataset: {experiment.dataset}")
print(f"  model: {experiment.model}")
print(f"  optimizer: {experiment.optimizer}")
```

```{code-cell} python3
result = experiment.load()
print(f"\nConstructed: {result}")
print(f"  {result.dataset}")
print(f"  {result.model}")
print(f"  {result.optimizer}")
```


Step 7: Debug override
---------------------------------------

During development, add a high-priority debug config to reduce batch sizes and iterations without touching any other file:

```{code-cell} python3
loader.load_string(r"""
priority: 98
---
- !Model {layers: 2}
""")

debug_exp = loader.construct_from_string("!Experiment {name: debug_run}")
print(f"Debug model layers: {debug_exp.model.layers}")
```

Remove the debug file for production — the base configs apply unchanged.


Step 8: Dump for reproducibility
---------------------------------------

After running an experiment, dump the resolved config to preserve the exact settings:

```{code-cell} python3
import yaml

class FullDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = False

dumped = yaml.dump(experiment, Dumper=FullDumper)
print("Saved config:")
print(dumped)
```

Save this YAML alongside your model checkpoint. To reproduce the experiment later, reload and construct:

```{code-cell} python3
loader3 = yaloader.ConfigLoader()
restored = loader3.construct_from_string(dumped)
restored_result = restored.load()
print(f"Restored: {restored_result}")
```


Summary
---------------------------------------

This tutorial used all core yaloader features:

| Feature | How we used it |
|---|---|
| Config classes | `DatasetConfig`, `ModelConfig`, `OptimizerConfig`, `ExperimentConfig` |
| Variable configs | `!ConfigVarTrainDataset`, `!ConfigVarOptimizer` — multiple instances of the same class |
| Priority layering | Base defaults (1) → machine paths (2) → debug override (98) |
| Nested configs | `ExperimentConfig` contains Dataset, Model, and Optimizer configs |
| Cross-document anchors | Shared `&img_size` between dataset and model |
| Dumping | Full config snapshot for reproducibility |

For recommended patterns and conventions, see {doc}`best-practices`.
