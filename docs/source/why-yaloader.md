---
jupytext:
    text_representation:
        format_name: myst
kernelspec:
    display_name: Python 3
    name: python3
---

Why yaloader?
=======================================

yaloader is not just another YAML parser. It implements a **Layered Component Registry** pattern for Python. It is designed for applications where you have a hierarchy of interchangeable components and want a clean, type-safe way to configure them.


The Core Philosophies
---------------------------------------

### 1. Late Binding vs. Hardcoded References

Most configuration libraries force you to hardcode your component logic. You either pass dictionaries around manually or use string references (like Hydra's `_target_`).

**yaloader uses Late Binding.** You define your components in Python using the `@yaloader.loads` decorator. When you load a YAML file, yaloader "binds" the configuration data to these components based on their tags. This means your code only asks for a `!Trainer`, and the YAML file decides whether that `!Trainer` uses a `!ResNet` or a `!Transformer`.

### 2. The "Sticky" Explicit Values Rule

In many configuration systems, a "High Priority" document resets everything to its default value. This makes it hard to manage "thin" override layers.

**yaloader tracks whether a field was explicitly set in YAML.**
*   If you set `learning_rate: 0.01` in a base YAML file (Priority 1)...
*   And you set `epochs: 100` in an override YAML file (Priority 10)...
*   The final configuration will have **both** `learning_rate: 0.01` and `epochs: 100`.

Higher priority documents do not reset unrelated fields back to their class defaults. This allows you to stack dozens of specialized configuration layers without losing your baseline settings.

### 3. Isolated State

Each `ConfigLoader` instance has its own isolated registry state and anchor scope. This means you can manage different configuration "worlds" (e.g., one for production, one for testing) in the same Python process without them leaking into each other.


Comparison at a glance
---------------------------------------

| Feature | yaloader | Hydra | OmegaConf | Gin |
|---|---|---|---|---|
| **Type-safe configs** | Pydantic v2 | Optional | Limited | No |
| **Binding Mechanism** | Python Decorators | Runtime Strings | None | Functions |
| **IDE / Refactor support** | Yes | Limited | No | Limited |
| **Merging logic** | Explicit-field tracking | Priority-based | Dict merging | Injection |
| **Late Binding** | Yes | Yes | No | Yes |


vs Hydra
---------------------------------------

Hydra is the closest comparison. While both load YAML and instantiate objects, the coupling differs:

*   **Hydra** uses `_target_: torch.optim.Adam`. This is a string that can break if you rename your class or move your module.
*   **yaloader** uses `@yaloader.loads(Adam)`. This is a direct Python reference. If you rename your class in your IDE, the binding stays intact.

**Choose yaloader if:** You want a clean, Python-native registry where your configurations are validated by Pydantic and your IDE can help you navigate.

**Choose Hydra if:** You need advanced CLI override grammar (`python train.py lr=0.1,0.2,0.5`), multi-run sweeps, or its large ecosystem of launchers.


When to use yaloader
---------------------------------------

yaloader is a good fit when:

*   **Your app is a pipeline of components.** You have various Models, Datasets, and Optimizers that you want to swap easily.
*   **You need layered configuration.** You have "Base defaults", "Machine-specific paths", and "Per-experiment overrides" that you want to stack cleanly.
*   **You want early validation.** You want to know that your config is wrong *before* your heavy application logic starts.
*   **You value IDE support.** You want your configuration classes to be fully typed and discoverable.

yaloader is **not** the right tool when:

*   **You need complex CLI overrides.** yaloader focuses on file-based configuration.
*   **You need experiment tracking.** Use MLflow or Sacred alongside yaloader.
*   **You only need simple environment variables.** Use Pydantic Settings instead.
