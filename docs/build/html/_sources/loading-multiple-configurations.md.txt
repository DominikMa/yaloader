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

Loading multiple configurations
=======================================


Installation
---------------------------------------


Basic Examples
---------------------------------------

### Loading a class

Consider you have any class, and you want to configure and load it though a yaml file.
For example a dataclass of a user:

```{code-cell} python3
---
tags: [show-input]
---
from dataclasses import dataclass
from typing import Any

@dataclass
class User:
    age: int
    name: str
```

To load it from yaml, you first have to define its configuration.
```{code-cell} python3
---
tags: [show-input]
---
import yaloader
    
@yaloader.loads(User)
class UserConfig(yaloader.YAMLBaseConfig):
    age: int
    name: str
```

Now a loader can be used to load a string or file holding the classes' configuration.
```{code-cell} python3
---
tags: [show-input]
---
loader = yaloader.ConfigLoader()
user_config = loader.construct_from_string("!User {age: 42, name: Alice}")
print(type(user_config))
print(user_config)
```

`user_config` now holds the configuration of the user.
The user itself can be loaded using the `user_config.load()` method. 
```{code-cell} python3
---
tags: [show-input]
---
user = user_config.load()
print(type(user))
print(user)
```


The loading is not limited to single configurations. Every valid YAML file, containing `!User` tags is fine.
```{code-cell} python3
---
tags: [show-input]
---
loader = yaloader.ConfigLoader()
all_user_configs = loader.construct_from_string(
    """
    - !User {age: 42, name: Alice}
    - !User {age: 20, name: Bob}
    - !User {age: 12, name: Peter}
    """
)
print(all_user_configs)
```

### Adding multiple configurations to the loader
The configuration loader allows you to add multiple configurations for the same tag
which will be layered while construction.




### Error messages
Thanks to pydantic you also get nice error messages when an incorrect configuration will be loaded.
```{code-cell} python3
---
tags: [show-input, raises-exception]
---
try:
    loader.construct_from_string("!User {age: 'Not an int', name: Alice}")
except yaloader.YAMLValueError as e:
    raise e from None
```
