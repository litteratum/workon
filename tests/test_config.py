"""Tests for config.py module."""
# pylint:disable=missing-function-docstring
import json
import tempfile

import pytest
from git_workon import config as config_module


def test_get_config():
    config = {"dir": "some"}
    with tempfile.NamedTemporaryFile("w+") as file:
        json.dump(config, file)
        file.flush()
        assert config_module.get_config(file.name) == config


def test_get_config_no_config_file():
    assert config_module.get_config("nonexistent") == {}


def test_get_config_wrong_json_file():
    with tempfile.NamedTemporaryFile("w+") as file:
        file.write("oops")
        file.flush()

        assert config_module.get_config(file.name) == {}


@pytest.mark.parametrize(
    "whats_wrong",
    [
        "dir",
        "editor",
        "source",
    ],
)
def test_get_config_invalid_config(whats_wrong):
    config = {"dir": "some", "source": ["some"], "editor": "some", whats_wrong: 1}

    with tempfile.NamedTemporaryFile("w+") as file:
        json.dump(config, file)
        file.flush()
        with pytest.raises(config_module.ConfigError):
            config_module.get_config(file.name)
