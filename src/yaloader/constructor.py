from __future__ import annotations

import textwrap
from typing import Callable

import yaml
from pydantic import ValidationError
from pydantic.fields import ModelPrivateAttr
from yaml.parser import ParserError

from yaloader import VarYAMLConfigBase, YAMLBaseConfig, YAMLConfigDumper, YAMLConfigLoader, YAMLValueError
from yaloader.representer import get_representer_for_class


def _check_extra_fields(cls: type[YAMLBaseConfig], mapping: dict, node: yaml.Node) -> None:
    """Check for extra fields not defined in the model."""
    extra_fields = set(mapping.keys()) - set(cls.model_fields.keys())
    if extra_fields:
        raise YAMLValueError(
            f"Could not validate the configuration for the tag {node.tag}",
            node.start_mark,
            f"extra fields not permitted: {extra_fields}",
        )


def get_constructor_for_class(cls: type[YAMLBaseConfig]) -> Callable:
    def constructor(loader: YAMLConfigLoader, node: yaml.MappingNode) -> YAMLBaseConfig:
        """Construct the config object from a mapping."""
        if not isinstance(node, yaml.MappingNode):
            raise ParserError(
                f"While parsing the configuration for the tag {node.tag}",
                node.start_mark,
                f"expected a mapping node, but found {node.id}",
            )
        # Get the mapping in a dictionary
        mapping = loader.construct_mapping(node, deep=True)
        # Check for extra fields when config is extra="forbid"
        if cls.model_config.get("extra") == "forbid":
            _check_extra_fields(cls, mapping, node)
        # Construct an object of this config class WITHOUT validating the inputs
        config_instance: YAMLBaseConfig = cls.model_construct(**mapping)
        # Validate the inputs, but ignore missing errors
        try:
            cls.validate_config(config_instance, force_all=False)
        except ValidationError as error:
            raise YAMLValueError(
                f"Could not validate the configuration for the tag {node.tag}",
                node.start_mark,
                textwrap.indent(str(error), 2 * " "),
            ) from error
        return config_instance

    return constructor


def get_multi_constructor_for_vars(
    yaml_loader: type[YAMLConfigLoader], yaml_dumper: type[YAMLConfigDumper] | None = None
) -> Callable:
    def constructor(loader: YAMLConfigLoader, tag_suffix: str, node: yaml.MappingNode) -> YAMLBaseConfig:
        """Construct the config object from a mapping."""
        if not isinstance(node, yaml.MappingNode):
            raise ParserError(
                f"While parsing the configuration for the tag {node.tag}",
                node.start_mark,
                f"expected a mapping node, but found {node.id}",
            )
        # Get the mapping in a dictionary
        mapping = loader.construct_mapping(node, deep=True)

        try:
            tag = str(mapping.pop("_tag"))
        except KeyError:
            # TODO test
            if node.tag in yaml_loader.yaml_config_classes:
                # noinspection PyUnresolvedReferences
                tag = yaml_loader.yaml_config_classes[node.tag].__base__.get_yaml_tag()
            else:
                raise YAMLValueError(
                    f"Could not load the configuration for variable with tag {node.tag}",
                    node.start_mark,
                    "_tag attribute is missing",
                ) from None
        if tag not in yaml_loader.yaml_config_classes:
            # TODO test
            raise YAMLValueError(
                f"Could not load the configuration for variable with tag {node.tag}",
                node.start_mark,
                "_tag attribute is no registered config",
            )

        if node.tag in yaml_loader.yaml_config_classes:
            # TODO test
            # noinspection PyUnresolvedReferences
            if tag != yaml_loader.yaml_config_classes[node.tag].__base__.get_yaml_tag():
                # TODO test
                raise YAMLValueError(
                    f"Could not load the configuration for variable with tag {node.tag}",
                    node.start_mark,
                    "variable with same tag already has another _tag attribute",
                )
            var_yaml_config_class = yaml_loader.yaml_config_classes[node.tag]
        else:
            base_config_class = yaml_loader.yaml_config_classes[tag]

            @loads(yaml_loader=None, yaml_dumper=None)
            class VarYAMLConfig(base_config_class, VarYAMLConfigBase):
                _yaml_tag = node.tag

            var_yaml_config_class = VarYAMLConfig
            yaml_loader.yaml_config_classes[node.tag] = var_yaml_config_class

        # Check for extra fields when config is extra="forbid"
        if var_yaml_config_class.model_config.get("extra") == "forbid":
            _check_extra_fields(var_yaml_config_class, mapping, node)
        # Construct an object of this config class WITHOUT validating the inputs
        config_instance: YAMLBaseConfig = var_yaml_config_class.model_construct(**mapping)
        # Validate the inputs, but ignore missing errors
        try:
            var_yaml_config_class.validate_config(config_instance, force_all=False)
        except ValidationError as e:
            raise YAMLValueError(
                f"Could not validate the configuration for the tag {node.tag}",
                node.start_mark,
                textwrap.indent(str(e), 2 * " "),
            ) from e
        return config_instance

    return constructor


def loads(
    loaded_class: type | None = None,
    overwrite_tag: bool = False,
    yaml_loader: type[YAMLConfigLoader] | None = YAMLConfigLoader,
    yaml_dumper: type[YAMLConfigDumper] | None = YAMLConfigDumper,
) -> Callable[[type[YAMLBaseConfig]], type[YAMLBaseConfig]]:
    """A class decorator for yaml configs to add a simple load function for a given class.

    A load function, which gets all attributes of the config
    and creates an instance of the given class with them as key word arguments,
    is added to the config.

    :param loaded_class: The class which should be loaded by this
    :return: The class decorator
    """

    def decorate(cls: type[YAMLBaseConfig]) -> type[YAMLBaseConfig]:
        # If there is an explict yaml tag given use it
        if hasattr(cls, "_yaml_tag"):
            if isinstance(cls._yaml_tag, ModelPrivateAttr):
                cls.set_yaml_tag(cls._yaml_tag.default)
            elif isinstance(cls._yaml_tag, str):
                cls.set_yaml_tag(cls._yaml_tag)
            else:
                raise TypeError(
                    f"The _yaml_tag attribute has to be of class str or pydantic.ModelPrivateAttr "
                    f"but got {type(cls._yaml_tag)}."
                )

        # Set the _loaded_class attribute
        if loaded_class is not None:
            cls._loaded_class = loaded_class

        if yaml_loader is not None:
            yaml_loader.add_config_constructor(cls, get_constructor_for_class(cls), overwrite_tag=overwrite_tag)
        if yaml_dumper is not None:
            yaml_dumper.add_representer(cls, get_representer_for_class(cls))

        return cls

    return decorate
