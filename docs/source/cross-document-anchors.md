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


Anchors within a file
---------------------------------------

Use an `anchors` document to define anchors, then reference them in config lists that follow:

```{code-cell} python3
import yaloader

@yaloader.loads()
class DBConfig(yaloader.YAMLBaseConfig):
    host: str = "localhost"
    port: int = 5432

loader = yaloader.ConfigLoader()
loader.load_string("anchors:\n  prod_host: &host db.production.internal\n  prod_port: &port 5433\n---\n- !DB {host: *host, port: *port}")

config = loader.construct_from_string("!DB {}")
print(f"host={config.host}, port={config.port}")
```

The `anchors` document is a dict with an `anchors` key. Its content can be any YAML structure — it exists only so the YAML parser registers the anchors.


Anchors across load calls
---------------------------------------

Anchors defined in one `load_string` call are available in subsequent calls on the **same** `ConfigLoader`:

```{code-cell} python3
loader = yaloader.ConfigLoader()

# First call: define anchors
loader.load_string("anchors:\n  shared_host: &host shared.internal")

# Second call: use them
loader.load_string("- !DB {host: *host}")

config = loader.construct_from_string("!DB {}")
print(f"host={config.host}")
```


Isolation between loaders
---------------------------------------

Each `ConfigLoader` instance has its own anchor scope. Anchors from one loader do not leak into another:

```{code-cell} python3
loader_a = yaloader.ConfigLoader()
loader_a.load_string("anchors:\n  value: &val 42")

loader_b = yaloader.ConfigLoader()
# loader_b does NOT have access to &val from loader_a
```

This means you can safely use multiple `ConfigLoader` instances without worrying about name collisions.


Anchors in `construct_from_string`
---------------------------------------

Anchors can also be defined inline when constructing:

```{code-cell} python3
loader = yaloader.ConfigLoader()
result = loader.construct_from_string(
    """
    - !DB {host: &h "inline.host", port: 5432}
    - !DB {host: *h, port: 5433}
    """
)
for r in result:
    print(f"host={r.host}, port={r.port}")
```
