import dataclasses

import pytest

from yaloader import YAMLBaseConfig


def test_unset_tag(yaml_loader):
    class XYZConfig(YAMLBaseConfig, yaml_loader=yaml_loader):
        attribute: int = 0

    assert XYZConfig.get_yaml_tag() == '!XYZ'


def test_set_tag(yaml_loader):
    class XYZConfig(YAMLBaseConfig, yaml_loader=yaml_loader):
        _yaml_tag = "!ABC"
        attribute: int = 0

    assert XYZConfig.get_yaml_tag() == '!ABC'


def test_raise_on_missing_tag(yaml_loader):
    with pytest.raises(RuntimeError) as error:
        class ConfigA(YAMLBaseConfig, yaml_loader=yaml_loader):
            attribute: int = 0

    assert str(error.value) == "Config class ConfigA has not yaml tag. " \
                               "If the tag should be derived automatically the class name has to end with `Config`"


def test_raise_on_wrong_tag_prefix(yaml_loader):
    with pytest.raises(RuntimeError) as error:
        class ConfigA(YAMLBaseConfig, yaml_loader=yaml_loader):
            _yaml_tag = "A"
            attribute: int = 0

    assert str(error.value).endswith('does not start with !')


def test_loaded_class_argument(yaml_loader, config_loader):
    @dataclasses.dataclass
    class Class:
        attribute: int

    class ClassConfig(YAMLBaseConfig, loaded_class=Class, yaml_loader=yaml_loader):
        attribute: int = 0

    config = config_loader.construct_from_string("!Class {attribute: 1}")
    klass = config.load()
    assert isinstance(klass, Class)


def test_loaded_class_argument_auto_load(yaml_loader, config_loader):
    @dataclasses.dataclass
    class Class:
        attribute: int

    class ClassConfig(YAMLBaseConfig, loaded_class=Class, yaml_loader=yaml_loader):
        attribute: int = 0

    klass = config_loader.construct_from_string("!Class {attribute: 1}", auto_load=True)
    assert isinstance(klass, Class)


def test_no_loaded_class_argument_raises(yaml_loader, config_loader):
    class ClassConfig(YAMLBaseConfig, yaml_loader=yaml_loader):
        attribute: int = 0

    config = config_loader.construct_from_string("!Class {attribute: 1}")
    with pytest.raises(NotImplementedError) as error:
        klass = config.load()
