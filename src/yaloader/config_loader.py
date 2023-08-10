from __future__ import annotations

import datetime
import logging
from inspect import isclass
from pathlib import PosixPath, Path
from typing import Type, Dict, List, Any, Tuple, Set, Iterator, Union, Optional

import yaml
from pydantic import BaseModel, conint
from yaml.constructor import ConstructorError
from yaml.parser import ParserError

from yaloader import YAMLBaseConfig, YAMLConfigLoader, get_multi_constructor_for_vars, VarYAMLConfigBase

logger = logging.getLogger(__name__)


class ConfigWithPriority(BaseModel):
    """Keep a loaded yaml config class together with its priority."""

    config: YAMLBaseConfig
    priority: conint(ge=0, le=100) = 0


class ConfigLoader:
    """The loader which will keep track of all loaded yaml configs."""

    def __init__(self, yaml_loader: Type[YAMLConfigLoader] = YAMLConfigLoader, cacheing: bool = True):
        self.yaml_loader = yaml_loader
        self.yaml_loader.add_multi_constructor(
            tag_prefix="!ConfigVar",
            multi_constructor=get_multi_constructor_for_vars(yaml_loader),
        )

        # All loaded yaml configs with their priorities per tag
        self.configs_per_tag: Dict[str, List[ConfigWithPriority]] = {}

        self.cacheing = cacheing
        self.cache = None if not cacheing else {}

    def deep_construct_from_config(
            self, config: YAMLBaseConfig, final: bool = False, auto_load: bool = False
    ) -> Any:
        """Deeply construct the config based on a config object.

        :param config: The config which should be constructed
        :param final: If False missing values will be ignored
        :param auto_load: If True automatically call the :meth:`YAMLBaseConfig.load()` method on the loaded config
        :return: The constructed config
        """
        # Construct only the flat object
        config = self.flat_construct_from_config(config)

        # Deep construct every attribute
        for key, v in dict(config).items():
            v = self.deep_construct(v, final=final, auto_load=auto_load)
            setattr(config, key, v)

        # Ensure that the config is still correct (and complete if final is True)
        config.validate_config(force_all=final)
        if auto_load:
            return config.load()
        return config

    def deep_construct(
            self, v: Any, final: bool = False, auto_load: bool = False
    ) -> Any:
        # If v is another config just recursive call deep construct
        if isinstance(v, YAMLBaseConfig):
            return self.deep_construct_from_config(v, final=final, auto_load=auto_load)
        # If v is a list, tuple or dict recursively call this method for every item
        elif isinstance(v, List):
            return list(
                [self.deep_construct(e, final=final, auto_load=auto_load) for e in v]
            )
        elif isinstance(v, Tuple):
            return tuple(
                (self.deep_construct(e, final=final, auto_load=auto_load) for e in v)
            )
        elif isinstance(v, Dict):
            return {
                k: self.deep_construct(e, final=final, auto_load=auto_load)
                for k, e in v.items()
            }
        # If v is an unhandled type log a warning and return v itself
        elif v is not None and not isinstance(
                v, (int, float, str, PosixPath, datetime.timedelta, datetime.datetime)
        ):
            logger.warning(
                f"Got type {type(v)} while deep construct of a yaml config which is not explicitly handled."
            )
        return v

    def flat_construct_from_config(self, config: YAMLBaseConfig) -> YAMLBaseConfig:
        """Construct the config based on a config object.

        :param config: The config which should be constructed
        :return: The constructed config
        """
        # Construct flat object from loaded configs
        tag_config = self.flat_construct_from_tag(config.get_yaml_tag())

        # Get the not explict configs attributes
        not_explict_config_attributes = {}
        self.update_config_attributes(
            not_explict_config_attributes, [tag_config, config], explicit=False
        )

        # Get the explict configs attributes
        explicit_configs_attributes = {}
        self.update_config_attributes(
            explicit_configs_attributes, [tag_config, config], explicit=True
        )

        # Update object from loaded config attributes with not explict and explict configs
        config_attributes = {}
        config_attributes.update(not_explict_config_attributes)
        config_attributes.update(explicit_configs_attributes)

        # If the config is a variable construct using the base class
        config_cls = tag_config.__class__
        while issubclass(config_cls, VarYAMLConfigBase):
            config_cls = config_cls.__base__

        constructed_config = config_cls.model_construct(
            _fields_set=set(explicit_configs_attributes.keys()), **config_attributes
        )

        constructed_config.validate_config(force_all=False)
        return constructed_config

    def flat_construct_from_tag(self, tag: str) -> YAMLBaseConfig:
        """Construct the config for a tag.

        This is not deep. If the config contains another config the included one is NOT constructed!

        This includes inheritance as following:
            - explict set fields go over not explict set fields
            - local field go over inherited fields
            - inherited explict field goes over local not explict field
            - if there are multiple base classes the most left is most important
            - for multiple yaml configs high priority goes over low priority
            - for multiple yaml configs with same priority order matters

        :param tag: The tag of the config which should be constructed
        :return: The constructed config
        """
        if self.cacheing and tag in self.cache:
            return self.cache[tag].model_copy()
        try:
            default_config = self.yaml_loader.yaml_config_classes[tag].model_construct()
        except KeyError as e:
            raise RuntimeError(
                f"Can not load configs for {tag}! "
                f"It seems that no config is registered for that tag."
            ) from e

        configs_with_priority_for_tag = [
            ConfigWithPriority(config=default_config, priority=0)
        ]
        configs_with_priority_for_tag += self.configs_per_tag.get(tag, [])

        # Sort pairs by priority (lowest first) and get the config
        configs_with_priority_for_tag.sort(
            key=lambda configs_with_priority: configs_with_priority.priority
        )
        configs_objects: List[YAMLBaseConfig] = list(
            map(lambda y: y.config, configs_with_priority_for_tag)
        )

        # Get the class of the config, make sure it is exactly one
        configs_object_classes: Set[Type[YAMLBaseConfig]] = set(
            map(lambda o: o.__class__, configs_objects)
        )
        if len(configs_object_classes) != 1:
            raise RuntimeError(
                f"In the configs for the tag {tag} is more than one class."
            )
        config_object_class = configs_object_classes.pop()

        # Get all config classes which it inherits from
        # noinspection PyTypeChecker
        config_class_bases: Iterator[Type[YAMLBaseConfig]] = filter(
            lambda x: (
                    isclass(x) and issubclass(x, YAMLBaseConfig) and not x == YAMLBaseConfig
            ),
            config_object_class.__bases__,
        )

        # Construct all bases, in reversed order (first base has the highest priority and should be at end of the list)
        # Construction MUST BE flat. Otherwise there might be circles.
        constructed_config_bases: List[YAMLBaseConfig] = list(
            map(
                lambda config_base: self.flat_construct_from_tag(
                    config_base.get_yaml_tag()
                ),
                config_class_bases,
            )
        )
        constructed_config_bases.reverse()

        # Construct not explict set config attributes
        not_explict_config_attributes = {}
        # Add all not explict set fields from the bases, starting with the most right base to left base
        self.update_config_attributes(
            not_explict_config_attributes, constructed_config_bases, explicit=False
        )
        # Add all not explict set fields from the loaded configs, starting with the lowest priority to the highest
        self.update_config_attributes(
            not_explict_config_attributes, configs_objects, explicit=False
        )

        # Construct explict set config attributes
        explicit_config_attributes = {}
        # Add all explict set fields from the bases, starting with the most right base to left base
        self.update_config_attributes(
            explicit_config_attributes, constructed_config_bases, explicit=True
        )
        # Add all explict set fields from the loaded configs, starting with the lowest priority to the highest
        self.update_config_attributes(
            explicit_config_attributes, configs_objects, explicit=True
        )

        # Overwrite not explict config attributes with explict ones
        config_attributes = {}
        config_attributes.update(not_explict_config_attributes)
        config_attributes.update(explicit_config_attributes)
        # Construct config object, set only fields from `explicit_config_attributes` to explict
        constructed_config = config_object_class.model_construct(
            _fields_set=set(explicit_config_attributes.keys()), **config_attributes
        )

        # Validate, but do not force all. Some base class might be not complete (and it don't has to)
        constructed_config.validate_config(force_all=False)

        if self.cacheing:
            self.cache[tag] = constructed_config
        return constructed_config.model_copy()

    @staticmethod
    def update_config_attributes(
            config_attributes: dict, config_updates: List[YAMLBaseConfig], explicit: bool
    ) -> None:
        """Add config attributes from update configs to the current config attributes.

        If the field already exists overwrite it. So `config_updates` are lowest priority first.

        :param config_attributes: Dict of existing attributes of the config
        :param config_updates: List of configs from which the attributes should be updated
        :param explicit: If True use only explicit attributes. Else use only not explicit ones.
        """
        for update in config_updates:
            update_dict = dict(update)
            fields = filter(
                lambda f: (f in update.model_fields_set) == explicit, update_dict.keys()
            )
            for field in fields:
                config_attributes[field] = update_dict[field]

    def add_config(self, config_with_priority: ConfigWithPriority):
        """Add a config object together with its priority to the loader."""
        config: YAMLBaseConfig = config_with_priority.config
        tag = config.get_yaml_tag()
        try:
            self.configs_per_tag[tag].append(config_with_priority)
        except KeyError:
            self.configs_per_tag[tag] = [config_with_priority]

    def add_single_config_string(self, string: str, priority):
        """Add a yaml string with a single config object."""
        config: YAMLBaseConfig = yaml.load(string, Loader=self.yaml_loader)
        if not isinstance(config, YAMLBaseConfig):
            string = string.replace("\n", "\n\t")
            raise ValueError(
                f"The given string is not a registered config:\n\n\t{string}"
            )
        config_with_priority = ConfigWithPriority(config=config, priority=priority)
        self.add_config(config_with_priority)

    def add_config_data(self, config_data: List[Union[Dict, List]], priority=None):
        """Add multiple configs or priorities."""
        given_priority = priority
        for config_element in config_data:
            if isinstance(config_element, Dict) and "priority" in config_element:
                priority = (
                    config_element["priority"]
                    if given_priority is None
                    else given_priority
                )
            elif isinstance(config_element, List):
                for config in config_element:
                    if isinstance(config, YAMLBaseConfig):
                        config_with_priority = ConfigWithPriority(
                            config=config,
                            priority=priority if priority is not None else 0,
                        )
                        self.add_config(config_with_priority)
            else:
                raise ValueError(
                    f"Entries in the config files must be mapping containing a priority key "
                    f"or a list of configs."
                )

    def load_string(self, string, priority: Optional[int] = None):
        """Load a yaml string including multiple configs or priorities."""
        try:
            config_data: List = list(yaml.load_all(string, Loader=self.yaml_loader))
        except (ParserError, ConstructorError) as e:
            raise e
        self.add_config_data(config_data, priority)

    def load_file(self, file_path: Path, priority: Optional[int] = None):
        """Load a yaml file including multiple configs or priorities."""
        if not file_path.is_file():
            if file_path.with_suffix(".yaml").is_file():
                file_path = file_path.with_suffix(".yaml")
            else:
                raise FileNotFoundError(f"Could not find file {file_path}")

        with open(file_path) as file:
            try:
                config_data: List = list(yaml.load_all(file, Loader=self.yaml_loader))
            except (ParserError, ConstructorError) as e:
                raise e
        self.add_config_data(config_data, priority)

    def load_directory(self, directory_path: Path, priority: Optional[int] = None):
        """Load all files ending with .yaml from a directory."""
        if not directory_path.is_dir():
            raise NotADirectoryError(f"{directory_path} is not a directory.")
        for file_path in sorted(directory_path.glob("*.yaml")):
            self.load_file(file_path, priority)

    def construct_from_string(self, string: str, auto_load: bool = False, final: bool = True):
        """Construct the configuration for a yaml string with a single yaml config."""
        try:
            config: Any = yaml.load(string, Loader=self.yaml_loader)
        except (ParserError, ConstructorError) as e:
            raise e
        return self.deep_construct(config, final=final, auto_load=auto_load)

    def construct_from_file(self, file_path: Path, auto_load: bool = False, final: bool = True):
        """Construct the configuration for a yaml file with a single yaml config."""
        if not file_path.is_file():
            if file_path.with_suffix(".yaml").is_file():
                file_path = file_path.with_suffix(".yaml")
            else:
                raise FileNotFoundError(f'Could not find file "{file_path}"')
        with open(file_path) as file:
            try:
                config: Any = yaml.load(file, Loader=self.yaml_loader)
            except (ParserError, ConstructorError) as e:
                raise e
        return self.deep_construct(config, final=final, auto_load=auto_load)
