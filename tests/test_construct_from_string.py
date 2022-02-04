def test_load_list(yaml_loader, config_loader, AConfig):
    config_list = config_loader.construct_from_string(
        """
        - !A {attribute: 1}
        - !A {attribute: 2}
        - !A {attribute: 3}
        """
    )
    assert config_list == [AConfig(attribute=1), AConfig(attribute=2), AConfig(attribute=3)]


def test_auto_load(yaml_loader, config_loader, AConfig):
    attribute_list = config_loader.construct_from_string(
        """
        - !A {attribute: 1}
        - !A {attribute: 2}
        - !A {attribute: 3}
        """,
        auto_load=True
    )
    assert attribute_list == [1, 2, 3]
