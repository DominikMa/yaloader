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

