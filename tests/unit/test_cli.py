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
        cli.parse_args()


def test_parse_args_command_no_args():
    if os.environ.get('WORKON_DIR'):
        del os.environ['WORKON_DIR']
    sys.argv = ['workon', 'start', 'my_project']

    with pytest.raises(ScriptError):
        cli.parse_args()

    sys.argv = ['workon', 'done']
    with pytest.raises(ScriptError):
        cli.parse_args()


def test_parse_args_start_command_no_args_env_variables_set():
    sys.argv = ['workon', 'start', 'my_project']
    os.environ['WORKON_GIT_SOURCE'] = 'some'
    os.environ['WORKON_DIR'] = '/tmp'
    os.environ['WORKON_EDITOR'] = 'my_editor'

    assert cli.parse_args() == Namespace(
        command='start', directory='/tmp', force=False, source='some',
        verbose=0, project='my_project', noopen=False, editor='my_editor'
    )


def test_parse_args_open_command():
    sys.argv = ['workon', 'open', 'my_project']
    os.environ['WORKON_DIR'] = '/tmp'
    os.environ['WORKON_EDITOR'] = 'my_editor'
    assert cli.parse_args() == Namespace(
        command='open', directory='/tmp', verbose=0, project='my_project',
        editor='my_editor'
    )


def test_parse_args_cli_arg_overrides_env_variable():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        sys.argv = ['workon', 'start', 'my_project', '-d', tmp_dir_path, '-vv']
        os.environ['WORKON_GIT_SOURCE'] = 'some'
        os.environ['WORKON_DIR'] = '/tmp'
        os.environ['WORKON_EDITOR'] = 'code'

        assert cli.parse_args() == Namespace(
            command='start', directory=tmp_dir_path, force=False,
            source='some', verbose=2, project='my_project', noopen=False,
            editor='code'
        )


def test_directory_does_not_exist_created():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        specified_dir = tmp_dir_path + '/aa'
        sys.argv = [
            'workon', 'start', 'my_project', '-d', specified_dir, '-vv'
        ]

        cli.parse_args()
        assert os.path.isdir(specified_dir)


def test_directory_does_not_exist_failed_to_create():
    sys.argv = [
        'workon', 'start', 'my_project', '-d', '/a', '-vv'
    ]

    with pytest.raises(ScriptError):
        cli.parse_args()


def test_directory_exists_permissions_not_sufficient():
    tmp_dir_path = tempfile.mkdtemp()

    sys.argv = [
        'workon', 'start', 'my_project', '-d', tmp_dir_path, '-vv'
    ]
    os.chmod(tmp_dir_path, 0o000)

    with pytest.raises(ScriptError):
        cli.parse_args()
