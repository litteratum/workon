"""Tests for script.py."""
import os
import json
import tempfile
from argparse import Namespace
from unittest.mock import Mock, patch, call

import pytest
from workon import script
from workon.errors import ScriptError


def test_done_no_such_project():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(project='dummy', directory=tmp_dir_path)

        with pytest.raises(ScriptError):
            script.done(args)


@pytest.mark.parametrize('specific', [(True, False)])
def test_done_nonexistent_dir(specific):
    if specific:
        project = 'dummy'
    else:
        project = None

    args = Namespace(project=project, directory='ehehe')

    with pytest.raises(ScriptError):
        script.done(args)


def test_done_project_found_and_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)
        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        script.done(args)
        assert not os.path.exists(proj_path)


def test_done_all_filetypes_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        # project dir
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)
        # regular file
        tempfile.mktemp(dir=tmp_dir_path)
        # symlink
        src = tempfile.mktemp(dir=tmp_dir_path)
        dst = tempfile.mktemp(dir=tmp_dir_path)
        os.symlink(src, dst)
        # namedpipe
        os.mkfifo(os.path.join(tmp_dir_path, 'tmppipe'), 0o600)

        args = Namespace(
            project=None, directory=tmp_dir_path, force=False
        )
        script.done(args)
        assert not os.listdir(tmp_dir_path)


@patch('workon.script.git.is_stash_empty', Mock(return_value=False))
def test_done_project_found_git_stashed_error_raised():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        with pytest.raises(ScriptError):
            script.done(args)
        assert os.path.exists(proj_path)


@patch('workon.script.git.is_stash_empty', Mock(return_value=False))
def test_done_project_found_git_stashed_forced_ok():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=True
        )
        script.done(args)
        assert not os.path.exists(proj_path)


@patch(
    'workon.script.git.get_unpushed_branches_info', Mock(return_value='oops')
)
def test_done_project_found_git_unpushed_error_raised():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        with pytest.raises(ScriptError) as exc:
            script.done(args)
        assert 'oops' in str(exc.value)
        assert os.path.exists(proj_path)


@patch(
    'workon.script.git.get_unpushed_branches_info', Mock(return_value='oops')
)
def test_done_project_found_git_unpushed_forced_ok():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=True
        )
        script.done(args)
        assert not os.path.exists(proj_path)


@patch(
    'workon.script.git.get_unstaged_info', Mock(return_value='oops')
)
def test_done_project_found_git_unstaged():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        with pytest.raises(ScriptError) as exc:
            script.done(args)
        assert 'oops' in str(exc.value)
        assert os.path.exists(proj_path)


@patch(
    'workon.script.git.get_unstaged_info', Mock(return_value='oops')
)
def test_done_project_found_git_unstaged_forced_ok():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=True
        )
        script.done(args)
        assert not os.path.exists(proj_path)


def test_done_all_projects_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(directory=tmp_dir_path, project=None, force=False)
        script.done(args)

        assert len(os.listdir(tmp_dir_path)) == 0


@patch('workon.script.git.is_stash_empty')
def test_done_all_projects_couple_are_dirty_but_all_tried_to_be_removed(
        mc_is_stash_empty):
    mc_is_stash_empty.side_effect = (
        ScriptError, True, ScriptError, True
    )

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        tempfile.mkdtemp(dir=tmp_dir_path)
        tempfile.mkdtemp(dir=tmp_dir_path)
        tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(directory=tmp_dir_path, project=None, force=False)
        script.done(args)

        assert len(os.listdir(tmp_dir_path)) == 2


def test_done_all_projects_removed_all_files_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        tempfile.mkdtemp(dir=tmp_dir_path)
        tempfile.mkstemp(dir=tmp_dir_path)

        args = Namespace(directory=tmp_dir_path, project=None, force=False)
        script.done(args)

        assert len(os.listdir(tmp_dir_path)) == 0


@patch('workon.script.git.clone')
def test_start_working_directory_is_not_empty(mc_clone):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        proj_path = os.path.join(tmp_dir_path, 'some')

        mc_clone.side_effect = lambda *args, **kwargs: os.mkdir(proj_path)

        args = Namespace(
            project='some', directory=tmp_dir_path, source=['some'],
            noopen=True
        )
        script.start(args)
        assert os.path.isdir(proj_path)


@patch('workon.script.git.clone')
def test_start_no_such_project(mc_clone):
    mc_clone.side_effect = ScriptError

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(
            project='some', directory=tmp_dir_path, source=['some'],
            noopen=True
        )

        with pytest.raises(ScriptError):
            script.start(args)


