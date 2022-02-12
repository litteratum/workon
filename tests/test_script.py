"""Tests for script.py."""
import os
import json
import tempfile
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from git_workon import script
from git_workon.script import ScriptError


def add_git_project(directory: str) -> str:
    """Add git project to the `directory`.

    :returns: path to the GIT project
    """
    proj_dir = tempfile.mkdtemp(dir=directory)
    os.mkdir(os.path.join(proj_dir, '.git'))
    return proj_dir


def test_done_no_such_project():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(project='dummy', directory=tmp_dir_path)

        with pytest.raises(ScriptError):
            script.done(args)


@pytest.mark.parametrize('specific', [(True, False)])
def test_done_nonexistent_dir(specific):
    project = 'dummy' if specific else None
    args = Namespace(project=project, directory='ehehe')

    with pytest.raises(ScriptError):
        script.done(args)


@patch('git_workon.script.git.get_unpushed_tags', Mock(return_value=''))
def test_done_project_found_and_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)
        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        script.done(args)
        assert not os.path.exists(proj_path)


@patch('git_workon.script.git.get_unpushed_tags', Mock(return_value=''))
def test_done_all_filetypes_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        # project dir
        tempfile.mkdtemp(dir=tmp_dir_path)
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


@patch('git_workon.script.git.get_stash_info', Mock(return_value='stash'))
def test_done_project_found_git_stashed_error_raised():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = add_git_project(tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        with pytest.raises(ScriptError):
            script.done(args)
        assert os.path.exists(proj_path)


@patch('git_workon.script.git.get_stash_info', Mock(return_value='stash'))
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
    'git_workon.script.git.get_unpushed_branches_info', Mock(
        return_value='oops')
)
def test_done_project_found_git_unpushed_error_raised():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = add_git_project(tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        with pytest.raises(ScriptError) as exc:
            script.done(args)
        assert 'oops' in str(exc.value)
        assert os.path.exists(proj_path)


@patch(
    'git_workon.script.git.get_unpushed_branches_info', Mock(
        return_value='oops')
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
    'git_workon.script.git.get_unstaged_info', Mock(return_value='oops')
)
def test_done_project_found_git_unstaged():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = add_git_project(tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        with pytest.raises(ScriptError) as exc:
            script.done(args)
        assert 'oops' in str(exc.value)
        assert os.path.exists(proj_path)


@patch(
    'git_workon.script.git.get_unstaged_info', Mock(return_value='oops')
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


@patch('git_workon.script.git.get_stash_info')
@patch('git_workon.script.git.get_unpushed_branches_info')
@patch('git_workon.script.git.get_unstaged_info')
@patch('git_workon.script.git.get_unpushed_tags')
def test_done_project_found_all_unpushed(
        mc_tags, mc_unstaged, mc_unpushed, mc_stashed):
    unstaged = 'M somefile.txt'
    unpushed = 'hash (branch1) message'
    stashed = 'stash1\nstash2'
    tags = (
        'To github.com:user/proj.git\n* [new tag]         1.1.0 -> 1.1.0\n'
        '* [new tag]         1.2 -> 1.2'
    )

    mc_unstaged.return_value = unstaged
    mc_unpushed.return_value = unpushed
    mc_stashed.return_value = stashed
    mc_tags.return_value = tags

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = add_git_project(tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path,
            force=False
        )
        with pytest.raises(ScriptError) as exc:
            script.done(args)

        for message in (unstaged, unpushed, stashed, tags,):
            assert message in str(exc.value)
        assert os.path.exists(proj_path)


@patch('git_workon.script.git.get_unpushed_tags', Mock(return_value=''))
def test_done_all_projects_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        for _ in range(2):
            add_git_project(tmp_dir_path)

        args = Namespace(directory=tmp_dir_path, project=None, force=False)
        script.done(args)

        assert len(os.listdir(tmp_dir_path)) == 0


@patch('git_workon.script.git.get_stash_info')
@patch('git_workon.script.git.get_unpushed_tags', Mock(return_value=''))
def test_done_all_projects_couple_are_dirty_but_all_tried_to_be_removed(
        mc_get_stash_info):
    mc_get_stash_info.side_effect = (
        ScriptError, '', ScriptError, ''
    )

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        for _ in range(4):
            add_git_project(tmp_dir_path)

        args = Namespace(directory=tmp_dir_path, project=None, force=False)
        script.done(args)

        assert len(os.listdir(tmp_dir_path)) == 2


@patch('git_workon.script.git.clone')
def test_start_working_directory_is_not_empty_project_cloned(mc_clone):
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


@patch('git_workon.script.git.clone')
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
@patch('git_workon.script.git.clone')
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


@patch('git_workon.script.git.clone', Mock())
@patch('git_workon.script.subprocess')
def test_start_opens_specified_editor(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=0)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, 'some'))
        args = Namespace(
            project='some', directory=tmp_dir_path, source=['some'],
            noopen=False, editor='code'
        )
        script.start(args)
        mc_subprocess.run.assert_called_once_with(
            ['code', tmp_dir_path + '/some'], check=False
        )


@patch('git_workon.script.git.clone', Mock())
@patch('git_workon.script.subprocess')
def test_start_no_open(mc_subprocess):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(
            project='some', directory=tmp_dir_path, source=['some'],
            noopen=True
        )
        script.start(args)
        assert mc_subprocess.run.call_count == 0


@patch('git_workon.script.git.clone', Mock())
@patch('git_workon.script.subprocess')
def test_start_no_editor(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=1)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, 'some'))
        args = Namespace(
            project='some', directory=tmp_dir_path, source=['some'],
            noopen=False, editor='code'
        )

        with pytest.raises(ScriptError) as exc:
            script.start(args)
        assert 'No suitable editor' in str(exc.value)

        assert mc_subprocess.run.call_count == 4


