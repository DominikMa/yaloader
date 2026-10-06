from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic

from typing_extensions import TypeVar, assert_type

from yaloader import YAMLBaseConfig, loads


@dataclass
class LoadedValue:
    value: int
    name: str = "default"


@loads(LoadedValue)
class TypedValueConfig(YAMLBaseConfig[LoadedValue]):
    value: int = 1


@loads(LoadedValue)
class UntypedValueConfig(YAMLBaseConfig):
    value: int = 1


@loads(LoadedValue)
class TypedChildConfig(TypedValueConfig):
    name: str = "child"


@loads(LoadedValue)
class UntypedChildConfig(UntypedValueConfig):
    name: str = "child"


@loads()
class CustomValueConfig(YAMLBaseConfig[LoadedValue]):
    value: int = 1

    def load(self, offset: int = 0) -> LoadedValue:
        return LoadedValue(value=self.value + offset)


@loads()
class InheritedCustomConfig(CustomValueConfig):
    pass


@loads()
class OverrideCustomConfig(CustomValueConfig):
    def load(self, offset: int = 0) -> LoadedValue:
        return LoadedValue(value=self.value * 2 + offset)


_Result = TypeVar("_Result", default=Any)


@loads()
class GenericValueConfig(YAMLBaseConfig[_Result], Generic[_Result]):
    value: int = 1


@loads(LoadedValue)
class ConcreteGenericValueConfig(GenericValueConfig[LoadedValue]):
    pass


def inspect_configs(
    typed: TypedValueConfig,
    untyped: UntypedValueConfig,
    typed_child: TypedChildConfig,
    untyped_child: UntypedChildConfig,
    custom: CustomValueConfig,
    inherited_custom: InheritedCustomConfig,
    override_custom: OverrideCustomConfig,
) -> None:
    assert_type(typed.value, int)
    assert_type(typed.load(), LoadedValue)
    assert_type(untyped.value, int)
    assert_type(untyped.load(), Any)
    assert_type(typed_child.value, int)
    assert_type(typed_child.name, str)
    assert_type(typed_child.load(), LoadedValue)
    assert_type(untyped_child.value, int)
    assert_type(untyped_child.name, str)
    assert_type(untyped_child.load(), Any)
    assert_type(custom.load(offset=1), LoadedValue)
    assert_type(inherited_custom.load(offset=1), LoadedValue)
    assert_type(override_custom.load(offset=1), LoadedValue)


assert_type(TypedValueConfig().load(), LoadedValue)
assert_type(UntypedValueConfig().load(), Any)
assert_type(TypedChildConfig().load(), LoadedValue)
assert_type(UntypedChildConfig().load(), Any)
assert_type(GenericValueConfig[LoadedValue]().load(), LoadedValue)
assert_type(GenericValueConfig().load(), Any)
assert_type(ConcreteGenericValueConfig().value, int)
assert_type(ConcreteGenericValueConfig().load(), LoadedValue)
