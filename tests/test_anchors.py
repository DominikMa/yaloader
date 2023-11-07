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
