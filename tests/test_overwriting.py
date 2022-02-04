import pytest


@pytest.fixture
def BConfig(yaml_loader, AConfig):

    class Config(AConfig, overwrite_tag=True, yaml_loader=yaml_loader):
        _yaml_tag = "!A"

    return Config


def test_loading_subclass(config_loader, AConfig, BConfig):
    config = config_loader.deep_construct_from_config(BConfig(), final=True)
    assert type(config) != AConfig
    assert type(config) == BConfig
