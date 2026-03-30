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


Loading methods
---------------------------------------

There are three ways to load config data into a `ConfigLoader`:

```{code-cell} python3
import yaloader

@yaloader.loads()
class ServerConfig(yaloader.YAMLBaseConfig):
    host: str = "localhost"
    port: int = 8080
    workers: int = 4
```

### From a string

```{code-cell} python3
loader = yaloader.ConfigLoader()
loader.load_string(
    """
    - !Server {host: "0.0.0.0", port: 9090}
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
- !Server {host: "0.0.0.0", port: 9090}
- !Server {workers: 8}
```

### Priority document

A dict with a `priority` key (integer 0–100). Sets the priority for all config lists that follow it in the same file:

```yaml
priority: 10
---
- !Server {host: "0.0.0.0"}
```

### Anchors document

A dict with an `anchors` key. The content under `anchors` is arbitrary — it exists only to define YAML anchors for use in later documents (see {doc}`cross-document-anchors`):

```yaml
anchors:
    default_host: &host "0.0.0.0"
---
- !Server {host: *host}
```

A document can combine both `priority` and `anchors`:

```yaml
priority: 10
anchors:
    default_host: &host "0.0.0.0"
---
- !Server {host: *host}
```

No other keys are allowed in dict documents — unexpected keys raise a `ValueError`.
Empty documents (`---` with nothing between them) are silently ignored.


The priority system
---------------------------------------

When multiple configs exist for the same tag, they are merged by priority. Higher priority values win over lower ones.

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Base defaults at priority 0 (the default)
loader.load_string("- !Server {host: localhost, port: 8080, workers: 4}")

# Production overrides at priority 10
loader.load_string("priority: 10\n---\n- !Server {host: '0.0.0.0', workers: 16}")

config = loader.construct_from_string("!Server {}")
print(f"host={config.host}, port={config.port}, workers={config.workers}")
```

The `host` and `workers` come from the priority-10 config, while `port` falls back to the priority-0 default.


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

# Priority 0: sets port explicitly
loader.load_string("- !Server {port: 3000}")

# Priority 10: only sets host explicitly (port not mentioned, stays at default 8080)
loader.load_string("priority: 10\n---\n- !Server {host: production.example.com}")

config = loader.construct_from_string("!Server {}")
print(f"host={config.host}, port={config.port}")
```

Even though the priority-10 config has a higher priority, the `port` from the priority-0 config wins because it was explicitly set, while the priority-10 config's `port` is just the class default.


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
config = loader.construct_from_string("!Server {port: 5000}")
print(config)
```

### `construct_from_file`

Same as above but reads from a file:

```python
config = loader.construct_from_file(Path("serve.yaml"))
```

Both methods merge the given config with all previously loaded data and recursively construct any nested configs.
