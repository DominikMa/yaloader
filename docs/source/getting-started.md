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

Getting Started
=======================================

yaloader is a type-safe configuration library designed for projects with complex, hierarchical component structures—like Machine Learning pipelines or plugin-based applications.

Installation
---------------------------------------

```bash
pip install yaloader
```

The Component Pattern
---------------------------------------

The core idea of yaloader is the **decoupling of configuration from implementation**. You define your logic in standard Python classes and your configuration in Pydantic-powered "Config" classes.

Suppose you have a Model and a Trainer:

```{code-cell} python3
class Model:
    def __init__(self, layers: int, hidden_dim: int):
        self.layers = layers
        self.hidden_dim = hidden_dim

class Trainer:
    def __init__(self, model: Model, lr: float, batch_size: int):
        self.model = model
        self.lr = lr
        self.batch_size = batch_size
```

### 1. Define Config Classes

Use the `@yaloader.loads(TargetClass)` decorator to register a config class. This tells yaloader: *"When you see this tag in YAML, use this config class to validate it, and create an instance of TargetClass when .load() is called."*

```{code-cell} python3
import yaloader

@yaloader.loads(Model)
class ModelConfig(yaloader.YAMLBaseConfig):
    layers: int = 50
    hidden_dim: int = 512

@yaloader.loads(Trainer)
class TrainerConfig(yaloader.YAMLBaseConfig):
    model: ModelConfig = ModelConfig()
    lr: float = 0.001
    batch_size: int = 32
```

### 2. The Configuration Workflow

Working with yaloader involves two stages: **Loading** (gathering data) and **Construction** (building the objects).

#### Stage A: Loading Defaults
You typically load a "base" configuration that defines the default setup for your components.

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Load base defaults for our components
loader.load_string("""
- !Model {layers: 101, hidden_dim: 1024}
- !Trainer {batch_size: 64}
""")
```

#### Stage B: Late Binding & Construction
When you are ready to run, you "construct" your entry point. yaloader merges your local overrides with the previously loaded defaults.

```{code-cell} python3
# Construct a Trainer with a specific learning rate override
# All other fields (layers, hidden_dim, batch_size) are pulled from the loader's state.
config = loader.construct_from_string("!Trainer {lr: 0.01}")

print(f"Configured Batch Size: {config.batch_size}")
print(f"Configured Model Layers: {config.model.layers}")

# Create the actual Python objects
trainer = config.load()
print(f"Actual Trainer LR: {trainer.lr}")
print(f"Actual Model Layers: {trainer.model.layers}")
```

Why is this beneficial?
---------------------------------------

1.  **Late Binding:** You don't hardcode which `Model` or `Dataset` your `Trainer` uses. You can swap implementations by just changing a tag in YAML.
2.  **Type Safety:** Pydantic validates every field. If you provide `lr: "fast"` (a string), yaloader catches it during `construct_from_string` with a clear error message.
3.  **Layered State:** The `ConfigLoader` acts as a repository of configuration state. You can layer multiple YAML files (e.g., `base.yaml`, `gpu_settings.yaml`, `experiment_01.yaml`) and yaloader handles the merging logic.

Next Steps
---------------------------------------

*   Learn about {doc}`loading-and-priority` to manage complex override layers.
*   See how {doc}`variable-configs` allow you to have multiple distinct configurations of the same class (e.g., `!TrainDataset` and `!ValDataset`).
*   Check {doc}`cross-document-anchors` to keep hyper-parameters synchronized across components.
