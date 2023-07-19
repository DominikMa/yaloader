import pytest

from yaloader import YAMLConfigLoader, ConfigLoader, YAMLBaseConfig
import yaloader


@pytest.fixture
def yaml_loader():
    class EmptyYAMLConfigLoader(YAMLConfigLoader):
        pass

    return EmptyYAMLConfigLoader


@pytest.fixture
def config_loader(yaml_loader):
    config_loader = ConfigLoader(yaml_loader=yaml_loader)
    return config_loader


@pytest.fixture
def AConfig(yaml_loader, config_loader):

    @yaloader.loads(yaml_loader=yaml_loader)
    class Config(YAMLBaseConfig):
        _yaml_tag = '!A'
        attribute: int = 0

        def load(self, *args, **kwargs):
            return self.attribute

    return Config
