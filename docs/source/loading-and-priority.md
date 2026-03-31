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

Loading & Priority
=======================================

yaloader separates **loading** (collecting config data) from **construction** (merging and building the final config). This page covers the loading side.

In a typical ML project, configs come from multiple sources: base defaults, dataset-specific settings, machine-specific paths, and debug overrides. yaloader's priority system lets you layer these naturally.


Loading methods
---------------------------------------

There are three ways to load config data into a `ConfigLoader`:

```{code-cell} python3
import yaloader
from pathlib import Path

@yaloader.loads()
class TrainingConfig(yaloader.YAMLBaseConfig):
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
```

### From a string

```{code-cell} python3
loader = yaloader.ConfigLoader()
loader.load_string(
    """
    - !Training {epochs: 100, batch_size: 64}
    """
)
```

### From a file

```python
loader.load_file(Path("config.yaml"))
```

If the file doesn't have a `.yaml` extension, yaloader tries appending it automatically.

### From a directory

```python
loader.load_directory(Path("configs/"))
```

This loads all `*.yaml` files in the directory in alphabetical order.


YAML document format
---------------------------------------

A YAML file (or string) loaded via `load_string` / `load_file` can contain multiple documents separated by `---`. Each document must be one of three types:

### Config list

A YAML list where every item is a tagged config object:

```yaml
- !Training {epochs: 100, batch_size: 64}
- !Training {learning_rate: 0.01}
```

### Priority document

A dict with a `priority` key (integer 0–100). Sets the priority for all config lists that follow it in the same file:

```yaml
priority: 10
---
- !Training {epochs: 200}
```

### Anchors document

A dict with an `anchors` key. The content under `anchors` is arbitrary — it exists only to define YAML anchors for use in later documents (see {doc}`cross-document-anchors`):

```yaml
anchors:
    base_lr: &lr 0.001
---
- !Training {learning_rate: *lr}
```

A document can combine both `priority` and `anchors`:

```yaml
priority: 10
anchors:
    base_lr: &lr 0.001
---
- !Training {learning_rate: *lr}
```

No other keys are allowed in dict documents — unexpected keys raise a `ValueError`.
Empty documents (`---` with nothing between them) are silently ignored.


The priority system
---------------------------------------

When multiple configs exist for the same tag, they are merged by priority. Higher priority values win over lower ones.

Think of priorities as configuration layers:

```{code-cell} python3
@yaloader.loads()
class DataLoaderConfig(yaloader.YAMLBaseConfig):
    batch_size: int = 32
    num_workers: int = 4
    data_root: str = "/data"

loader = yaloader.ConfigLoader()

# Base defaults (priority 1)
loader.load_string(r"""
priority: 1
---
- !Training {epochs: 100, batch_size: 64, learning_rate: 0.001}
- !DataLoader {batch_size: 64, num_workers: 4}
""")

# Machine-specific paths (priority 2) — different per workstation
loader.load_string(r"""
priority: 2
---
- !DataLoader {data_root: "/ssd1/datasets", num_workers: 8}
""")

config = loader.construct_from_string("!DataLoader {}")
print(f"batch_size={config.batch_size}, num_workers={config.num_workers}, data_root={config.data_root}")
```

The `data_root` and `num_workers` come from the machine-specific config (priority 2), while `batch_size` falls back to the base defaults (priority 1).

A typical real-world layout:

```
configs/
  base.yaml               # priority: 1 — shared defaults
  dataset/
    imagenet.yaml          # dataset-specific settings
    cifar10.yaml
  pc/
    workstation_01.yaml    # priority: 2 — machine paths, worker counts
    cluster_gpu.yaml
  debug.yaml               # priority: 98 — small batches, few iterations
```


### Debug overrides

A common pattern is a debug config with a high priority that overrides everything for quick testing:

```{code-cell} python3
# Debug override (priority 98) — small batches, few iterations
loader.load_string(r"""
priority: 98
---
- !Training {epochs: 2, batch_size: 4}
- !DataLoader {batch_size: 4}
""")

config = loader.construct_from_string("!Training {}")
print(f"epochs={config.epochs}, batch_size={config.batch_size}")
```

Load the debug file only during development — in production, leave it out and the base defaults apply.


### Priority scoping

Priorities are scoped **per file** (or per `load_string` call). A `priority:` document affects all subsequent config lists in the same file, but does not carry over to the next file.

You can also pass a priority directly to the loading method, which overrides any `priority:` documents in the file:

```python
loader.load_file(Path("overrides.yaml"), priority=20)
```


Explicit vs. default fields
---------------------------------------

yaloader distinguishes between **explicitly set** fields and **default** fields.
A field is explicit if it appears in the YAML; it's a default if it comes from the Python class definition.

During merging, explicit fields always win over defaults, regardless of priority:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Priority 1: sets learning_rate explicitly
loader.load_string(r"""
priority: 1
---
- !Training {learning_rate: 0.01}
""")

# Priority 10: only sets epochs explicitly (learning_rate not mentioned, stays at default 0.001)
loader.load_string(r"""
priority: 10
---
- !Training {epochs: 200}
""")

config = loader.construct_from_string("!Training {}")
print(f"epochs={config.epochs}, lr={config.learning_rate}")
```

Even though the priority-10 config has a higher priority, the `learning_rate` from the priority-1 config wins because it was explicitly set, while the priority-10 config's `learning_rate` is just the class default.


### Full resolution order

From highest to lowest precedence:

1. Explicit fields from the `construct_from_string` / `construct_from_file` call
2. Explicit fields from loaded configs (highest priority first)
3. Default fields from loaded configs (highest priority first)
4. Class defaults


Construction methods
---------------------------------------

After loading, use one of these to build the final object:

### `construct_from_string`

Parses a single YAML document and deeply constructs it:

```{code-cell} python3
config = loader.construct_from_string("!Training {batch_size: 256}")
print(config)
```

### `construct_from_file`

Same as above but reads from a file:

```python
config = loader.construct_from_file(Path("experiment.yaml"))
```

Both methods merge the given config with all previously loaded data and recursively construct any nested configs.
