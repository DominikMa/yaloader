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

There are many configuration libraries for Python. Here is how yaloader relates to the most common ones, and when you might prefer it.


At a glance
---------------------------------------

| Feature | yaloader | Hydra | Pydantic Settings | OmegaConf | Gin |
|---|---|---|---|---|---|
| Type-safe configs | Pydantic v2 | Structured Configs (opt.) | Pydantic v2 | Limited | No |
| Object instantiation | `config.load()` | `instantiate(_target_=...)` | No | No | `@gin.configurable` |
| Config inheritance | Python class hierarchy | YAML defaults list | No | No | No |
| Priority merging | Built-in (0–100) | Override grammar | No | `OmegaConf.merge` | No |
| CLI overrides | No | Yes | env vars | No | `--gin_bindings` |
| Experiment tracking | No | No | No | No | No |


vs Hydra
---------------------------------------

[Hydra](https://hydra.cc/) is the most common comparison point. Both tools load YAML configs and instantiate Python objects, but the coupling mechanism differs fundamentally.

**Hydra** uses string-based `_target_` references resolved at runtime:

```yaml
# Hydra config
optimizer:
  _target_: torch.optim.Adam
  lr: 0.001
```

```python
# Hydra instantiation
optimizer = hydra.utils.instantiate(cfg.optimizer)
```

**yaloader** couples at the Python class level:

```python
# yaloader config
@yaloader.loads(torch.optim.Adam)
class AdamConfig(yaloader.YAMLBaseConfig):
    lr: float = 0.001
```

```yaml
# yaloader YAML
- !Adam {lr: 0.001}
```

The key difference: yaloader's `@loads(Adam)` binding is checked by the IDE and type checker. Hydra's `_target_: torch.optim.Adam` is a string that can silently break on rename or import change.

**When to choose Hydra:** You need CLI overrides (`python train.py optimizer.lr=0.01`), multi-run sweeps, or plugin-based experiment launchers. Hydra's ecosystem is large and well-supported.

**When to choose yaloader:** You want type-safe config classes with IDE support, priority-based merging, and Python-native inheritance. You don't need CLI overrides or sweep frameworks.


vs Pydantic Settings
---------------------------------------

[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) manages application settings from environment variables, `.env` files, and other sources. yaloader manages object construction from structured YAML.

These solve different problems and can complement each other:
- Use **Pydantic Settings** for infrastructure and deployment config (database URLs, API keys, feature flags).
- Use **yaloader** for pipeline configuration where configs define complex object hierarchies (models, optimizers, datasets).


vs OmegaConf
---------------------------------------

[OmegaConf](https://omegaconf.readthedocs.io/) provides dict-like config containers with dot access, interpolation, and structured merge semantics. It's the backend powering Hydra.

yaloader provides Pydantic models with full validation and direct object instantiation via `load()`. Where OmegaConf gives you a flexible container you pass around, yaloader gives you typed config objects that create real Python objects.


vs Gin-config
---------------------------------------

[Gin](https://github.com/google/gin-config) by Google binds configuration to functions via decorators. It's lightweight and popular in research code.

The key difference is explicitness: Gin injects config values into function calls implicitly (you call `train()` and Gin fills in the parameters). yaloader constructs config objects explicitly — you construct them, then call `.load()`.

Gin has no type validation. yaloader validates every field via Pydantic v2.


vs Sacred / MLflow
---------------------------------------

[Sacred](https://sacred.readthedocs.io/) and [MLflow](https://mlflow.org/) are experiment tracking frameworks, not configuration libraries. They log parameters, metrics, and artifacts for reproducibility.

yaloader is purely config management — it doesn't track experiments. But the two work well together: use yaloader to build your configs, then dump them to YAML (see {doc}`dumping`) and log the output with Sacred or MLflow.


When to use yaloader
---------------------------------------

yaloader is a good fit when:

- You want configs that know how to create the objects they describe
- You want Pydantic v2 validation on your configs
- You have class hierarchies you want to mirror in config inheritance
- You want layered configs with explicit priority control
- You prefer class-level type safety over string-based references

yaloader is **not** the right tool when:

- You need CLI parameter overrides (consider Hydra)
- You need experiment tracking (consider Sacred or MLflow)
- You need environment-based settings management (consider Pydantic Settings or Dynaconf)
