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


Basic dumping
---------------------------------------

Any config registered with `@yaloader.loads` can be dumped:

```{code-cell} python3
import yaml
import yaloader

@yaloader.loads()
class ServerConfig(yaloader.YAMLBaseConfig):
    host: str = "localhost"
    port: int = 8080
    workers: int = 4

config = ServerConfig(host="0.0.0.0", port=9090, workers=4)
print(yaml.dump(config, Dumper=yaloader.YAMLConfigDumper))
```

By default, the dumper excludes fields that are unset or at their default value, keeping the output minimal.


Controlling which fields are dumped
---------------------------------------

`YAMLConfigDumper` has two class attributes that control output:

- `exclude_unset` (default `True`) — exclude fields that weren't explicitly set
- `exclude_defaults` (default `True`) — exclude fields whose value equals the default

### Include all fields

To dump every field, create a dumper subclass with both flags set to `False`:

```{code-cell} python3
class FullDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = False

config = ServerConfig(host="0.0.0.0")
print(yaml.dump(config, Dumper=FullDumper))
```

### Exclude only defaults

```{code-cell} python3
class NoDefaultsDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = True

config = ServerConfig(host="0.0.0.0", port=8080)
print(yaml.dump(config, Dumper=NoDefaultsDumper))
```

Here `port=8080` matches the default, so it's excluded. `host` was explicitly set to a non-default value, so it's included.


Nested configs
---------------------------------------

Nested config objects are dumped with their own YAML tags:

```{code-cell} python3
class FullDumper(yaloader.YAMLConfigDumper):
    exclude_unset = False
    exclude_defaults = False

@yaloader.loads()
class CacheConfig(yaloader.YAMLBaseConfig):
    ttl: int = 300

@yaloader.loads(yaml_dumper=FullDumper)
class AppConfig(yaloader.YAMLBaseConfig):
    name: str = "myapp"
    cache: CacheConfig = CacheConfig()

config = AppConfig(name="prod", cache=CacheConfig(ttl=600))
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
