import datetime
from pathlib import PosixPath, WindowsPath

import yaml
from pydantic import BaseModel


from yaloader.base_config import VarYAMLConfigBase, YAMLBaseConfig

from yaloader.dumper import YAMLConfigDumper
from yaloader.loader import YAMLConfigLoader, YAMLValueError

from yaloader import representer
from yaloader.constructor import get_constructor_for_class, get_multi_constructor_for_vars, loads

from yaloader.config_loader import ConfigLoader

VERSION = '1.0.1'

__all__ = [
    'VERSION',
    'VarYAMLConfigBase',
    'YAMLBaseConfig',
    'YAMLConfigLoader',
    'YAMLValueError',
    'YAMLConfigDumper',
    'get_constructor_for_class',
    'get_multi_constructor_for_vars',
    'loads',
    'representer',
    'ConfigLoader',
]

yaml.add_representer(PosixPath, representer.represent_posix_path, Dumper=YAMLConfigDumper)
yaml.add_representer(WindowsPath, representer.represent_windows_path, Dumper=YAMLConfigDumper)
yaml.add_representer(datetime.timedelta, representer.represent_timedelta, Dumper=YAMLConfigDumper)
yaml.add_multi_representer(BaseModel, representer.represent_base_model, Dumper=YAMLConfigDumper)
