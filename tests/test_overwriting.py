import pytest

from src.yaloader import YAMLBaseConfig


@pytest.fixture
def simple_base_class(empty_yaml_loader):

    class AConfig(YAMLBaseConfig, yaml_loader=empty_yaml_loader):
        attribute_int: int = 0

        def load(self, *args, **kwargs):
            pass

    return AConfig


@pytest.fixture
def simple_sub_class(simple_base_class, empty_yaml_loader):

    class BConfig(simple_base_class, overwrite_tag=True, yaml_loader=empty_yaml_loader):
        _yaml_tag = "!A"

        def load(self, *args, **kwargs):
            pass

    return BConfig


def test_loading_subclass(simple_sub_class, empty_config_loader):
    config = empty_config_loader.deep_construct_from_config(simple_sub_class(), final=True)
    assert isinstance(config, simple_sub_class)
