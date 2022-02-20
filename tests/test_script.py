"""Tests for script.py."""
# pylint:disable=missing-function-docstring
import os
import tempfile
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from git_workon import git, script
from git_workon.script import ScriptError


def add_git_project(directory: str) -> str:
    """Add git project to the `directory`.

    :returns: path to the GIT project
    """
    proj_dir = tempfile.mkdtemp(dir=directory)
    os.mkdir(os.path.join(proj_dir, ".git"))
    return proj_dir


def test_done_no_such_project():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(project="dummy", directory=tmp_dir_path)

        with pytest.raises(ScriptError):
            script.done(args)


@pytest.mark.parametrize("specific", [(True, False)])
def test_done_nonexistent_dir(specific):
    project = "dummy" if specific else None
    args = Namespace(project=project, directory="ehehe")

    with pytest.raises(ScriptError):
        script.done(args)


@patch("git_workon.script.git.check_all_pushed", Mock(return_value=None))
def test_done_project_found_and_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)
        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path, force=False
        )
        script.done(args)
        assert not os.path.exists(proj_path)


@patch("git_workon.script.git.check_all_pushed", Mock(return_value=None))
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
        os.mkfifo(os.path.join(tmp_dir_path, "tmppipe"), 0o600)

        args = Namespace(project=None, directory=tmp_dir_path, force=False)
        script.done(args)
        assert not os.listdir(tmp_dir_path)


@patch(
    "git_workon.script.git.check_all_pushed",
    Mock(side_effect=git.GITError("something")),
)
def test_done_project_found_something_unpushed_error_raised():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = add_git_project(tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path, force=False
        )
        with pytest.raises(ScriptError):
            script.done(args)
        assert os.path.exists(proj_path)


@patch("git_workon.script.git.check_all_pushed", Mock(return_value="something"))
def test_done_project_found_git_stashed_forced_ok():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = tempfile.mkdtemp(dir=tmp_dir_path)

        args = Namespace(
            project=os.path.basename(proj_path), directory=tmp_dir_path, force=True
        )
        script.done(args)
        assert not os.path.exists(proj_path)


@patch("git_workon.script.git.check_all_pushed", Mock(return_value=None))
def test_done_all_projects_removed():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        for _ in range(2):
            add_git_project(tmp_dir_path)

        args = Namespace(directory=tmp_dir_path, project=None, force=False)
        script.done(args)

        assert len(os.listdir(tmp_dir_path)) == 0


@patch("git_workon.script.git.check_all_pushed")
def test_done_all_projects_couple_are_dirty_but_all_tried_to_be_removed(
    mc_check_all_pushed,
):
    mc_check_all_pushed.side_effect = (git.GITError, None, git.GITError, None)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        for _ in range(4):
            add_git_project(tmp_dir_path)

        args = Namespace(directory=tmp_dir_path, project=None, force=False)
        script.done(args)

        assert len(os.listdir(tmp_dir_path)) == 2


@patch("git_workon.script.git.clone")
def test_start_working_directory_is_not_empty_project_cloned(mc_clone):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        proj_path = os.path.join(tmp_dir_path, "some")

        mc_clone.side_effect = lambda *args, **kwargs: os.mkdir(proj_path)

        args = Namespace(
            project="some", directory=tmp_dir_path, source=["some"], noopen=True
        )
        script.start(args)
        assert os.path.isdir(proj_path)


@patch("git_workon.script.git.clone")
def test_start_no_such_project(mc_clone):
    mc_clone.side_effect = ScriptError

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(
            project="some", directory=tmp_dir_path, source=["some"], noopen=True
        )

        with pytest.raises(ScriptError):
            script.start(args)


@pytest.mark.parametrize(
    "source,expected_source",
    [
        ("https://github.com/user", "https://github.com/user/some.git"),
        ("https://github.com/user/", "https://github.com/user/some.git"),
        ("https://github.com/user//", "https://github.com/user/some.git"),
        ("git@github.com:user", "git@github.com:user/some.git"),
        ("git@github.com:user/", "git@github.com:user/some.git"),
        ("git@github.com:user//", "git@github.com:user/some.git"),
    ],
)
@patch("git_workon.script.git.clone")
def test_start_cloned(mc_clone, source, expected_source):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        proj_path = os.path.join(tmp_dir_path, "some")
        mc_clone.side_effect = lambda *args, **kwargs: os.mkdir(proj_path)
        args = Namespace(
            project="some", directory=tmp_dir_path, source=[source], noopen=True
        )
        script.start(args)
        assert os.path.isdir(proj_path)

        mc_clone.assert_called_once_with(expected_source, proj_path)


@patch("git_workon.script.git.clone", Mock())
@patch("git_workon.script.subprocess")
def test_start_opens_specified_editor(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=0)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, "some"))
        args = Namespace(
            project="some",
            directory=tmp_dir_path,
            source=["some"],
            noopen=False,
            editor="code",
        )
        script.start(args)
        mc_subprocess.run.assert_called_once_with(
            ["code", tmp_dir_path + "/some"], check=False
        )


@patch("git_workon.script.git.clone", Mock())
@patch("git_workon.script.subprocess")
def test_start_no_open(mc_subprocess):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        args = Namespace(
            project="some", directory=tmp_dir_path, source=["some"], noopen=True
        )
        script.start(args)
        assert mc_subprocess.run.call_count == 0


@patch("git_workon.script.git.clone", Mock())
@patch("git_workon.script.subprocess")
def test_start_no_editor(mc_subprocess):
    # this test assumes that this ENV variable is set
    os.environ["EDITOR"] = "env_editor"
    mc_subprocess.run.return_value = Mock(returncode=1)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, "some"))
        args = Namespace(
            project="some",
            directory=tmp_dir_path,
            source=["some"],
            noopen=False,
            editor="code",
        )

        with pytest.raises(ScriptError) as exc:
            script.start(args)
        assert "No suitable editor" in str(exc.value)

        assert mc_subprocess.run.call_count == 4


@patch("git_workon.script.git.clone", Mock())
@patch("git_workon.script.subprocess")
def test_start_editor_from_env(mc_subprocess):
    mc_subprocess.run.side_effect = (Mock(returncode=1), Mock(returncode=0))

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, "some"))
        args = Namespace(
            project="some",
            directory=tmp_dir_path,
            source=["some"],
            noopen=False,
            editor="code",
        )

        script.start(args)
        assert mc_subprocess.run.call_count == 2


@patch("git_workon.script._open_project")
def test_start_project_exists_should_be_opened(mc_open_project):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(os.path.join(tmp_dir_path, "some"))
        args = Namespace(
            project="some",
            directory=tmp_dir_path,
            source=["some"],
            noopen=False,
            editor="code",
        )
        script.start(args)
        mc_open_project.assert_called_once_with(
            args.directory, args.project, args.editor  # pylint:disable=no-member
        )

@patch("git_workon.script.subprocess")
def test_config_command_creates_config_dir(mc_subprocess):
    mc_subprocess.run.return_value = Mock(returncode=0)
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        config_dir = os.path.join(tmp_dir_path, "config_dir")
        config_path = os.path.join(config_dir, "config.json")
        assert not os.path.exists(config_dir)

        with patch.object(script, "CONFIG_PATH", config_path):
            script.config(Namespace(editor="vi"))

        assert os.path.exists(config_path)
