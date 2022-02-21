"""Tests for config.py module."""
# pylint:disable=missing-function-docstring
import json
import os
import tempfile

import pytest
from git_workon import config as config_module


def test_get_config():
    config = {"dir": "some"}
    with tempfile.NamedTemporaryFile("w+") as file:
        json.dump(config, file)
        file.flush()
        assert config_module.load_config(file.name) == config_module.UserConfig(
            dir="some", editor=None, sources=None
        )


def test_get_config_no_config_file():
    assert config_module.load_config("nonexistent") == config_module.UserConfig(
        dir=None, editor=None, sources=None
    )


def test_get_config_wrong_json_file():
    with tempfile.NamedTemporaryFile("w+") as file:
        file.write("oops")
        file.flush()

        assert config_module.load_config(file.name) == config_module.UserConfig(
            dir=None, editor=None, sources=None
        )


@pytest.mark.parametrize(
    "whats_wrong",
    [
        "dir",
        "editor",
        "sources",
    ],
)
def test_get_config_invalid_config(whats_wrong):
    config = {"dir": "some", "sources": ["some"], "editor": "some", whats_wrong: 1}

    with tempfile.NamedTemporaryFile("w+") as file:
        json.dump(config, file)
        file.flush()
        with pytest.raises(config_module.ConfigError):
            config_module.load_config(file.name)


def test_init_config_config_does_not_exist_created():
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "config.json")
        config_module.init_config(path)

        with open(path, encoding="utf-8") as file:
            # pylint:disable=protected-access
            assert json.load(file) == config_module._CONFIG_TEMPLATE
