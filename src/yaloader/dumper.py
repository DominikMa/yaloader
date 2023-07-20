from __future__ import annotations

import yaml


class YAMLConfigDumper(yaml.SafeDumper):
    """YAML dumper for the configs."""

    exclude_unset: bool = True
    """If True exclude all unset values when dumping the config. 
    See https://pydantic-docs.helpmanual.io/usage/exporting_models/ for details."""
    exclude_defaults: bool = True
    """If True exclude all default values when dumping the config.
    See https://pydantic-docs.helpmanual.io/usage/exporting_models/ for details."""
