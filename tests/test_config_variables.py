import pytest

from yaloader import YAMLValueError, YAMLBaseConfig


@pytest.fixture
def MultiAttrConfig(yaml_loader, config_loader):

    class Config(YAMLBaseConfig, yaml_loader=yaml_loader):
        _yaml_tag = '!MAC'
        attribute1: int = 0
        attribute2: int = 0
        attribute3: int = 0

        def load(self, *args, **kwargs):
            return (self.attribute1, self.attribute2, self.attribute3)

    return Config


def test_load_list(config_loader, AConfig):
    config_list = config_loader.construct_from_string(
        """
        - !A {attribute: 1}
        - !ConfigVarA {_tag: "!A", attribute: 2}
        - !ConfigVarB {_tag: "!A", attribute: 3}
        """
    )
    assert config_list == [AConfig(attribute=1), AConfig(attribute=2), AConfig(attribute=3)]


def test_auto_load(config_loader, AConfig):
    attribute_list = config_loader.construct_from_string(
        """
        - !A {attribute: 1}
        - !ConfigVarA {_tag: "!A", attribute: 2}
        - !ConfigVarB {_tag: "!A", attribute: 3}
        """,
        auto_load=True
    )
    assert attribute_list == [1, 2, 3]


def test_raise_on__tag_not_registered(config_loader, AConfig):
    with pytest.raises(YAMLValueError) as error:
        config_loader.construct_from_string('!ConfigVarA {_tag: "!B", attribute: 1}')


def test_raise_on_additional_attribute(config_loader, AConfig):
    with pytest.raises(YAMLValueError) as error:
        config_loader.construct_from_string("!ConfigVarA {_tag: '!A', xyz: 1}")


def test_raise_on_wrong_attribute_type(config_loader, AConfig):
    with pytest.raises(YAMLValueError) as error:
        config_loader.construct_from_string("!ConfigVarA {_tag: '!A', 'Some text': 1}")


def test_multi_load_list(config_loader, AConfig):
    config_loader.add_single_config_string("!A {attribute: 2}", priority=1)

    config_list = config_loader.construct_from_string(
        """
        - !A {}
        - !A {attribute: 2}
        - !ConfigVarABC {attribute: 1, _tag: "!A"}
        - !ConfigVarABC {_tag: "!A"}
        """
    )
    assert config_list == [AConfig(attribute=2), AConfig(attribute=2),
                           AConfig(attribute=1), AConfig(attribute=2)]


def test_multi_load_list_var_config(config_loader, AConfig):
    config_loader.add_single_config_string("!A {attribute: 2}", priority=1)
    config_loader.add_single_config_string("!ConfigVarABC {_tag: '!A', attribute: 3}", priority=1)

    config_list = config_loader.construct_from_string(
        """
        - !A {}
        - !A {attribute: 2}
        - !A {attribute: 1}
        - !ConfigVarABC {attribute: 1, _tag: "!A"}
        - !ConfigVarABC {_tag: "!A"}
        """
    )
    assert config_list == [AConfig(attribute=2), AConfig(attribute=2), AConfig(attribute=1),
                           AConfig(attribute=1), AConfig(attribute=3)]


def test_multi_load_list_var_inheritance(config_loader, AConfig):
    config_loader.add_single_config_string("!A {attribute: 2}", priority=1)
    config_loader.add_single_config_string("!ConfigVarABC {_tag: '!A', attribute: 3}", priority=1)
    config_loader.add_single_config_string("!ConfigVarABCA {_tag: '!ConfigVarABC'}", priority=1)

    config_list = config_loader.construct_from_string(
        """
        - !A {}
        - !A {attribute: 2}
        - !A {attribute: 1}
        - !ConfigVarABC {attribute: 1, _tag: "!A"}
        - !ConfigVarABC {_tag: "!A"}
        - !ConfigVarABCA {_tag: "!ConfigVarABC"}
        - !ConfigVarABCA {attribute: 1, _tag: "!ConfigVarABC"}
        """
    )
    assert config_list == [AConfig(attribute=2), AConfig(attribute=2), AConfig(attribute=1),
                           AConfig(attribute=1), AConfig(attribute=3),
                           AConfig(attribute=3), AConfig(attribute=1),
                           ]


def test_multi_load_list_multi_attr_var_inheritance(config_loader, MultiAttrConfig):
    config_loader.add_single_config_string("!MAC {attribute2: 2}", priority=1)
    config_loader.add_single_config_string("!ConfigVarABC {_tag: '!MAC', attribute3: 3}", priority=1)
    config_loader.add_single_config_string("!ConfigVarABCA {_tag: '!ConfigVarABC', attribute1: 1}", priority=1)

    config_list = config_loader.construct_from_string(
        """
        - !MAC {}
        - !ConfigVarABC {_tag: '!MAC'}
        - !ConfigVarABC {attribute1: 2, _tag: "!MAC"}
        - !ConfigVarABCA {_tag: '!ConfigVarABC'}
        - !ConfigVarABCA {attribute1: 2, _tag: '!ConfigVarABC'}
        - !ConfigVarABCA {attribute1: 2, attribute3: 1, _tag: '!ConfigVarABC'}
        """
    )
    assert config_list == [
        MultiAttrConfig(attribute1=0, attribute2=2, attribute3=0),
        MultiAttrConfig(attribute1=0, attribute2=2, attribute3=3),
        MultiAttrConfig(attribute1=2, attribute2=2, attribute3=3),
        MultiAttrConfig(attribute1=1, attribute2=2, attribute3=3),
        MultiAttrConfig(attribute1=2, attribute2=2, attribute3=3),
        MultiAttrConfig(attribute1=2, attribute2=2, attribute3=1),
    ]
