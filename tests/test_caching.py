import timeit

import pydantic
import pytest

import yaloader
import yaloader.constructor
from yaloader import YAMLBaseConfig, ConfigLoader


@pytest.fixture
def large_config_list(yaml_loader, config_loader):
    @yaloader.loads(yaml_loader=yaml_loader)
    class BaseConfig(YAMLBaseConfig):
        def load(self, *args, **kwargs):
            return self.get_yaml_tag()

    config_list = []
    for i in range(10):
        base_config_index = int(i / 10)
        if base_config_index == 0:
            base_config = BaseConfig
        else:
            base_config = config_list[base_config_index]

        field_definitions = {f"attribute{j}": (int, int(j)) if (j + i) % 2 == 0 else (str, str(j)) for j in
                             range(min(i, 20))}
        field_definitions["_yaml_tag"] = f'!Config{i}'

        config_class = pydantic.create_model(
            __model_name=f'Config{i}Config',
            __base__=base_config,
            **field_definitions
        )
        config_class = yaloader.constructor.loads(yaml_loader=yaml_loader)(config_class)
        config_list.append(config_class)

    return config_list


@pytest.fixture
def caching_config_loader(yaml_loader):
    config_loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=True)
    return config_loader


@pytest.mark.long
def test_caching_speed_load_large_config_list(config_loader, caching_config_loader, large_config_list):
    load_strings = []
    for config in large_config_list:
        load_strings.append(f"- {config.get_yaml_tag()} {{}}")

    load_string = '\n'.join(load_strings)

    time_with_cache = timeit.timeit("config_loader.construct_from_string(load_string)", number=20, globals={
        'load_string': load_string,
        'config_loader': caching_config_loader
    })

    time_without_cache = timeit.timeit("config_loader.construct_from_string(load_string)", number=20, globals={
        'load_string': load_string,
        'config_loader': config_loader
    })

    time_without_cache += timeit.timeit("config_loader.construct_from_string(load_string)", number=20, globals={
        'load_string': load_string,
        'config_loader': config_loader
    })

    time_with_cache += timeit.timeit("config_loader.construct_from_string(load_string)", number=20, globals={
        'load_string': load_string,
        'config_loader': caching_config_loader
    })

    assert time_without_cache > time_with_cache


@pytest.mark.long
def test_caching_load_large_config_list(config_loader, caching_config_loader, large_config_list):
    load_strings = []
    for config in large_config_list:
        load_strings.append(f"- {config.get_yaml_tag()} {{}}")

    load_string = '\n'.join(load_strings)

    config_list = config_loader.construct_from_string(load_string)
    config_list_cached = caching_config_loader.construct_from_string(load_string)

    assert config_list == config_list_cached