@pytest.mark.parametrize('source,expected_source', [
    ('https://github.com/user', 'https://github.com/user/some.git'),
    ('https://github.com/user/', 'https://github.com/user/some.git'),
    ('https://github.com/user//', 'https://github.com/user/some.git'),
    ('git@github.com:user', 'git@github.com:user/some.git'),
    ('git@github.com:user/', 'git@github.com:user/some.git'),
    ('git@github.com:user//', 'git@github.com:user/some.git'),
])
@patch('workon.script.git.clone')
def test_start_cloned(mc_clone, source, expected_source):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = os.path.join(tmp_dir_path, 'some')
        mc_clone.side_effect = lambda *args, **kwargs: os.mkdir(proj_path)
        args = Namespace(
            project='some', directory=tmp_dir_path,
            source=[source], noopen=True
        )
        script.start(args)
        assert os.path.isdir(proj_path)

        mc_clone.assert_called_once_with(expected_source, proj_path)


@patch('workon.script.git.clone', Mock())
@patch('workon.script.subprocess')
def test_start_opens_specified_editor(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=0)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, 'some'))
        args = Namespace(
            project='some', directory=tmp_dir_path, source='some',
            noopen=False, editor='code'
        )
        script.start(args)
        mc_subprocess.run.assert_called_once_with(
            ['code', tmp_dir_path + '/some'], check=False
        )


@patch('workon.script.git.clone', Mock())
@patch('workon.script.subprocess')
def test_start_no_open(mc_subprocess):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(
            project='some', directory=tmp_dir_path, source='some',
            noopen=True
        )
        script.start(args)
        assert mc_subprocess.run.call_count == 0


@patch('workon.script.git.clone', Mock())
@patch('workon.script.subprocess')
def test_start_no_editor(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=1)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, 'some'))
        args = Namespace(
            project='some', directory=tmp_dir_path, source='some',
            noopen=False, editor='code'
        )

        with pytest.raises(ScriptError) as exc:
            script.start(args)
        assert 'No suitable editor' in str(exc.value)

        assert mc_subprocess.run.call_count == 4


@patch('workon.script.git.clone', Mock())
@patch('workon.script.subprocess')
def test_start_editor_from_env(mc_subprocess):
    mc_subprocess.run.side_effect = (Mock(returncode=1), Mock(returncode=0))

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, 'some'))
        args = Namespace(
            project='some', directory=tmp_dir_path, source='some',
            noopen=False, editor='code'
        )

        script.start(args)
        assert mc_subprocess.run.call_count == 2


def test_open_no_such_project():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(
            project='some', directory=tmp_dir_path, editor='code'
        )
        with pytest.raises(ScriptError):
            script.open_project(args)


@patch('workon.script.subprocess')
def test_open_ok(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=0)
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tmp_proj_path = tempfile.mkdtemp(dir=tmp_dir_path)
        args = Namespace(
            project=tmp_proj_path, directory=tmp_dir_path, editor='my_editor'
        )

        script.open_project(args)
        mc_subprocess.run.assert_called_once_with(
            ['my_editor', tmp_proj_path], check=False)


@patch('workon.script.subprocess')
def test_open_no_such_editor(mc_subprocess):
    mc_subprocess.run.side_effect = (FileNotFoundError, Mock(returncode=0))
    os.environ['EDITOR'] = 'some_env_editor'
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tmp_proj_path = tempfile.mkdtemp(dir=tmp_dir_path)
        args = Namespace(
            project=tmp_proj_path, directory=tmp_dir_path, editor='my_editor'
        )

        script.open_project(args)
        assert call(['some_env_editor', tmp_proj_path],
                    check=False) in mc_subprocess.run.call_args_list


def test_get_config():
    config = {'dir': 'some'}
    with tempfile.NamedTemporaryFile('w+') as file:
        json.dump(config, file)
        file.flush()

        with patch('workon.script.CONFIG_PATH', file.name):
            assert script.get_config() == config


def test_get_config_no_config_file():
    with patch('workon.script.CONFIG_PATH', 'nonexistent'):
        assert script.get_config() == {}


def test_get_config_wrong_json_file():
    with tempfile.NamedTemporaryFile('w+') as file:
        file.write('oops')
        file.flush()

        with patch('workon.script.CONFIG_PATH', file.name):
            assert script.get_config() == {}


@pytest.mark.parametrize('whats_wrong', [
    'dir', 'editor', 'source',
])
def test_get_config_invalid_config(whats_wrong):
    config = {
        'dir': 'some',
        'source': ['some', ],
        'editor': 'some'
    }

    config[whats_wrong] = 1

    with tempfile.NamedTemporaryFile('w+') as file:
        json.dump(config, file)
        file.flush()

        with patch('workon.script.CONFIG_PATH', file.name):
            with pytest.raises(ScriptError):
                script.get_config()
