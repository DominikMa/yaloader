import dataclasses

import yaloader
import yaloader.constructor
from yaloader import YAMLBaseConfig


def test_loads_constructor(yaml_loader, config_loader):
    @dataclasses.dataclass
    class Class:
        attribute: int

    @yaloader.constructor.loads(loaded_class=Class, yaml_loader=yaml_loader)
    class ClassConfig(YAMLBaseConfig):
        attribute: int = 0

    config = config_loader.construct_from_string("!Class {attribute: 1}")
    klass = config.load()
    assert isinstance(klass, Class)
