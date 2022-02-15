from __future__ import annotations

import datetime
import functools
import logging
import textwrap
from inspect import isclass
from pathlib import PosixPath, Path
from typing import Dict, Tuple, Set, Iterator, Type, Union, List, Optional, Any, Callable

import yaml
from pydantic import BaseModel, ValidationError, conint
from pydantic.main import ModelMetaclass
from yaml import MarkedYAMLError
from yaml.constructor import ConstructorError
from yaml.parser import ParserError

from yaloader.utils import full_object_name, remove_missing_errors

logger = logging.getLogger(__name__)


class YAMLValueError(MarkedYAMLError):
    """Error of wrong values in the loaded yaml configs."""
    pass


class YAMLConfigLoader(yaml.SafeLoader):
    """YAML loader for the configs."""
    yaml_config_classes: Dict[str, Type[YAMLBaseConfig]] = {}

    @classmethod
    def add_config_constructor(cls, config_class: Type[YAMLBaseConfig],
                               constructor, overwrite_tag: bool = False) -> None:
        """Add a yaml config class with its constructor to the loader.

        :param config_class: The config which should be added to the loader.
        :param constructor: The constructor to load the class.
        :param overwrite_tag: If true and an other config with the same tag is already registered
                              the previous config for the same tag is overwritten.
                              Else a RuntimeError is raised if the tag of the config is already registered.
        :return:
        """
        tag = config_class.get_yaml_tag()
        if tag.startswith('!!'):
            raise RuntimeError(
                f"The tag {tag} has the prefix !! and can therefore not be used by {full_object_name(config_class)}. "
                f"Choose another tag for the yaml config class."
            )

        if tag in cls.yaml_constructors.keys():
            # If tag is not in the registered yaml config classes,
            # it is a tag of the SafeLoader and should not be overwritten.
            if tag not in cls.yaml_config_classes:
                raise RuntimeError(
                    f"The tag {tag} is already registered and can not be used by {full_object_name(config_class)}. "
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
        if 'yaml_config_classes' not in cls.__dict__:
            cls.yaml_config_classes = cls.yaml_config_classes.copy()
        cls.yaml_config_classes[tag] = config_class


class YAMLConfigDumper(yaml.SafeDumper):
    """YAML dumper for the configs."""
    exclude_unset: bool = True
    """If True exclude all unset values when dumping the config. 
    See https://pydantic-docs.helpmanual.io/usage/exporting_models/ for details."""
    exclude_defaults: bool = True
    """If True exclude all default values when dumping the config.
    See https://pydantic-docs.helpmanual.io/usage/exporting_models/ for details."""


class YAMLConfigMetaclass(ModelMetaclass):
    """Metaclass for the BaseConfig to automagically add constructor and representer to the loader and dumper."""

    def __init__(cls: Type[YAMLBaseConfig], name, bases, attrs, overwrite_tag: bool = False,
                 yaml_loader: Type[YAMLConfigLoader] = YAMLConfigLoader,
                 yaml_dumper: Type[YAMLConfigDumper] = YAMLConfigDumper, **kwargs):
        cls: Type[YAMLBaseConfig]  # For the IDE
        super(YAMLConfigMetaclass, cls).__init__(name, bases, attrs, **kwargs)

        # If there is an explict yaml tag given use it
        if '_yaml_tag' in attrs:
            cls.set_yaml_tag(attrs['_yaml_tag'])

        def constructor(loader: YAMLConfigLoader, node: yaml.MappingNode) -> YAMLBaseConfig:
            """Construct the config object from a mapping."""
            if not isinstance(node, yaml.MappingNode):
                raise ParserError(f"While parsing the configuration for the tag {node.tag}", node.start_mark,
                                  f"expected a mapping node, but found {node.id}")
            # Get the mapping in a dictionary
            mapping = loader.construct_mapping(node, deep=True)
            # Construct an object of this config class WITHOUT validating the inputs
            config_instance: YAMLBaseConfig = cls.construct(**mapping)
            # Validate the inputs, but ignore missing errors
            try:
                cls.validate_config(config_instance, force_all=False)
            except ValidationError as e:
                raise YAMLValueError(f"Could not validate the configuration for the tag {node.tag}", node.start_mark,
                                     textwrap.indent(str(e), 2 * ' '))
            return config_instance

        yaml_loader.add_config_constructor(cls, constructor, overwrite_tag=overwrite_tag)

        def representer(dumper: YAMLConfigDumper, data: YAMLBaseConfig):
            """Represent the config object as a mapping."""
            # Get all keys which should be dumped
            keys = set(data.dict(exclude_unset=dumper.exclude_unset, exclude_defaults=dumper.exclude_defaults).keys())

            # Just for sorting the output:
            # Get keys of iteration types
            it_keys = set(filter(lambda k: isinstance(getattr(data, k), (list, tuple, dict)), keys))
            keys = keys.difference(it_keys)

            # Get keys of BaseConfig type
            config_objects_keys = set(filter(lambda key: isinstance(getattr(data, key), YAMLBaseConfig), keys))
            keys = keys.difference(config_objects_keys)

            dump_dict = {k: getattr(data, k) for k in sorted(keys) + sorted(it_keys) + sorted(config_objects_keys)}
            return dumper.represent_mapping(
                cls.get_yaml_tag(),
                dump_dict
            )

        yaml_dumper.add_representer(cls, representer)


def loads(loaded_class: Type) -> Callable[[Type[YAMLBaseConfig]], Type[YAMLBaseConfig]]:
    """A class decorator for yaml configs to add a simple load function for a given class.

    A load function, which gets all attributes of the config
    and creates an instance of the given class with them as key word arguments,
    is added to the config.

    :param loaded_class: The class which should be loaded by this
    :return: The class decorator
    """
    def decorate(cls: Type[YAMLBaseConfig]):
        @functools.wraps(cls.load)
        def load(self, *args, **kwargs):
            return loaded_class(**dict(self))

        setattr(cls, 'load', load)
        return cls
    return decorate


class YAMLBaseConfig(BaseModel, metaclass=YAMLConfigMetaclass):
    """The base class for all config objects which are loaded from or dumped to yaml files.

    Each config from which an actual object can be created has to implement
    the :meth:`YAMLBaseConfig.load()` method.
    """

    class Config:
        """Since yaml configs are used to create instances extra fields are forbidden."""
        extra = 'forbid'
        validate_assignment = True

    @classmethod
    def get_yaml_tag(cls) -> str:
        """Return the configs yaml tag."""
        cls._assure_has_yaml_tag()
        return getattr(cls, f"_{cls.__name__}__yaml_tag", None)

    @classmethod
    def set_yaml_tag(cls, yaml_tag: Optional[str]) -> None:
        """Set the yaml tag of the config.

        A valid tag has to start with an exclamation mark.

        :param yaml_tag: Optional string of the tag. If None the tag will be set to a default value.
        """
        setattr(cls, f"_{cls.__name__}__yaml_tag", yaml_tag)
        cls._assure_has_yaml_tag()

    @classmethod
    def _assure_has_yaml_tag(cls) -> None:
        """ Assert that the config has a valid yaml tag.

        If the tag is not set yet, try to set it to a default value.
        """
        yaml_tag = getattr(cls, f"_{cls.__name__}__yaml_tag", None)
        if yaml_tag is None or not isinstance(yaml_tag, str):
            # Set yaml tag to default case: class name without `Config` suffix
            class_name = cls.__name__
            if not class_name.endswith("Config"):
                raise RuntimeError(f"Config class {cls.__name__} has not yaml tag. "
                                   f"If the tag should be derived automatically the "
                                   f"class name has to end with `Config`")
            class_name = class_name.removesuffix("Config")
            yaml_tag = f"!{class_name}"
        elif not yaml_tag.startswith("!"):
            raise RuntimeError(f"The tag of config class {full_object_name(cls)} does not start with !")
        setattr(cls, f"_{cls.__name__}__yaml_tag", yaml_tag)

    def validate_config(self, force_all: bool = False) -> None:
        """Validate a BaseConfig instance

        If force_all is False do not raise an error on missing attributes.
        Configs have to be correct but may be incomplete.

        :param force_all: If True raise an error on missing attributes
        """
        try:
            self.validate(dict(self))
        except ValidationError as e:
            if force_all:
                raise
            not_missing_errors = remove_missing_errors(e.raw_errors)
            if len(not_missing_errors) > 0:
                raise ValidationError(not_missing_errors, model=e.model)

    def load(self, *args, **kwargs):
        """Create the object the yaml config object is for.

        Should be overwritten in sub classes.
        """
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        if 'overwrite_tag' in kwargs:
            kwargs.pop('overwrite_tag')
        if 'yaml_loader' in kwargs:
            kwargs.pop('yaml_loader')
        if 'yaml_dumper' in kwargs:
            kwargs.pop('yaml_dumper')
        super().__init_subclass__(**kwargs)


class ConfigWithPriority(BaseModel):
    """Keep a loaded yaml config class together with its priority."""
    config: YAMLBaseConfig
    priority: conint(ge=0) = 0


class ConfigLoader:
    """The loader which will keep track of all loaded yaml configs."""

    def __init__(self, yaml_loader: Type[YAMLConfigLoader] = YAMLConfigLoader):
        self.yaml_loader = yaml_loader

        # All loaded yaml configs with their priorities per tag
        self.configs_per_tag: Dict[str, List[ConfigWithPriority]] = {}

    def deep_construct_from_config(self, config: Any, final: bool = False, auto_load: bool = False) -> Any:
        """Deeply construct the config based on a config object.

        :param config: The config which should be constructed
        :param final: If False missing values will be ignored
        :param auto_load: If True automatically call the :meth:`YAMLBaseConfig.load()` method on the loaded config
        :return: The constructed config
        """
        if not isinstance(config, YAMLBaseConfig):
            return self._deep_construct(config, final=final, auto_load=auto_load)
        config: YAMLBaseConfig
        # Construct only the flat object
        config = self.flat_construct_from_config(config)

        # Deep construct every attribute
        for key, v in dict(config).items():
            v = self._deep_construct(v, final=final, auto_load=auto_load)
            setattr(config, key, v)

        # Ensure that the config is still correct (and complete if final is True)
        config.validate_config(force_all=final)
        if auto_load:
            return config.load()
        return config

    def _deep_construct(self, v: Any, final: bool = False, auto_load: bool = False) -> Any:
        # If v is another config just recursive call deep construct
        if isinstance(v, YAMLBaseConfig):
            return self.deep_construct_from_config(v, final=final, auto_load=auto_load)
        # If v is a list, tuple or dict recursively call this method for every item
        elif isinstance(v, List):
            return list([self._deep_construct(e, final=final, auto_load=auto_load) for e in v])
        elif isinstance(v, Tuple):
            return tuple((self._deep_construct(e, final=final, auto_load=auto_load) for e in v))
        elif isinstance(v, Dict):
            return {k: self._deep_construct(e, final=final, auto_load=auto_load) for k, e in v.items()}
        # If v is an unhandled type log a warning and return v itself
        elif v is not None and not isinstance(v, (
                int, float, str,
                PosixPath,
                datetime.timedelta, datetime.datetime
        )):
            logger.warning(f'Got type {type(v)} while deep construct of a yaml config which is not explicitly handled.')
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
        self.update_config_attributes(not_explict_config_attributes, [tag_config, config], explicit=False)

        # Get the explict configs attributes
        explicit_configs_attributes = {}
        self.update_config_attributes(explicit_configs_attributes, [tag_config, config], explicit=True)

        # Update object from loaded config attributes with not explict and explict configs
        config_attributes = {}
        config_attributes.update(not_explict_config_attributes)
        config_attributes.update(explicit_configs_attributes)
        constructed_config = config.construct(_fields_set=set(explicit_configs_attributes.keys()), **config_attributes)

        constructed_config.validate_config(force_all=False)
        return constructed_config

    def flat_construct_from_tag(self, tag: str) -> YAMLBaseConfig:
        """Construct the config for a tag.

        This is not deep. If the config contains an other config the included one is NOT constructed!

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
        try:
            default_config = self.yaml_loader.yaml_config_classes[tag].construct()
        except KeyError as e:
            raise RuntimeError(f"Can not load configs for {tag}! "
                               f"It seems that no config is registered for that tag.") from e

        configs_with_priority_for_tag = [ConfigWithPriority(config=default_config, priority=0)]
        configs_with_priority_for_tag += self.configs_per_tag.get(tag, [])

        # Sort pairs by priority (lowest first) and get the config
        configs_with_priority_for_tag.sort(key=lambda configs_with_priority: configs_with_priority.priority)
        configs_objects: List[YAMLBaseConfig] = list(map(lambda y: y.config, configs_with_priority_for_tag))

        # Get the class of the config, make sure it is exactly one
        configs_object_classes: Set[Type[YAMLBaseConfig]] = set(map(lambda o: o.__class__, configs_objects))
        if len(configs_object_classes) != 1:
            raise RuntimeError(f"In the configs for the tag {tag} is more than one class.")
        config_object_class = configs_object_classes.pop()

        # Get all config classes which it inherits from
        # noinspection PyTypeChecker
        config_class_bases: Iterator[Type[YAMLBaseConfig]] = filter(lambda x: (isclass(x) and
                                                                               issubclass(x, YAMLBaseConfig) and
                                                                               not x == YAMLBaseConfig),
                                                                    config_object_class.__bases__)

        # Construct all bases, in reversed order (first base has highest priority and should be at end of the list)
        # Construction MUST BE flat. Otherwise there might be circles.
        constructed_config_bases: List[YAMLBaseConfig] = list(map(
            lambda config_base: self.flat_construct_from_tag(config_base.get_yaml_tag()),
            config_class_bases)
        )
        constructed_config_bases.reverse()

        # Construct not explict set config attributes
        not_explict_config_attributes = {}
        # Add all not explict set fields from the bases, starting with the most right base to left base
        self.update_config_attributes(not_explict_config_attributes, constructed_config_bases, explicit=False)
        # Add all not explict set fields from the loaded configs, starting with the lowest priority to the highest
        self.update_config_attributes(not_explict_config_attributes, configs_objects, explicit=False)

        # Construct explict set config attributes
        explicit_config_attributes = {}
        # Add all explict set fields from the bases, starting with the most right base to left base
        self.update_config_attributes(explicit_config_attributes, constructed_config_bases, explicit=True)
        # Add all explict set fields from the loaded configs, starting with the lowest priority to the highest
        self.update_config_attributes(explicit_config_attributes, configs_objects, explicit=True)

        # Overwrite not explict config attributes with explict ones
        config_attributes = {}
        config_attributes.update(not_explict_config_attributes)
        config_attributes.update(explicit_config_attributes)
        # Construct config object, set only fields from `explicit_config_attributes` to explict
        constructed_config = config_object_class.construct(_fields_set=set(explicit_config_attributes.keys()),
                                                           **config_attributes)

        # Validate, but do not force all. Some base class might be not complete (and it don't has to)
        constructed_config.validate_config(force_all=False)
        return constructed_config

    @staticmethod
    def update_config_attributes(config_attributes: dict, config_updates: List[YAMLBaseConfig], explicit: bool) -> None:
        """Add config attributes from update configs to the current config attributes.

        If the field already exists overwrite it. So `config_updates` are lowest priority first.

        :param config_attributes: Dict of existing attributes of the config
        :param config_updates: List of configs from which the attributes should be updated
        :param explicit: If True use only explicit attributes. Else use only not explicit ones.
        """
        for update in config_updates:
            update_dict = dict(update)
            fields = filter(lambda f: (f in update.__fields_set__) == explicit,
                            update_dict.keys())
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
            string = string.replace('\n', '\n\t')
            raise ValueError(f"The given string is not a registered config:\n\n\t{string}")
        config_with_priority = ConfigWithPriority(config=config, priority=priority)
        self.add_config(config_with_priority)

    def add_config_data(self, config_data: List[Union[Dict, List]], priority=None):
        """Add multiple configs or priorities."""
        given_priority = priority
        for config_element in config_data:
            if isinstance(config_element, Dict) and 'priority' in config_element:
                priority = config_element['priority'] if given_priority is None else given_priority
            elif isinstance(config_element, List):
                for config in config_element:
                    if isinstance(config, YAMLBaseConfig):
                        config_with_priority = ConfigWithPriority(
                            config=config,
                            priority=priority if priority is not None else 0
                        )
                        self.add_config(config_with_priority)
            else:
                raise ValueError(f"Entries in the config files must be mapping containing a priority key "
                                 f"or a list of configs.")

    def load_string(self, string, priority: Optional[int] = None):
        """Load a yaml string including multiple configs or priorities."""
        try:
            config_data: List = yaml.load_all(string, Loader=self.yaml_loader)
        except (ParserError, ConstructorError) as e:
            raise e
        self.add_config_data(config_data, priority)

    def load_file(self, file_path: Path, priority: Optional[int] = None):
        """ Load a yaml file including multiple configs or priorities."""
        if not file_path.is_file():
            if file_path.with_suffix('.yaml').is_file():
                file_path = file_path.with_suffix('.yaml')
            else:
                raise FileNotFoundError(f'Could not find file {file_path}')

        with open(file_path) as file:
            try:
                config_data: List = yaml.load_all(file, Loader=self.yaml_loader)
                # pyyaml lazy loads, so file needs to stay open
                self.add_config_data(config_data, priority)
            except (ParserError, ConstructorError) as e:
                raise e

    def load_directory(self, directory_path: Path, priority: Optional[int] = None):
        """Load all files ending with .yaml from a directory."""
        if not directory_path.is_dir():
            raise NotADirectoryError(f"{directory_path} is not a directory.")
        for file_path in sorted(directory_path.glob("*.yaml")):
            self.load_file(file_path, priority)

    def construct_from_string(self, string: str, auto_load: bool = False):
        """Construct the configuration for a yaml string with a single yaml config."""
        try:
            config: Any = yaml.load(string, Loader=self.yaml_loader)
        except (ParserError, ConstructorError) as e:
            raise e
        return self.deep_construct_from_config(config, final=True, auto_load=auto_load)

    def construct_from_file(self, file_path: Path, auto_load: bool = False):
        """Construct the configuration for a yaml file with a single yaml config."""
        if not file_path.is_file():
            if file_path.with_suffix('.yaml').is_file():
                file_path = file_path.with_suffix('.yaml')
            else:
                raise FileNotFoundError(f'Could not find file "{file_path}"')
        with open(file_path) as file:
            try:
                config: Any = yaml.load(file, Loader=self.yaml_loader)
            except (ParserError, ConstructorError) as e:
                raise e
        return self.deep_construct_from_config(config, final=True, auto_load=auto_load)
