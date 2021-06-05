"""Tests for cli.py."""
import os
import sys
import tempfile
from argparse import Namespace

import pytest
from workon import cli
from workon.errors import ScriptError


def test_parse_args_no_args():
    sys.argv = ['workon']
    with pytest.raises(SystemExit):
        cli.parse_args(user_config={})


def test_parse_args_command_no_args():
    sys.argv = ['workon', 'start', 'my_project']

    with pytest.raises(ScriptError):
        cli.parse_args(user_config={})

    sys.argv = ['workon', 'done']
    with pytest.raises(ScriptError):
        cli.parse_args(user_config={})


def test_parse_args_start_command_no_args_config_variables_set():
    sys.argv = ['workon', 'start', 'my_project']

    user_config = {
        'dir': '/tmp', 'editor': 'my_editor', 'source': ['some']
    }

    assert cli.parse_args(user_config) == Namespace(
        command='start', directory='/tmp', source=['some'],
        verbose=0, project='my_project', noopen=False, editor='my_editor'
    )


def test_parse_args_start_command_source_extended_from_config():
    sys.argv = ['workon', 'start', 'my_project', '-s', 'some', '-s', 'another']

    user_config = {
        'dir': '/tmp', 'editor': 'my_editor', 'source': ['from_config']
    }
    expected_source = ['some', 'another', 'from_config']

    assert cli.parse_args(user_config) == Namespace(
        command='start', directory='/tmp', source=expected_source,
        verbose=0, project='my_project', noopen=False, editor='my_editor'
    )


def test_parse_args_open_command():
    sys.argv = ['workon', 'open', 'my_project']
    user_config = {
        'dir': '/tmp', 'editor': 'my_editor'
    }

    assert cli.parse_args(user_config) == Namespace(
        command='open', directory='/tmp', verbose=0, project='my_project',
        editor='my_editor'
    )


def test_parse_args_cli_arg_overrides_config_variable():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        sys.argv = ['workon', 'start', 'my_project', '-d', tmp_dir_path, '-vv']

        user_config = {
            'dir': '/tmp', 'editor': 'code', 'source': ['some']
        }

        assert cli.parse_args(user_config) == Namespace(
            command='start', directory=tmp_dir_path,
            source=['some'], verbose=2, project='my_project', noopen=False,
            editor='code'
        )


def test_directory_does_not_exist_created():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        specified_dir = tmp_dir_path + '/aa'
        sys.argv = [
            'workon', 'start', 'my_project', '-d', specified_dir, '-vv',
            '-s', 'some'
        ]

        cli.parse_args(user_config={})
        assert os.path.isdir(specified_dir)


def test_directory_does_not_exist_failed_to_create():
    sys.argv = [
        'workon', 'start', 'my_project', '-d', '/a', '-vv'
    ]

    with pytest.raises(ScriptError):
        cli.parse_args(user_config={})


def test_directory_exists_permissions_not_sufficient():
    tmp_dir_path = tempfile.mkdtemp()

    sys.argv = [
        'workon', 'start', 'my_project', '-d', tmp_dir_path, '-vv'
    ]
    os.chmod(tmp_dir_path, 0o000)

    with pytest.raises(ScriptError):
        cli.parse_args(user_config={})


def test_parse_args_directory_path_expanded():
    sys.argv = ['workon', 'start', 'my_project']

    user_config = {
        'dir': '~', 'editor': 'my_editor', 'source': ['some']
    }

    assert cli.parse_args(user_config) == Namespace(
        command='start', directory=os.environ.get('HOME'), source=['some'],
        verbose=0, project='my_project', noopen=False, editor='my_editor'
    )
