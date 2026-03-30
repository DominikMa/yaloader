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

Variable configs let you create **named presets** for a config class directly in YAML — without writing new Python classes.
This is useful when you want several variations of the same config (e.g. "small", "medium", "large" model sizes).


The `!ConfigVar` prefix
---------------------------------------

Any YAML tag starting with `!ConfigVar` is treated as a variable config. You specify which base config it derives from using the `_tag` field:

```{code-cell} python3
import yaloader

@yaloader.loads()
class OptimizerConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001
    momentum: float = 0.9

loader = yaloader.ConfigLoader()
result = loader.construct_from_string(
    """
    - !Optimizer {lr: 0.01}
    - !ConfigVarSGD {_tag: "!Optimizer", lr: 0.1, momentum: 0.95}
    - !ConfigVarAdam {_tag: "!Optimizer", lr: 0.001}
    """
)
for r in result:
    print(f"lr={r.lr}, momentum={r.momentum}")
```

`!ConfigVarSGD` and `!ConfigVarAdam` are both variants of `!Optimizer` with different default overrides. No new Python class is needed.


Named presets with loading
---------------------------------------

Variable configs become powerful when combined with the loading system. You can define presets in config files and reference them later:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Register a named preset
loader.add_single_config_string("!ConfigVarFastOpt {_tag: '!Optimizer', lr: 0.1, momentum: 0.99}", priority=1)

# Construct using the preset — fields come from the loaded preset
result = loader.construct_from_string("!ConfigVarFastOpt {_tag: '!Optimizer'}")
print(f"lr={result.lr}, momentum={result.momentum}")
```


Chaining variable configs
---------------------------------------

Variable configs can reference other variable configs, creating a chain of presets:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Base preset
loader.add_single_config_string("!ConfigVarBase {_tag: '!Optimizer', lr: 0.05}", priority=1)

# Derived preset — inherits lr from Base, sets momentum
loader.add_single_config_string("!ConfigVarDerived {_tag: '!ConfigVarBase', momentum: 0.99}", priority=1)

result = loader.construct_from_string("!ConfigVarDerived {_tag: '!ConfigVarBase'}")
print(f"lr={result.lr}, momentum={result.momentum}")
```


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
