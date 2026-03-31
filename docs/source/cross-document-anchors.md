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

This is useful for values that must stay consistent across multiple configs — for example, an image size shared between a dataset's preprocessing and a model's input layer, or a learning rate used by both the optimizer and a scheduler.


Anchors within a file
---------------------------------------

Use an `anchors` document to define anchors, then reference them in config lists that follow:

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
loader.load_string(r"""
anchors:
  image_size: &img_size 350
---
- !Dataset {name: imagenet, image_size: *img_size}
- !Model {name: resnet, input_size: *img_size}
""")

ds = loader.construct_from_string("!Dataset {}")
model = loader.construct_from_string("!Model {}")
print(f"dataset image_size={ds.image_size}, model input_size={model.input_size}")
```

By defining `&img_size` once, you guarantee the dataset and model always use the same image size. Change it in one place, both update.


Anchors across load calls
---------------------------------------

Anchors defined in one `load_string` call are available in subsequent calls on the **same** `ConfigLoader`:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# First call: define shared values
loader.load_string(r"""
anchors:
  image_size: &img_size 400
""")

# Second call: use them
loader.load_string("- !Dataset {image_size: *img_size}")

config = loader.construct_from_string("!Dataset {}")
print(f"image_size={config.image_size}")
```

This means you can define anchors in a shared file (e.g. `anchors.yaml`) and reference them in separate config files loaded afterwards.


Isolation between loaders
---------------------------------------

Each `ConfigLoader` instance has its own anchor scope. Anchors from one loader do not leak into another:

```{code-cell} python3
loader_a = yaloader.ConfigLoader()
loader_a.load_string(r"""
anchors:
  value: &val 42
""")

loader_b = yaloader.ConfigLoader()
# loader_b does NOT have access to &val from loader_a
```

This means you can safely use multiple `ConfigLoader` instances — for example, one per experiment — without worrying about name collisions.


Anchors in `construct_from_string`
---------------------------------------

Anchors can also be defined inline when constructing:

```{code-cell} python3
@yaloader.loads()
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001

@yaloader.loads()
class SchedulerConfig(yaloader.YAMLBaseConfig):
    base_lr: float = 0.001

loader = yaloader.ConfigLoader()
result = loader.construct_from_string(
    """
    - !Optimizer {lr: &lr 0.01}
    - !Scheduler {base_lr: *lr}
    """
)
for r in result:
    print(r)
```
