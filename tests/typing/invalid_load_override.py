# pyright: reportIncompatibleMethodOverride=true

from yaloader import YAMLBaseConfig, loads


@loads()
class InvalidConfig(YAMLBaseConfig[int]):
    def load(self) -> str:
        return "not an int"
