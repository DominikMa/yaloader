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

Dumping
=======================================

yaloader can serialize config objects back to YAML using `YAMLConfigDumper`.

After training, serialize your resolved config to YAML and save it alongside your model checkpoint. This ensures every experiment is fully reproducible — you know exactly which hyperparameters produced each result.


Basic dumping
---------------------------------------

Any config registered with `@yaloader.loads` can be dumped:

```{code-cell} python3
import yaml
import yaloader

@yaloader.loads()
class TrainingConfig(yaloader.YAMLBaseConfig):
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001

config = TrainingConfig(epochs=200, batch_size=128, learning_rate=0.001)
print(yaml.dump(config, Dumper=yaloader.YAMLConfigDumper))
```

By default, the dumper excludes fields that are unset or at their default value, keeping the output minimal.


Controlling which fields are dumped
---------------------------------------

`YAMLConfigDumper` has two class attributes that control output:

- `exclude_unset` (default `True`) — exclude fields that weren't explicitly set
- `exclude_defaults` (default `True`) — exclude fields whose value equals the default

### Include all fields

To dump every field — useful for creating a complete snapshot of your experiment config — create a dumper subclass with both flags set to `False`:

```{code-cell} python3
class FullDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = False

config = TrainingConfig(epochs=200)
print(yaml.dump(config, Dumper=FullDumper))
```

### Exclude only defaults

```{code-cell} python3
class NoDefaultsDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = True

config = TrainingConfig(epochs=200, batch_size=32)
print(yaml.dump(config, Dumper=NoDefaultsDumper))
```

Here `batch_size=32` matches the default, so it's excluded. `epochs` was explicitly set to a non-default value, so it's included.


Round-trip: dump and reload
---------------------------------------

A key use case is round-tripping: dump a resolved config after construction, then reload it to reproduce the exact same setup.

```{code-cell} python3
class FullDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = False

# Construct a config from merged sources
loader = yaloader.ConfigLoader()
loader.load_string("- !Training {epochs: 100}")
loader.load_string(r"""
priority: 10
---
- !Training {batch_size: 256}
""")
original = loader.construct_from_string("!Training {learning_rate: 0.01}")

# Dump to YAML
dumped = yaml.dump(original, Dumper=FullDumper)
print("Dumped config:")
print(dumped)

# Reload from the dumped YAML
loader2 = yaloader.ConfigLoader()
restored = loader2.construct_from_string(dumped)
print(f"Restored: epochs={restored.epochs}, batch_size={restored.batch_size}, lr={restored.learning_rate}")
```

This makes it easy to save your exact experiment configuration alongside model checkpoints and recreate the setup later.


Nested configs
---------------------------------------

Nested config objects are dumped with their own YAML tags:

```{code-cell} python3
class FullDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = False

@yaloader.loads()
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001

@yaloader.loads(yaml_dumper=FullDumper)
class ExperimentConfig(yaloader.YAMLBaseConfig):
    name: str = "baseline"
    optimizer: OptimizerConfig = OptimizerConfig()

config = ExperimentConfig(name="exp_001", optimizer=OptimizerConfig(lr=0.01))
print(yaml.dump(config, Dumper=FullDumper))
```


Supported types
---------------------------------------

The dumper handles these types automatically:

- **Basic types**: `int`, `str`, `float`, `bool`
- **Collections**: `list`, `tuple`, `dict`
- **Paths**: `PosixPath`, `WindowsPath` (dumped as absolute path strings)
- **Dates**: `datetime.timedelta` (dumped as string)
- **Pydantic models**: `BaseModel` subclasses (dumped as dicts)
- **Config objects**: `YAMLBaseConfig` subclasses (dumped with their YAML tag)
