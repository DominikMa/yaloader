import pytest
from yaml.composer import ComposerError


def test_anchor_single_document(config_loader, AConfig):
    config_list = config_loader.construct_from_string(
        """
        - !A {attribute: &name 1}
        - !A {attribute: *name}
        """
    )
    assert config_list == [AConfig(attribute=1), AConfig(attribute=1)]


def test_anchor_multiple_document(config_loader, AConfig):
    config_loader.load_string(
        """
        - attribute: &name 1
        """
    )
    config_list = config_loader.construct_from_string(
        """
        - !A {attribute: *name}
        - !A {attribute: 2}
        """
    )
    assert config_list == [AConfig(attribute=1), AConfig(attribute=2)]


def test_fail_on_missing_anchor(config_loader, AConfig):
    with pytest.raises(ComposerError) as error:
        config_loader.load_string(
            """
            - !A {attribute: *name}
            """
        )


def test_fail_on_same_anchor_name(config_loader, AConfig):
    with pytest.raises(ComposerError) as error:
        config_loader.load_string(
            """
            - !A {attribute: &name 1}
            - !A {attribute: &name 2}
            """
        )


def test_anchors_isolated_between_config_loaders(yaml_loader, AConfig):
    """Anchors from one ConfigLoader must not leak into another."""
    from yaloader import ConfigLoader

    loader_a = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader_a.load_string(
        """
        - attribute: &shared 42
        """
    )

    loader_b = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ComposerError):
        loader_b.load_string(
            """
            - !A {attribute: *shared}
            """
        )


def test_anchors_do_not_leak_back_to_parent_yaml_loader(yaml_loader, AConfig):
    """Loading anchors in a ConfigLoader must not pollute the parent yaml_loader class."""
    from yaloader import ConfigLoader

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string(
        """
        - attribute: &leaked 99
        """
    )

    assert yaml_loader.anchors == {}, "Parent yaml_loader anchors dict should remain empty"


def test_two_loaders_same_anchor_name_independent(yaml_loader, AConfig):
    """Two ConfigLoaders defining the same anchor name should each resolve their own value."""
    from yaloader import ConfigLoader

    loader_a = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader_a.load_string(
        """
        - attribute: &val 10
        """
    )

    loader_b = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader_b.load_string(
        """
        - attribute: &val 20
        """
    )

    result_a = loader_a.construct_from_string("!A {attribute: *val}")
    result_b = loader_b.construct_from_string("!A {attribute: *val}")

    assert result_a == AConfig(attribute=10)
    assert result_b == AConfig(attribute=20)


def test_config_registered_after_config_loader_creation(yaml_loader):
    """Configs registered after ConfigLoader instantiation should be visible via shared yaml_config_classes."""
    import yaloader.constructor
    from yaloader import ConfigLoader, YAMLBaseConfig

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)

    @yaloader.constructor.loads(yaml_loader=yaml_loader)
    class LateConfig(YAMLBaseConfig):
        _yaml_tag = "!Late"
        value: int = 0

        def load(self, *args, **kwargs):
            return self.value

    result = loader.construct_from_string("!Late {value: 7}")
    assert result == LateConfig(value=7)


def test_construct_from_string_does_not_leak_anchors(yaml_loader, AConfig):
    """Anchors defined during construct_from_string on one loader must not be visible to another."""
    from yaloader import ConfigLoader

    loader_a = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader_a.construct_from_string("!A {attribute: &cval 55}")

    loader_b = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ComposerError):
        loader_b.construct_from_string("!A {attribute: *cval}")


def test_anchors_persist_across_multiple_load_string_calls(yaml_loader, AConfig):
    """Anchors from earlier load_string calls should be available in later ones on the same loader."""
    from yaloader import ConfigLoader

    loader = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader.load_string(
        """
        - attribute: &first 1
        """
    )
    loader.load_string(
        """
        - attribute: &second 2
        """
    )

    result = loader.construct_from_string(
        """
        - !A {attribute: *first}
        - !A {attribute: *second}
        """
    )
    assert result == [AConfig(attribute=1), AConfig(attribute=2)]


def test_isolation_with_pre_existing_anchors_on_parent(yaml_loader, AConfig):
    """A ConfigLoader created from a yaml_loader that already has class-level anchors
    should NOT inherit those anchors."""
    from yaloader import ConfigLoader

    # First loader adds anchors to its IsolatedLoader
    loader_first = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    loader_first.load_string(
        """
        - attribute: &preexisting 77
        """
    )

    # A new ConfigLoader should start with a clean anchor slate
    loader_second = ConfigLoader(yaml_loader=yaml_loader, cacheing=False)
    with pytest.raises(ComposerError):
        loader_second.construct_from_string("!A {attribute: *preexisting}")
