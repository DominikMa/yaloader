from __future__ import annotations

from typing import Optional, Type

from pydantic import BaseModel, ConfigDict, ValidationError

from yaloader.utils import full_object_name, remove_missing_errors


class VarYAMLConfigBase:
    pass


class YAMLBaseConfig(BaseModel):
    """The base class for all config objects which are loaded from or dumped to yaml files.

    Each config from which an actual object can be created has to implement
    the :meth:`YAMLBaseConfig.load()` method.
    """

    _loaded_class: Optional[Type] = None
    """The class which is loaded by the configuration. 
    Can be None if the loaded class is explicitly specified in the load method."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    """Since yaml configs are used to create instances extra fields are forbidden."""

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
        """Assert that the config has a valid yaml tag.

        If the tag is not set yet, try to set it to a default value.
        """
        yaml_tag = getattr(cls, f"_{cls.__name__}__yaml_tag", None)
        if yaml_tag is None or not isinstance(yaml_tag, str):
            # Set yaml tag to default case: class name without `Config` suffix
            class_name = cls.__name__
            if not class_name.endswith("Config"):
                raise RuntimeError(
                    f"Config class {cls.__name__} has not yaml tag. "
                    f"If the tag should be derived automatically the "
                    f"class name has to end with `Config`"
                )
            class_name = class_name.removesuffix("Config")
            yaml_tag = f"!{class_name}"
        elif not yaml_tag.startswith("!"):
            raise RuntimeError(
                f"The tag of config class {full_object_name(cls)} does not start with !"
            )
        setattr(cls, f"_{cls.__name__}__yaml_tag", yaml_tag)

    def validate_config(self, force_all: bool = False) -> None:
        """Validate a BaseConfig instance

        If force_all is False do not raise an error on missing attributes.
        Configs have to be correct but may be incomplete.

        :param force_all: If True raise an error on missing attributes
        """
        try:
            self.model_validate(dict(self))
        except ValidationError as e:
            if force_all:
                raise
            not_missing_errors = remove_missing_errors(e.errors())
            if len(not_missing_errors) > 0:
                # noinspection PyTypeChecker
                raise ValidationError.from_exception_data(title=e.title, line_errors=not_missing_errors)

    def load(self, *args, **kwargs):
        """Create the object the yaml config object is for.

        This basic constructor uses all attributes of the config as kwargs for the loaded class.
        """
        if hasattr(self, "_loaded_class") and self._loaded_class is not None:
            return self._loaded_class(**dict(self))
        raise NotImplementedError
