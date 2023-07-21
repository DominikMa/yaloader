from __future__ import annotations

from typing import Dict, Type

import yaml
from yaml import MarkedYAMLError

from yaloader import YAMLBaseConfig
from yaloader.utils import full_object_name


class YAMLConfigLoader(yaml.SafeLoader):
    """YAML loader for the configs."""

    yaml_config_classes: Dict[str, Type[YAMLBaseConfig]] = {}

    @classmethod
    def add_config_constructor(
            cls,
            config_class: Type[YAMLBaseConfig],
            constructor,
            overwrite_tag: bool = False,
    ) -> None:
        """Add a yaml config class with its constructor to the loader.

        :param config_class: The config which should be added to the loader.
        :param constructor: The constructor to load the class.
        :param overwrite_tag: If true and an other config with the same tag is
                              already registered the previous config for
                              the same tag is overwritten.
                              Else a RuntimeError is raised if the tag of
                              the config is already registered.
        :return:
        """
        tag = config_class.get_yaml_tag()
        if tag.startswith("!!"):
            raise RuntimeError(
                f"The tag {tag} has the prefix !! and can "
                f"therefore not be used by {full_object_name(config_class)}. "
                f"Choose another tag for the yaml config class."
            )

        if tag in cls.yaml_constructors:
            # If tag is not in the registered yaml config classes,
            # it is a tag of the SafeLoader and should not be overwritten.
            if tag not in cls.yaml_config_classes:
                raise RuntimeError(
                    f"The tag {tag} is already registered and can not be used "
                    f"by {full_object_name(config_class)}. "
                    f"Choose another tag for the yaml config class."
                )

            if not overwrite_tag:
                raise RuntimeError(
                    f"The tag {tag} is already registered by {full_object_name(cls.yaml_config_classes[tag])} "
                    f"and can therefore not be used by {full_object_name(config_class)}. "
                    f"Set overwrite_tag to True if you want to overwrite the existing tag "
                    f"or choose another tag for one of the yaml config classes."
                )
            # Overwrite existing tag, while keeping is under a different tag.
            old_constructor = cls.yaml_constructors[tag]
            del cls.yaml_constructors[tag]
            old_config_class = cls.yaml_config_classes[tag]
            del cls.yaml_config_classes[tag]

            old_config_class.set_yaml_tag(f"!{full_object_name(old_config_class)}")
            cls.add_config_constructor(old_config_class, old_constructor)

        cls.add_constructor(tag, constructor)

        # TODO: Not quite sure if this makes sense. Copied from the original yaml loader.
        if "yaml_config_classes" not in cls.__dict__:
            cls.yaml_config_classes = cls.yaml_config_classes.copy()
        cls.yaml_config_classes[tag] = config_class


class YAMLValueError(MarkedYAMLError):
    """Error of wrong values in the loaded yaml configs."""
