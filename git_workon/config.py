"""Module for dealing with the utility configuration."""
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import appdirs

_CONFIG_PATH = os.path.join(
    appdirs.user_config_dir("git_workon"), "config.json"
)
_CONFIG_TEMPLATE = {
    "dir": "~/git_workon",
    "editor": "",
    "sources": [],
}


class ConfigError(Exception):
    """Configuration error."""


@dataclass
class UserConfig:
    """User configuration."""

    dir: Optional[str]
    editor: Optional[str]
    sources: Optional[list]

    def __post_init__(self):
        if self.dir and not isinstance(self.dir, str):
            raise ConfigError(
                '"dir" parameter should be of string type'
            )
        if self.editor and not isinstance(self.editor, str):
            raise ConfigError(
                '"editor" parameter should be of string type'
            )
        if self.sources and not isinstance(self.sources, list):
            raise ConfigError(
                '"sources" parameter should be of array type'
            )


def load_config(path: str = _CONFIG_PATH) -> "UserConfig":
    """Load a configuration from path."""
    try:
        with open(path, encoding="utf8") as file:
            config = json.load(file)
    except (json.JSONDecodeError, OSError):
        config = {}

    return UserConfig(
        config.get("dir"), config.get("editor"), config.get("sources")
    )


def init_config(path: str = _CONFIG_PATH) -> None:
    """Initialize configuration.

    If the config file does not exists -> create it.
    """
    logging.info("Configuration is under %s", path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if not os.path.exists(path):
        logging.debug('Writing configuration template to "%s"', path)
        with open(path, "w", encoding="utf8") as file:
            json.dump(_CONFIG_TEMPLATE, file, indent=2)
