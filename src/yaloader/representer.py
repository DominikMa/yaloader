from __future__ import annotations

import datetime
from pathlib import PosixPath, WindowsPath
from typing import Type

from pydantic import BaseModel

from yaloader import YAMLConfigDumper, YAMLBaseConfig


def represent_posix_path(dumper: YAMLConfigDumper, data: PosixPath):
    return dumper.represent_str(str(data.absolute()))


def represent_windows_path(dumper: YAMLConfigDumper, data: WindowsPath):
    return dumper.represent_str(str(data.absolute()))


def represent_timedelta(dumper: YAMLConfigDumper, data: datetime.timedelta):
    return dumper.represent_str(str(data))


def represent_base_model(dumper: YAMLConfigDumper, data: BaseModel):
    return dumper.represent_dict(data.model_dump())


def get_representer_for_class(cls: Type[YAMLBaseConfig]):
    def represent_config(dumper: YAMLConfigDumper, data: YAMLBaseConfig):
        """Represent the config object as a mapping."""
        # Get all keys which should be dumped
        keys = set(
            data.model_dump(
                exclude_unset=dumper.exclude_unset,
                exclude_defaults=dumper.exclude_defaults,
            ).keys()
        )

        # Just for sorting the output:
        # Get keys of iteration types
        it_keys = set(
            filter(lambda k: isinstance(getattr(data, k), (list, tuple, dict)), keys)
        )
        keys = keys.difference(it_keys)

        # Get keys of BaseConfig type
        config_objects_keys = set(
            filter(lambda key: isinstance(getattr(data, key), YAMLBaseConfig), keys)
        )
        keys = keys.difference(config_objects_keys)

        dump_dict = {
            k: getattr(data, k)
            for k in sorted(keys) + sorted(it_keys) + sorted(config_objects_keys)
        }
        return dumper.represent_mapping(cls.get_yaml_tag(), dump_dict)

    return represent_config
