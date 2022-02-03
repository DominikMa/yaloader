from src.yaloader import YAMLBaseConfig


def test_load_list(empty_yaml_loader, empty_config_loader):

    class AConfig(YAMLBaseConfig, yaml_loader=empty_yaml_loader):
        attribute: int = 0

    config_list = empty_config_loader.construct_from_string(
        """
        - !A {attribute: 1}
        - !A {attribute: 2}
        - !A {attribute: 3}
        """
    )
    assert config_list == [AConfig(attribute=1), AConfig(attribute=2), AConfig(attribute=3)]


def test_auto_load(empty_yaml_loader, empty_config_loader):

    class AConfig(YAMLBaseConfig, yaml_loader=empty_yaml_loader):
        attribute: int = 0

        def load(self, *args, **kwargs):
            return self.attribute

    attribute_list = empty_config_loader.construct_from_string(
        """
        - !A {attribute: 1}
        - !A {attribute: 2}
        - !A {attribute: 3}
        """,
        auto_load=True
    )
    assert attribute_list == [1, 2, 3]
