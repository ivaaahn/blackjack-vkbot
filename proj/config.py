from collections import Mapping
from typing import TypeVar

import yaml


def setup_config(config_path: str) -> Mapping:
    with open(config_path, "r") as f:
        raw_config = yaml.full_load(f)

    return raw_config


ConfigType = TypeVar("ConfigType")
