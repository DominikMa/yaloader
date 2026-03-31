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

Installation
---------------------------------------

yaloader is on [PyPI](https://pypi.org/project/yaloader/):

```bash
pip install yaloader
```

````{tip}
For development, install with extras:
```bash
pip install yaloader[dev]
```
````


Your first config
---------------------------------------

Suppose you have a class you want to configure from YAML — here, a simple optimizer:

```{code-cell} python3
class Optimizer:
    def __init__(self, lr: float, momentum: float):
        self.lr = lr
        self.momentum = momentum

    def __repr__(self):
        return f"Optimizer(lr={self.lr}, momentum={self.momentum})"
```

Define a configuration class for it:

```{code-cell} python3
import yaloader

@yaloader.loads(Optimizer)
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001
    momentum: float = 0.9
```

The `@yaloader.loads(Optimizer)` decorator registers `OptimizerConfig` with the YAML tag `!Optimizer` (derived from the class name minus the `Config` suffix) and tells it to create `Optimizer` instances when `.load()` is called.


Constructing from YAML
---------------------------------------

Use a `ConfigLoader` to parse YAML and construct the config:

```{code-cell} python3
loader = yaloader.ConfigLoader()
config = loader.construct_from_string("!Optimizer {lr: 0.01, momentum: 0.95}")
print(config)
```

The config object holds the validated configuration. Call `.load()` to create the actual `Optimizer`:

```{code-cell} python3
optimizer = config.load()
print(optimizer)
```


Loading and layering
---------------------------------------

The real power of yaloader comes from loading configs from multiple sources and merging them.
Imagine you have base defaults in one file and per-experiment overrides in another.
Here's a quick preview — see {doc}`loading-and-priority` for the full explanation.

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Load base defaults
loader.load_string(
    """
    - !Optimizer {lr: 0.001, momentum: 0.9}
    """
)

# Construct with the loaded defaults — no fields needed
config = loader.construct_from_string("!Optimizer {}")
print(config)
```

The `!Optimizer {}` in `construct_from_string` is an empty config — all fields come from the previously loaded data.
You can layer multiple sources with different priorities to build up complex configurations from simple, reusable parts.


Error messages
---------------------------------------

Thanks to Pydantic, type errors are caught early with clear messages — before your training run starts, not hours into it:

```{code-cell} python3
---
tags: [raises-exception]
---
try:
    loader.construct_from_string("!Optimizer {lr: 'fast', momentum: 0.9}")
except yaloader.YAMLValueError as e:
    raise e from None
```
