import dataclasses
import json
from typing import Any, Generic

import pytest
import yaml
from typing_extensions import TypeVar

from yaloader import YAMLBaseConfig, YAMLConfigDumper, loads


@dataclasses.dataclass
class LoadedValue:
    value: int


_Result = TypeVar("_Result", default=Any)


@pytest.mark.parametrize("register_specialization", [False, True])
@pytest.mark.parametrize("inherited", [False, True])
def test_specialized_generic_parent_registration(yaml_loader, config_loader, register_specialization, inherited):
    @loads(yaml_loader=yaml_loader, yaml_dumper=None)
    class GenericParentConfig(YAMLBaseConfig[_Result], Generic[_Result]):
        value: int = 1

    specialized_parent = GenericParentConfig[LoadedValue]
    assert specialized_parent not in yaml_loader.yaml_config_classes.values()

    if register_specialization:
        specialized_parent.set_yaml_tag("!SpecializedParent")
        loads(yaml_loader=yaml_loader, yaml_dumper=None)(specialized_parent)

    @loads(LoadedValue, yaml_loader=yaml_loader, yaml_dumper=None)
    class ChildConfig(specialized_parent):
        value: int = 2

    @loads(yaml_loader=yaml_loader, yaml_dumper=None)
    class GrandChildConfig(ChildConfig):
        pass

    config_loader.load_string("- !GenericParent {value: 7}")
    if register_specialization:
        config_loader.load_string("- !SpecializedParent {value: 9}")

    config_class = GrandChildConfig if inherited else ChildConfig
    config = config_loader.construct_from_string(f"{config_class.get_yaml_tag()} {{}}")
    assert type(config) is config_class
    assert config.load() == LoadedValue(value=9 if register_specialization else 7)
    if not register_specialization:
        assert specialized_parent not in yaml_loader.yaml_config_classes.values()


def test_specialized_generic_parent_requires_registered_origin(yaml_loader, config_loader):
    class UnregisteredParentConfig(YAMLBaseConfig[_Result], Generic[_Result]):
        value: int = 1

    @loads(LoadedValue, yaml_loader=yaml_loader, yaml_dumper=None)
    class ChildConfig(UnregisteredParentConfig[LoadedValue]):
        pass

    with pytest.raises(RuntimeError, match="no config is registered for that tag"):
        config_loader.construct_from_string("!Child {}")


@pytest.mark.parametrize("typed", [False, True])
@pytest.mark.parametrize("inherited", [False, True])
def test_generic_default_load_and_yaml_round_trip(yaml_loader, config_loader, typed, inherited):
    base = YAMLBaseConfig[LoadedValue] if typed else YAMLBaseConfig
    dumper = type("TestDumper", (YAMLConfigDumper,), {})

    @loads(LoadedValue, yaml_loader=yaml_loader, yaml_dumper=dumper)
    class ValueConfig(base):
        value: int = 1

    @loads(yaml_loader=yaml_loader, yaml_dumper=dumper)
    class ChildValueConfig(ValueConfig):
        value: int = 2

    config_class = ChildValueConfig if inherited else ValueConfig
    config = config_class(value=42)
    assert config_class.load is YAMLBaseConfig.load
    assert config.load() == LoadedValue(value=42)
    assert config_class().load() == LoadedValue(value=2 if inherited else 1)
    assert config.get_yaml_tag() == ("!ChildValue" if inherited else "!Value")

    assert set(config_class.model_fields) == {"value"}
    assert dict(config) == {"value": 42}
    assert config.model_dump() == {"value": 42}
    assert json.loads(config.model_dump_json()) == {"value": 42}
    output = yaml.dump(config, Dumper=dumper)
    assert "_loaded_class" not in output
    restored = yaml.load(output, Loader=yaml_loader)
    assert type(restored) is config_class
    assert restored.model_dump() == {"value": 42}
    assert restored.load() == LoadedValue(value=42)

    config_loader.load_string("- !Value {value: 7}")
    constructed = config_loader.construct_from_string(f"{config.get_yaml_tag()} {{}}")
    assert type(constructed) is config_class
    assert constructed.load() == LoadedValue(value=7)

    variable = config_loader.construct_from_string(f"!ConfigVarValue {{_tag: '{config.get_yaml_tag()}', value: 11}}")
    assert type(variable) is config_class
    assert variable.load() == LoadedValue(value=11)


@pytest.mark.parametrize("typed", [False, True])
def test_generic_missing_constructor_raises(typed):
    base = YAMLBaseConfig[LoadedValue] if typed else YAMLBaseConfig

    @loads(yaml_loader=None, yaml_dumper=None)
    class MissingConstructorConfig(base):
        value: int = 1

    with pytest.raises(NotImplementedError):
        MissingConstructorConfig().load()


def test_generic_custom_and_inherited_load(yaml_loader):
    @loads(yaml_loader=yaml_loader, yaml_dumper=None)
    class CustomValueConfig(YAMLBaseConfig[LoadedValue]):
        value: int = 1

        def load(self, offset: int = 0) -> LoadedValue:
            return LoadedValue(value=self.value + offset)

    @loads(yaml_loader=yaml_loader, yaml_dumper=None)
    class InheritedValueConfig(CustomValueConfig):
        value: int = 2

    @loads(yaml_loader=yaml_loader, yaml_dumper=None)
    class OverrideValueConfig(InheritedValueConfig):
        def load(self, offset: int = 0) -> LoadedValue:
            return LoadedValue(value=self.value * 2 + offset)

    assert CustomValueConfig().load(offset=10) == LoadedValue(value=11)
    assert InheritedValueConfig.load is CustomValueConfig.load
    assert InheritedValueConfig().load(offset=10) == LoadedValue(value=12)
    assert OverrideValueConfig().load(offset=10) == LoadedValue(value=14)


def test_generic_custom_load_controls_result_with_registered_constructor():
    @loads(dict, yaml_loader=None, yaml_dumper=None)
    class CustomValueConfig(YAMLBaseConfig[LoadedValue]):
        value: int = 3

        def load(self) -> LoadedValue:
            return LoadedValue(value=self.value)

    assert CustomValueConfig().load() == LoadedValue(value=3)
