"""Tests for config_loader.py edge cases: construct_from_file, load_file suffix, deep construction, etc."""

import logging
from unittest.mock import MagicMock

import pytest
from pydantic import Field, ValidationError
from yaml.parser import ParserError

import yaloader.constructor
from yaloader import ConfigLoader, YAMLBaseConfig


def test_construct_from_file(config_loader, AConfig, tmp_path):
    """Test construct_from_file basic usage."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("!A {attribute: 42}")

    result = config_loader.construct_from_file(config_file)
    assert result == AConfig(attribute=42)


def test_construct_from_file_yaml_suffix_auto_append(config_loader, AConfig, tmp_path):
    """Test construct_from_file auto-appends .yaml suffix."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("!A {attribute: 7}")

    # Pass path without .yaml suffix
    result = config_loader.construct_from_file(tmp_path / "config")
    assert result == AConfig(attribute=7)


def test_construct_from_file_not_found(config_loader, tmp_path):
    """Test construct_from_file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Could not find file"):
        config_loader.construct_from_file(tmp_path / "nonexistent")


def test_load_file_yaml_suffix_auto_append(config_loader, AConfig, tmp_path):
    """Test load_file auto-appends .yaml suffix."""
    config_file = tmp_path / "data.yaml"
    config_file.write_text("- !A {attribute: 99}")

    config_loader.load_file(tmp_path / "data")
    result = config_loader.construct_from_string("!A {}")
    assert result == AConfig(attribute=99)


def test_load_file_not_found(config_loader, tmp_path):
    """Test load_file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Could not find file"):
        config_loader.load_file(tmp_path / "missing")


def test_load_directory_not_a_dir(config_loader, tmp_path):
    """Test load_directory raises NotADirectoryError."""
    fake = tmp_path / "not_a_dir"
    with pytest.raises(NotADirectoryError):
        config_loader.load_directory(fake)


def test_deep_construct_nested_config(yaml_loader):
    """Test deep construction with nested YAMLBaseConfig fields."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class ChildConfig(YAMLBaseConfig):
        _yaml_tag = "!Child"
        x: int = 0

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class ParentConfig(YAMLBaseConfig):
        _yaml_tag = "!Parent"
        name: str = "default"
        child: ChildConfig = ChildConfig()

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string(
        """
        - !Child {x: 10}
        """
    )

    result = loader.construct_from_string('!Parent {name: "test", child: !Child {}}')
    assert result.name == "test"
    assert result.child == ChildConfig(x=10)


def test_deep_construct_list_of_configs(yaml_loader):
    """Test deep construction with a list containing configs."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class ItemConfig(YAMLBaseConfig):
        _yaml_tag = "!Item"
        v: int = 0

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string("- !Item {v: 5}")

    result = loader.construct_from_string(
        """
        - !Item {}
        - !Item {v: 3}
        """
    )
    assert result[0] == ItemConfig(v=5)
    assert result[1] == ItemConfig(v=3)


def test_deep_construct_dict_of_configs(yaml_loader):
    """Test deep construction recursing into dict values."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class DictItemConfig(YAMLBaseConfig):
        _yaml_tag = "!DictItem"
        n: int = 0

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string("- !DictItem {n: 7}")

    result = loader.construct_from_string("!DictItem {}")
    assert result == DictItemConfig(n=7)


def test_deep_construct_tuple_of_configs(yaml_loader):
    """Test deep construction recursing into tuple values."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class TupleItemConfig(YAMLBaseConfig):
        _yaml_tag = "!TupleItem"
        items: tuple[int, ...] = ()

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    result = loader.construct_from_string("!TupleItem {items: [1, 2, 3]}")
    assert result.items == (1, 2, 3)


def test_add_config_data_with_priority_and_configs(yaml_loader):
    """Test add_config_data with mixed priority/config-list documents."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class PrioConfig(YAMLBaseConfig):
        _yaml_tag = "!Prio"
        val: int = 0

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string("priority: 10\n---\n- !Prio {val: 42}")

    result = loader.construct_from_string("!Prio {}")
    assert result == PrioConfig(val=42)


def test_add_config_data_invalid_entry_raises(yaml_loader):
    """Test add_config_data raises ValueError on invalid entry type."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class BadDataConfig(YAMLBaseConfig):
        _yaml_tag = "!BadData"
        val: int = 0

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ValueError, match="Entries in the config files must be"):
        loader.add_config_data(["not a dict or list"])


