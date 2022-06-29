import pytest

from yaloader import YAMLBaseConfig
from yaloader.utils import full_object_name


@pytest.fixture
def BConfig(yaml_loader, AConfig):

    class Config(AConfig, overwrite_tag=True, yaml_loader=yaml_loader):
        _yaml_tag = "!A"

    return Config


def test_loading_subclass(config_loader, AConfig, BConfig):
    config = config_loader.deep_construct_from_config(BConfig(), final=True)
    assert type(config) != AConfig
    assert type(config) == BConfig


def test_error_on_standard_tag(yaml_loader):

    with pytest.raises(RuntimeError) as error:
        class Config(YAMLBaseConfig, yaml_loader=yaml_loader):
            _yaml_tag = "!!str"

    assert str(error.value).startswith(f"The tag !!str has the prefix !! and can therefore not be used")


def test_error_on_existing_tag(yaml_loader):
    yaml_loader.add_constructor('!A', lambda _: None)

    with pytest.raises(RuntimeError) as error:
        class Config(YAMLBaseConfig, yaml_loader=yaml_loader):
            _yaml_tag = "!A"

    assert str(error.value).startswith(f"The tag !A is already registered and can not be used")


def test_error_on_registered_tag(yaml_loader, AConfig):

    with pytest.raises(RuntimeError) as error:
        class Config(YAMLBaseConfig, overwrite_tag=False, yaml_loader=yaml_loader):
            _yaml_tag = "!A"

    assert str(error.value).startswith(f"The tag !A is already registered by {full_object_name(AConfig)}")