@patch('git_workon.script.git.clone', Mock())
@patch('git_workon.script.subprocess')
def test_start_editor_from_env(mc_subprocess):
    mc_subprocess.run.side_effect = (Mock(returncode=1), Mock(returncode=0))

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, 'some'))
        args = Namespace(
            project='some', directory=tmp_dir_path, source=['some'],
            noopen=False, editor='code'
        )

        script.start(args)
        assert mc_subprocess.run.call_count == 2


@patch('git_workon.script._open_project')
def test_start_project_exists_should_be_opened(mc_open_project):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, 'some'))
        args = Namespace(
            project='some', directory=tmp_dir_path, source=['some'],
            noopen=False, editor='code'
        )
        script.start(args)
        mc_open_project.assert_called_once_with(
            args.directory, args.project, args.editor
        )


def test_get_config():
    config = {'dir': 'some'}
    with tempfile.NamedTemporaryFile('w+') as file:
        json.dump(config, file)
        file.flush()

        with patch('git_workon.script._CONFIG_PATH', file.name):
            assert script.get_config() == config


def test_get_config_no_config_file():
    with patch('git_workon.script._CONFIG_PATH', 'nonexistent'):
        assert script.get_config() == {}


def test_get_config_wrong_json_file():
    with tempfile.NamedTemporaryFile('w+') as file:
        file.write('oops')
        file.flush()

        with patch('git_workon.script._CONFIG_PATH', file.name):
            assert script.get_config() == {}


@pytest.mark.parametrize('whats_wrong', [
    'dir', 'editor', 'source',
])
def test_get_config_invalid_config(whats_wrong):
    config = {
        'dir': 'some', 'source': ['some'], 'editor': 'some', whats_wrong: 1
    }

    with tempfile.NamedTemporaryFile('w+') as file:
        json.dump(config, file)
        file.flush()

        with patch('git_workon.script._CONFIG_PATH', file.name):
            with pytest.raises(ScriptError):
                script.get_config()


@patch('git_workon.script.subprocess')
def test_config_command_creates_config_dir(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=0)
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        config_dir = os.path.join(tmp_dir_path, "config_dir")
        config_path = os.path.join(config_dir, "config.json")
        assert not os.path.exists(config_dir)

        with patch.object(script, "_CONFIG_DIR", config_dir):
            with patch.object(script, "_CONFIG_PATH", config_path):
                script.config(Namespace(editor="vi"))

        assert os.path.exists(config_path)