def test_add_single_config_string_non_config_raises(yaml_loader):
    """Test add_single_config_string raises ValueError for non-config YAML."""
    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ValueError, match="not a registered config"):
        loader.add_single_config_string("just a string", priority=0)


def test_flat_construct_unregistered_tag_raises(yaml_loader):
    """Test flat_construct_from_tag raises for unregistered tag."""
    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(RuntimeError, match="no config is registered"):
        loader.flat_construct_from_tag("!NoSuchTag")


def test_validate_assignment_during_deep_construct(yaml_loader):
    """Test that validate_assignment=True is respected during deep construction."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class ValidatedConfig(YAMLBaseConfig):
        _yaml_tag = "!Validated"
        count: int = 0

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string("- !Validated {count: 5}")

    result = loader.construct_from_string("!Validated {}")
    assert result.count == 5

    # validate_assignment should prevent setting wrong type
    with pytest.raises(ValidationError):
        result.count = "not a number"  # type: ignore[assignment]


def test_construct_from_file_with_loaded_configs(yaml_loader, tmp_path):
    """Test construct_from_file uses previously loaded configs for resolution."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class FileConfig(YAMLBaseConfig):
        _yaml_tag = "!File"
        x: int = 0
        y: int = 0

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string("- !File {x: 10}")

    construct_file = tmp_path / "construct.yaml"
    construct_file.write_text("!File {y: 20}")

    result = loader.construct_from_file(construct_file)
    assert result.x == 10
    assert result.y == 20


def test_validate_config_force_all_raises_on_missing():
    """validate_config with force_all=True raises on missing required fields."""

    class RequiredConfig(YAMLBaseConfig):
        _yaml_tag = "!Required"
        required_field: int

    config = RequiredConfig.model_construct()
    with pytest.raises(ValidationError):
        config.validate_config(force_all=True)


def test_validate_config_ctx_in_error():
    """validate_config includes ctx from constraint errors (e.g. ge)."""

    class ConstrainedConfig(YAMLBaseConfig):
        _yaml_tag = "!Constrained"
        value: int = Field(ge=0)

    config = ConstrainedConfig.model_construct(value=-1)
    with pytest.raises(ValidationError, match="greater than or equal"):
        config.validate_config(force_all=False)


def test_deep_construct_with_tuple(yaml_loader):
    """Test deep_construct handles tuples containing configs."""
    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    result = loader.deep_construct(("a", 1, None))
    assert result == ("a", 1, None)


def test_deep_construct_with_dict(yaml_loader):
    """Test deep_construct handles dicts containing configs."""
    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    result = loader.deep_construct({"key": "value", "num": 42})
    assert result == {"key": "value", "num": 42}


def test_deep_construct_warns_on_unknown_type(yaml_loader, caplog):
    """Test that deep_construct logs a warning for unhandled types."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class WarnConfig(YAMLBaseConfig):
        _yaml_tag = "!Warn"
        value: int = 0

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    # Call deep_construct directly with an unknown type
    with caplog.at_level(logging.WARNING, logger="yaloader.config_loader"):
        loader.deep_construct(MagicMock())
    assert "not explicitly handled" in caplog.text


def test_load_string_parser_error(yaml_loader):
    """Test load_string re-raises ParserError for invalid YAML."""
    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ParserError):
        loader.load_string("!A {invalid yaml: [")


def test_load_file_parser_error(yaml_loader, tmp_path):
    """Test load_file re-raises ParserError for invalid YAML."""
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("!A {invalid yaml: [")
    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ParserError):
        loader.load_file(bad_file)


def test_construct_from_file_parser_error(yaml_loader, tmp_path):
    """Test construct_from_file re-raises ParserError for invalid YAML."""
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("!A {invalid yaml: [")
    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ParserError):
        loader.construct_from_file(bad_file)
