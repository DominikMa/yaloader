"""Tests for constructor.py edge cases."""

import pytest
from yaml.parser import ParserError

import yaloader.constructor
from yaloader import YAMLBaseConfig, YAMLValueError


def test_var_constructor_missing_tag_falls_back_to_registered_parent(yaml_loader, config_loader):
    """When _tag is missing but the variable tag is already registered, fall back to parent's tag."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class FallbackConfig(YAMLBaseConfig):
        _yaml_tag = "!Fallback"
        value: int = 0

    # First, register the variable tag by using it with _tag
    config_loader.construct_from_string('!ConfigVarFB {_tag: "!Fallback", value: 1}')

    # Now use the same variable tag without _tag — should fall back to registered parent
    result = config_loader.construct_from_string("!ConfigVarFB {value: 2}")
    assert result == FallbackConfig(value=2)


def test_var_constructor_missing_tag_no_parent_raises(yaml_loader, config_loader):
    """When _tag is missing and the variable tag is not registered, raise an error."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class SomeConfig(YAMLBaseConfig):
        _yaml_tag = "!Some"
        value: int = 0

    with pytest.raises(YAMLValueError, match="_tag attribute is missing"):
        config_loader.construct_from_string("!ConfigVarUnknown {value: 1}")


def test_var_constructor_tag_not_registered_raises(yaml_loader, config_loader):
    """When _tag references an unregistered config, raise an error."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class RegConfig(YAMLBaseConfig):
        _yaml_tag = "!Reg"
        value: int = 0

    with pytest.raises(YAMLValueError, match="_tag attribute is no registered config"):
        config_loader.construct_from_string('!ConfigVarBad {_tag: "!NotRegistered", value: 1}')


def test_var_constructor_reused_tag_same_parent_ok(yaml_loader, config_loader):
    """Reusing a variable tag with the same _tag should work fine."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class ReuseConfig(YAMLBaseConfig):
        _yaml_tag = "!Reuse"
        value: int = 0

    result = config_loader.construct_from_string(
        """
        - !ConfigVarReuse {_tag: "!Reuse", value: 1}
        - !ConfigVarReuse {_tag: "!Reuse", value: 2}
        """
    )
    assert result[0] == ReuseConfig(value=1)
    assert result[1] == ReuseConfig(value=2)


def test_var_constructor_reused_tag_different_parent_raises(yaml_loader, config_loader):
    """Reusing a variable tag with a different _tag should raise an error."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class AlphaConfig(YAMLBaseConfig):
        _yaml_tag = "!Alpha"
        value: int = 0

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class BetaConfig(YAMLBaseConfig):
        _yaml_tag = "!Beta"
        value: int = 0

    # First use registers the variable tag with !Alpha
    config_loader.construct_from_string('!ConfigVarConflict {_tag: "!Alpha", value: 1}')

    # Second use with different _tag should raise
    with pytest.raises(YAMLValueError, match="variable with same tag already has another _tag attribute"):
        config_loader.construct_from_string('!ConfigVarConflict {_tag: "!Beta", value: 2}')


def test_var_constructor_not_a_mapping_raises(yaml_loader, config_loader):
    """Variable constructor should raise on non-mapping nodes."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class MapConfig(YAMLBaseConfig):
        _yaml_tag = "!Map"
        value: int = 0

    with pytest.raises(ParserError):
        config_loader.construct_from_string("!ConfigVarX 42")


def test_var_constructor_validation_error(yaml_loader, config_loader):
    """Variable constructor should raise YAMLValueError on validation failure."""

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class StrictConfig(YAMLBaseConfig):
        _yaml_tag = "!Strict"
        value: int = 0

    with pytest.raises(YAMLValueError):
        config_loader.construct_from_string('!ConfigVarStrict {_tag: "!Strict", value: "not_an_int"}')


def test_loads_decorator_invalid_yaml_tag_type(yaml_loader):
    """@loads should raise TypeError when _yaml_tag is not str or ModelPrivateAttr."""
    with pytest.raises(TypeError, match="_yaml_tag attribute has to be of class str"):

        @yaloader.constructor.loads(yaml_loader=yaml_loader)
        class BadTagConfig(YAMLBaseConfig):
            _yaml_tag = 123
            value: int = 0
