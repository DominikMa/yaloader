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

Cross-Document Anchors
=======================================

Standard YAML anchors (`&name` / `*name`) only work within a single document.
yaloader extends this so that anchors persist across documents and even across multiple `load_string` calls on the same `ConfigLoader`.

This is the primary way to maintain a **Single Source of Truth** for hyper-parameters shared between unrelated components.


Use Case: Shared Image Size
---------------------------------------

Imagine you have a `Dataset` that pre-processes images to a certain size and a `Model` that expects that exact same size as input.

```{code-cell} python3
import yaloader

@yaloader.loads()
class DatasetConfig(yaloader.YAMLBaseConfig):
    name: str = "imagenet"
    image_size: int = 224

@yaloader.loads()
class ModelConfig(yaloader.YAMLBaseConfig):
    name: str = "resnet"
    input_size: int = 224

loader = yaloader.ConfigLoader()

# First document: Define the shared values
loader.load_string(r"""
anchors:
  shared_size: &img_size 299
""")

# Second document (can be a different file!): Use the shared values
loader.load_string(r"""
- !Dataset {image_size: *img_size}
- !Model {input_size: *img_size}
""")

ds = loader.construct_from_string("!Dataset {}")
model = loader.construct_from_string("!Model {}")
print(f"Dataset image_size={ds.image_size}")
print(f"Model input_size={model.input_size}")
```

By using `*img_size`, you ensure the two components are always in sync. If you change the anchor in the first document, both components update automatically.


Workflow: Centralized `anchors.yaml`
---------------------------------------

A common pattern for large projects is to have a centralized file for global hyper-parameters.

**`anchors.yaml`**
```yaml
anchors:
  global_lr: &lr 0.001
  global_batch_size: &batch 64
```

**`trainer.yaml`**
```yaml
- !Trainer
    learning_rate: *lr
    batch_size: *batch
```

**`main.py`**
```python
loader = yaloader.ConfigLoader()
loader.load_file("anchors.yaml")
loader.load_file("trainer.yaml")
```


Isolation between loaders
---------------------------------------

Each `ConfigLoader` instance has its own isolated anchor scope. This is important for running multiple experiments in parallel without naming collisions.

```{code-cell} python3
loader_a = yaloader.ConfigLoader()
loader_a.load_string("anchors: { val: &v 42 }")

loader_b = yaloader.ConfigLoader()
# loader_b does NOT have access to &v from loader_a.
# This prevents "leaks" between different experiments.
```


Summary
---------------------------------------

Cross-document anchors are a powerful tool for:
1.  **Ensuring consistency** between decoupled components (e.g., Model and Dataset).
2.  **Centralizing configuration** of global parameters in a single file.
3.  **Maintaining clean YAML** by avoiding repetitive hard-coded values.
