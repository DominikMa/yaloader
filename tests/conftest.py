import pytest

from yaloader import YAMLConfigLoader, ConfigLoader


@pytest.fixture
def empty_yaml_loader():
    class EmptyYAMLConfigLoader(YAMLConfigLoader):
        pass

    return EmptyYAMLConfigLoader


@pytest.fixture
def empty_config_loader(empty_yaml_loader):
    config_loader = ConfigLoader(yaml_loader=empty_yaml_loader)
    return config_loader
