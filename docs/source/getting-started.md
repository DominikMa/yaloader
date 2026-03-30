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

Suppose you have a class you want to configure from YAML:

```{code-cell} python3
from dataclasses import dataclass

@dataclass
class User:
    age: int
    name: str
```

Define a configuration class for it:

```{code-cell} python3
import yaloader

@yaloader.loads(User)
class UserConfig(yaloader.YAMLBaseConfig):
    age: int
    name: str
```

The `@yaloader.loads(User)` decorator registers `UserConfig` with the YAML tag `!User` (derived from the class name minus the `Config` suffix) and tells it to create `User` instances when `.load()` is called.


Constructing from YAML
---------------------------------------

Use a `ConfigLoader` to parse YAML and construct the object:

```{code-cell} python3
loader = yaloader.ConfigLoader()
config = loader.construct_from_string("!User {age: 42, name: Alice}")
print(config)
```

The config object holds the validated configuration. Call `.load()` to create the actual `User`:

```{code-cell} python3
user = config.load()
print(user)
```


Lists of configs
---------------------------------------

You can construct multiple configs from a single YAML document:

```{code-cell} python3
loader = yaloader.ConfigLoader()
users = loader.construct_from_string(
    """
    - !User {age: 42, name: Alice}
    - !User {age: 20, name: Bob}
    - !User {age: 12, name: Peter}
    """
)
print(users)
```


Loading and layering
---------------------------------------

The real power of yaloader comes from loading configs from files and merging them.
Here's a quick preview — see {doc}`loading-and-priority` for the full explanation.

```{code-cell} python3
loader = yaloader.ConfigLoader()

# Load a base config
loader.load_string(
    """
    - !User {age: 30, name: Default}
    """
)

# Construct with the loaded defaults
config = loader.construct_from_string("!User {}")
print(config)
```

The `!User {}` in `construct_from_string` is an empty config — all fields come from the previously loaded data.


Error messages
---------------------------------------

Thanks to Pydantic, type errors are caught early with clear messages:

```{code-cell} python3
---
tags: [raises-exception]
---
try:
    loader.construct_from_string("!User {age: 'not a number', name: Alice}")
except yaloader.YAMLValueError as e:
    raise e from None
```
