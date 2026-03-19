"""Tests for YAMLConfigDumper, representers, and YAML serialization."""

import datetime
from pathlib import Path

import yaml

import yaloader.constructor
from yaloader import YAMLBaseConfig, YAMLConfigDumper


def test_dump_simple_config(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class SimpleConfig(YAMLBaseConfig):
        _yaml_tag = "!Simple"
        value: int = 0

    config = SimpleConfig(value=42)
    output = yaml.dump(config, Dumper=dumper_class)
    assert "!Simple" in output
    assert "value: 42" in output


def test_dump_exclude_defaults(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_defaults": True, "exclude_unset": False})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class DefaultsConfig(YAMLBaseConfig):
        _yaml_tag = "!Defaults"
        a: int = 0
        b: int = 10

    config = DefaultsConfig(a=5, b=10)
    output = yaml.dump(config, Dumper=dumper_class)
    assert "a: 5" in output
    # b=10 is the default, so it should be excluded
    assert "b:" not in output


def test_dump_exclude_unset(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_unset": True, "exclude_defaults": False})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class UnsetConfig(YAMLBaseConfig):
        _yaml_tag = "!Unset"
        a: int = 0
        b: int = 10

    config = UnsetConfig(a=5)
    output = yaml.dump(config, Dumper=dumper_class)
    assert "a: 5" in output
    # b was not set, should be excluded
    assert "b:" not in output


def test_dump_no_excludes(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_unset": False, "exclude_defaults": False})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class AllConfig(YAMLBaseConfig):
        _yaml_tag = "!All"
        a: int = 0
        b: int = 10

    config = AllConfig(a=5)
    output = yaml.dump(config, Dumper=dumper_class)
    assert "a: 5" in output
    assert "b: 10" in output


def test_dump_with_list_and_dict_fields(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_unset": False, "exclude_defaults": False})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class CollectionConfig(YAMLBaseConfig):
        _yaml_tag = "!Collection"
        name: str = "test"
        items: list[int] = [1, 2, 3]  # noqa: RUF012
        mapping: dict[str, int] = {"x": 1}  # noqa: RUF012

    config = CollectionConfig()
    output = yaml.dump(config, Dumper=dumper_class)
    assert "!Collection" in output
    assert "name:" in output
    assert "items:" in output
    assert "mapping:" in output


def test_dump_nested_config(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_unset": False, "exclude_defaults": False})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class InnerConfig(YAMLBaseConfig):
        _yaml_tag = "!Inner"
        x: int = 1

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class OuterConfig(YAMLBaseConfig):
        _yaml_tag = "!Outer"
        name: str = "outer"
        inner: InnerConfig = InnerConfig()

    config = OuterConfig(inner=InnerConfig(x=5))
    output = yaml.dump(config, Dumper=dumper_class)
    assert "!Outer" in output
    assert "!Inner" in output
    assert "name:" in output
    assert "inner:" in output


def test_represent_timedelta(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_unset": False, "exclude_defaults": False})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class TimedeltaConfig(YAMLBaseConfig):
        _yaml_tag = "!TD"
        duration: datetime.timedelta = datetime.timedelta(seconds=0)

    config = TimedeltaConfig(duration=datetime.timedelta(hours=1, minutes=30))
    output = yaml.dump(config, Dumper=dumper_class)
    assert "1:30:00" in output


def test_represent_posix_path(yaml_loader):
    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_unset": False, "exclude_defaults": False})

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class PathConfig(YAMLBaseConfig):
        _yaml_tag = "!PathCfg"
        path: Path = Path("/tmp")

    config = PathConfig(path=Path("/tmp/test"))
    output = yaml.dump(config, Dumper=dumper_class)
    assert "/tmp/test" in output


def test_represent_base_model(yaml_loader):
    """Test that plain BaseModel fields are dumped as dicts."""
    from pydantic import BaseModel

    dumper_class = type("TestDumper", (YAMLConfigDumper,), {"exclude_unset": False, "exclude_defaults": False})

    # Register BaseModel representer
    from yaloader.representer import represent_base_model

    dumper_class.add_representer(BaseModel, represent_base_model)

    @yaloader.constructor.loads(yaml_loader=yaml_loader, yaml_dumper=dumper_class)
    class ModelConfig(YAMLBaseConfig):
        _yaml_tag = "!ModelCfg"
        value: int = 0

    config = ModelConfig(value=3)
    output = yaml.dump(config, Dumper=dumper_class)
    assert "value: 3" in output
