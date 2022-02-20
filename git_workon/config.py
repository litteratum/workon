"""Module for dealing with the utility configuration."""
import json
import logging
import os
import shutil

import pkg_resources


class ConfigError(Exception):
    """Configuration error."""


def _validate_config(user_config):
    if user_config.get("dir") and not isinstance(user_config["dir"], str):
        raise ConfigError('"dir" parameter should be of string type')
    if user_config.get("editor") and not isinstance(user_config["editor"], str):
        raise ConfigError('"editor" parameter should be of string type')
    if user_config.get("source") and not isinstance(user_config["source"], list):
        raise ConfigError('"source" parameter should be of array type')

    return user_config


def get_config(path: str) -> dict:
    """Return config loaded from `_CONFIG_PATH`."""
    try:
        with open(path, encoding="utf8") as file:
            user_config = json.load(file)
    except json.JSONDecodeError as exc:
        logging.warning("Failed to load user config file: %s. Skipping", exc)
        user_config = {}
    except OSError as exc:
        logging.warning("Failed to load user configuration file: %s. Skipping", exc)
        user_config = {}

    return _validate_config(user_config)


def init_config(path: str) -> None:
    """Initialize configuration.

    If the config file does not exists -> create it.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if not os.path.exists(path):
        logging.debug('Copying config template to "%s"', path)
        shutil.copy(pkg_resources.resource_filename("git_workon", "config.json"), path)
