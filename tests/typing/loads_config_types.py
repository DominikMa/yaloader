from __future__ import annotations

from typing import Optional

from typing_extensions import assert_type

from yaloader import YAMLBaseConfig, loads


@loads(None)
class OptimizerConfig(YAMLBaseConfig):
    params: list[dict[str, float]] | None = None


@loads(None)
class ScheduledOptimizerConfig(OptimizerConfig):
    interval: int = 1


assert_type(OptimizerConfig, type[OptimizerConfig])
assert_type(ScheduledOptimizerConfig, type[ScheduledOptimizerConfig])
assert_type(OptimizerConfig(), OptimizerConfig)
assert_type(ScheduledOptimizerConfig(), ScheduledOptimizerConfig)


def inspect_config(config: OptimizerConfig) -> None:
    assert_type(config, OptimizerConfig)
    assert_type(config.params, Optional[list[dict[str, float]]])


def inspect_scheduled_config(config: ScheduledOptimizerConfig) -> None:
    assert_type(config, ScheduledOptimizerConfig)
    assert_type(config.params, Optional[list[dict[str, float]]])
    assert_type(config.interval, int)
