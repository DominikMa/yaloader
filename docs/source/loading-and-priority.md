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

yaloader separates **loading** (collecting config data) from **construction** (merging and building the final config). This page covers the merging logic and the priority system.

In a typical ML project, configs come from multiple sources: base defaults, dataset-specific settings, machine-specific paths, and debug overrides. yaloader's priority system lets you layer these naturally.


The "Explicit vs. Default" Rule
---------------------------------------

This is the most important technical detail of yaloader's merging logic. **Explicitly typed fields in YAML always take precedence over default values in the Python class, regardless of priority.**

Consider this `ModelConfig`:

```{code-cell} python3
import yaloader

@yaloader.loads()
class ModelConfig(yaloader.YAMLBaseConfig):
    layers: int = 50
    hidden_dim: int = 512
```

### Scenario: Stacking Overrides

Imagine you have a "Base" config (Priority 1) and a "Specific Experiment" config (Priority 10).

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Layer 1: The Base defaults (Priority 1)
# We explicitly set `layers: 101`.
loader.load_string("""
priority: 1
---
- !Model {layers: 101}
""")

# Layer 2: The Specific Experiment (Priority 10)
# We only want to override `hidden_dim: 1024`.
# We DO NOT mention `layers` here.
loader.load_string("""
priority: 10
---
- !Model {hidden_dim: 1024}
""")

# Construct the config
config = loader.construct_from_string("!Model {}")
print(f"Final Layers: {config.layers}")
print(f"Final Hidden Dim: {config.hidden_dim}")
```

#### What happened here?
1.  **Layers (101):** Even though the Priority 10 document is "more important," it didn't mention `layers`. yaloader looks at the Priority 1 document, sees that `layers: 101` was **explicitly typed in YAML**, and uses it. It ignores the Priority 10's *implicit* default of 50.
2.  **Hidden Dim (1024):** The Priority 10 document explicitly sets `hidden_dim: 1024`, which wins over the class default of 512.

### Summary Table: Who wins?

| Source A (Prio 1) | Source B (Prio 10) | Result | Logic |
|---|---|---|---|
| Explicit (101) | *Not Mentioned* | **101** | Explicit always beats Class Default |
| *Not Mentioned* | Explicit (202) | **202** | Explicit beats Class Default |
| Explicit (101) | Explicit (202) | **202** | Higher priority explicit wins |
| *Not Mentioned* | *Not Mentioned* | **50** | Fallback to Class Default |


Loading Methods
---------------------------------------

You can load data from strings, files, or entire directories:

```python
loader = yaloader.ConfigLoader()

# Individual strings
loader.load_string("- !Model {layers: 101}")

# Single YAML files
loader.load_file(Path("configs/base.yaml"))

# All .yaml files in a directory (sorted alphabetically)
loader.load_directory(Path("configs/experiments/"))
```

### Passing priority directly

Instead of using a `priority:` document inside YAML, you can pass it as an argument:

```python
# Force this file to have very high priority
loader.load_file(Path("debug_overrides.yaml"), priority=99)
```


Structuring your Configs
---------------------------------------

A common pattern for complex projects is to load them in layers:

1.  **Base Layer (Prio 1):** Shared defaults for all components.
2.  **Environment Layer (Prio 5):** Machine-specific paths, GPU counts, etc.
3.  **Experiment Layer (Prio 10):** The specific hyperparameters for a run.
4.  **Runtime Overrides (Prio 99):** Quick debug settings (e.g., `epochs: 1`).

This structure ensures that you only ever need to type the *differences* in each file.
