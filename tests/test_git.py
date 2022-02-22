"""Tests for git.py."""
# pylint:disable=missing-function-docstring, no-self-use
import os
import re
import shutil
import subprocess
import tempfile
from collections import namedtuple
from dataclasses import dataclass
from typing import Iterable
from unittest import TestCase
from unittest.mock import Mock, call, patch

import pytest
from git_workon import git

DummyGitProject = namedtuple("DummyProject", ["name", "path"])


class TmpGitDir:
    """Temporary GIT directory."""

    def __init__(self, initial_commit=False) -> None:
        self.path = tempfile.mkdtemp()
        self.initial_commit = initial_commit

        self._git_init()

    def _git_init(self):
        subprocess.run(["git", "init"], cwd=self.path, check=True)

        if self.initial_commit:
            os.mknod(os.path.join(self.path, "some"))
            self.add()
            self.commit()

    def add(self, files: Iterable[str] = None):
        if not files:
            subprocess.run(["git", "add", "--all"], cwd=self.path, check=True)
        else:
            for file in files:
                subprocess.run(["git", "add", file], cwd=self.path, check=True)

    def stash(self, include_untracked=True):
        command = ["git", "stash"]
        if include_untracked:
            command.append("--include-untracked")

        subprocess.run(command, cwd=self.path, check=True)

    def checkout(self, branch, create=True):
        command = ["git", "checkout", "-b" if create else "", branch]
        subprocess.run(command, cwd=self.path, check=True)

    def commit(self, message="dummy"):
        subprocess.run(["git", "commit", "-m", message], cwd=self.path, check=True)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        shutil.rmtree(self.path)


def test_is_git_dir():
    with TmpGitDir() as git_dir:
        assert git.is_git_dir(git_dir.path)

    with tempfile.TemporaryDirectory() as tmp_dir_path:
        assert not git.is_git_dir(tmp_dir_path)


def test_check_all_pushed_everything_is_pushed_returns_none():
    """If everything is pushed, the function should return None."""
    with TmpGitDir() as git_repo:
        with patch("git_workon.git.subprocess.run") as mc_run:
            mc_run.return_value = Mock(stderr="Everything up-to-date", stdout="")
            assert git.check_all_pushed(git_repo.path) is None


def test_check_all_pushed_there_is_some_stash_raises_exception():
    """If everything is pushed, the function should return None."""
    with TmpGitDir(initial_commit=True) as git_dir:
        os.mknod(os.path.join(git_dir.path, "1.txt"))
        git_dir.stash()
        pattern = r"stash@\{0\}: WIP on master: .+? dummy"

        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert re.search(pattern, str(exc.value))


def test_check_all_pushed_branch_raises_exception():
    with TmpGitDir(initial_commit=True) as git_dir:
        git_dir.checkout("test")
        os.mknod(os.path.join(git_dir.path, "1.txt"))
        git_dir.add()
        git_dir.commit("example")

        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert "(master) dummy" in str(exc.value)
        assert "(HEAD -> test) example" in str(exc.value)


def test_check_all_pushed_with_unstaged_returns_info():
    with TmpGitDir(initial_commit=True) as git_dir:
        git_dir.checkout("test")
        os.mknod(os.path.join(git_dir.path, "1.txt"))

        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert "?? 1.txt\n" in str(exc.value)


def test_check_all_pushed_tags_no_remote_raises_exception():
    with TmpGitDir() as git_dir:
        with pytest.raises(git.GITError) as exc:
            git.check_all_pushed(git_dir.path)
        assert "Failed to check unpushed tags" in str(exc.value)


def test_check_all_pushed_tags_with_unpushed_raises_exception():
    with TmpGitDir(initial_commit=True) as git_dir:
        with patch("git_workon.git.subprocess.run") as mc_run:
            mc_run.return_value = Mock(
                stderr="* [new tag]         1.1.0 -> 1.1.0", stdout=""
            )
            with pytest.raises(git.GITError) as exc:
                git.check_all_pushed(git_dir.path)
            assert "1.1.0 -> 1.1.0" in str(exc.value)


def test_check_all_all_entities_are_unpushed_raises_exception():
    with TmpGitDir(initial_commit=True) as git_dir:
        with patch("git_workon.git.subprocess.run") as mc_run:
            mc_run.side_effect = [
                Mock(stdout="?? 1.txt\n"),
                Mock(stdout="stash{0}"),
                Mock(stdout="(master) dummy\n(HEAD -> test) example"),
                Mock(stderr="* [new tag]         1.1.0 -> 1.1.0", stdout=""),
            ]
            with pytest.raises(git.GITError) as exc:
                git.check_all_pushed(git_dir.path)
            for entity in "Stashes", "Commits", "Not staged", "Tags":
                assert entity in str(exc.value)


@patch("git_workon.git.subprocess.run")
def test_clone(mc_subprocess_run):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        mc_subprocess_run.side_effect = lambda *args, **kwargs: os.mkdir(
            os.path.join(tmp_dir_path, "a")
        )
        git.clone("http://localhost:3000/gogs/a", tmp_dir_path)
        assert os.path.exists(os.path.join(tmp_dir_path, "a"))


@patch("git_workon.git.subprocess.run")
def test_clone_no_such_project(mc_subprocess_run):
    mc_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], "", "not found"
    )
    with tempfile.TemporaryDirectory() as tmp_dir_path:

        with pytest.raises(git.GITError) as exc:
            git.clone("http://localhost:3000/gogs/c", tmp_dir_path)
        assert "not found" in str(exc.value)


@patch("git_workon.git.subprocess.run")
def test_clone_already_exists(mc_subprocess_run):
    mc_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], "", "already exists"
    )
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        directory = os.path.join(tmp_dir_path, "a")
        os.mkdir(directory)
        os.mknod(os.path.join(directory, "some"))

        with pytest.raises(git.GITError) as exc:
            git.clone("http://localhost:3000/gogs/a", tmp_dir_path)
        assert "already exists" in str(exc.value)


class TestWorkingDirBase(TestCase):
    """Base tester for `WorkingDir`."""

    def setUp(self) -> None:
        self.directory = tempfile.mkdtemp()
        self.workon = git.WorkingDir(self.directory)
        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(self.directory)
        return super().tearDown()

    def add_git_project(self) -> DummyGitProject:
        """Add git project to the `directory`.

        :returns: path to the GIT project
        """
        proj_dir = tempfile.mkdtemp(dir=self.workon.directory)
        os.mkdir(os.path.join(proj_dir, ".git"))
        return DummyGitProject(os.path.basename(proj_dir), proj_dir)


class TestInit(TestWorkingDirBase):
    """Tests for initialization."""

    @patch("git_workon.git.os.makedirs")
    def test_creates_working_dir_if_it_does_not_exist(self, mc_makedirs):
        git.WorkingDir("~/_test_workon")
        assert mc_makedirs.call_args[1] == {"exist_ok": True}
        assert mc_makedirs.call_args[0][0].startswith("/")
        assert "_test_workon" in mc_makedirs.call_args[0][0]


class TestRemove(TestWorkingDirBase):
    """Tests for done command."""

    def test_no_such_project_exception_raised(self):
        with pytest.raises(git.CommandError) as exc:
            self.workon.remove("nonex")
        assert "not found" in str(exc.value)

    @patch("git_workon.git.check_all_pushed", Mock(return_value=None))
    def test_existing_project_gets_removed(self):
        proj = self.add_git_project()
        self.workon.remove(proj.name)
        assert not os.path.exists(proj.path)

    @patch("git_workon.git.check_all_pushed", Mock(return_value=None))
    def test_all_filetypes_removed(self):
        # GIT projects
        for _ in range(2):
            self.add_git_project()
        # project dir
        tempfile.mkdtemp(dir=self.workon.directory)
        # regular file
        tempfile.mktemp(dir=self.workon.directory)
        # symlink
        src = tempfile.mktemp(dir=self.workon.directory)
        dst = tempfile.mktemp(dir=self.workon.directory)
        os.symlink(src, dst)
        # namedpipe
        os.mkfifo(os.path.join(self.workon.directory, "tmppipe"), 0o600)

        self.workon.remove()
        assert not os.listdir(self.workon.directory)

    @patch(
        "git_workon.git.check_all_pushed",
        Mock(side_effect=git.GITError("something")),
    )
    def test_existing_project_unpushed_error_raised(self):
        proj = self.add_git_project()

        with pytest.raises(git.CommandError):
            self.workon.remove(project_name=proj.name)
        assert os.path.exists(proj.path)

    @patch("git_workon.git.check_all_pushed", Mock(return_value="something"))
    def test_existing_project_unpushed_forced_ok(self):
        proj = self.add_git_project()

        self.workon.remove(proj.name, force=True)
        assert not os.path.exists(proj.path)

    @patch("git_workon.git.check_all_pushed")
    def test_all_projects_couple_are_dirty_but_all_tried_to_be_removed(
        self, mc_check_all_pushed
    ):
        for _ in range(4):
            self.add_git_project()

        mc_check_all_pushed.side_effect = (git.GITError, None, git.GITError, None)
        self.workon.remove()

        assert len(os.listdir(self.directory)) == 2


class TestClone(TestWorkingDirBase):
    """Tests for the clone command."""

    @patch("git_workon.git.clone")
    def test_clone_error(self, mc_clone):
        mc_clone.side_effect = git.GITError

        with pytest.raises(git.CommandError):
            self.workon.clone("some", ["some"])

    def test_project_already_exist_error_raised(self):
        proj = self.add_git_project()
        with pytest.raises(git.CommandError) as exc:
            self.workon.clone(proj.name, [])
        assert "already cloned" in str(exc.value)

    @patch("git_workon.git.clone")
    def test_cloned_ok(self, mc_clone):
        @dataclass
        class _Case:
            source: str
            expected: str

        cases = [
            _Case("https://github.com/user", "https://github.com/user/some.git"),
            _Case("https://github.com/user/", "https://github.com/user/some.git"),
            _Case("https://github.com/user//", "https://github.com/user/some.git"),
            _Case("git@github.com:user", "git@github.com:user/some.git"),
            _Case("git@github.com:user/", "git@github.com:user/some.git"),
            _Case("git@github.com:user//", "git@github.com:user/some.git"),
        ]

        for case in cases:
            # pylint:disable=cell-var-from-loop
            with tempfile.TemporaryDirectory() as tmp_dir:
                proj_path = os.path.join(tmp_dir, "some")
                mc_clone.side_effect = lambda *args, **kwargs: os.mkdir(proj_path)

                workon_ = git.WorkingDir(tmp_dir)
                workon_.clone("some", [case.source])
                assert os.path.isdir(proj_path)

                mc_clone.assert_called_once_with(case.expected, proj_path)
                mc_clone.reset_mock()

    @patch("git_workon.git.clone")
    def test_cloned_couple_of_sources_tried(self, mc_clone):
        mc_clone.side_effect = (git.GITError, None)
        self.workon.clone("any", ["fail_source", "success_source"])

        mc_clone.assert_has_calls(
            [
                call("fail_source/any.git", f"{self.directory}/any"),
                call("success_source/any.git", f"{self.directory}/any"),
            ]
        )


class TestOpen(TestWorkingDirBase):
    """Tests for the open command."""

    def test_no_project_exception_raised(self):
        with pytest.raises(git.CommandError):
            self.workon.open("nonex", editor="code")

    @patch("git_workon.git.subprocess")
    def test_with_specified_editor(self, mc_subprocess):
        mc_subprocess.run.return_value = Mock(returncode=0)

        proj = self.add_git_project()
        self.workon.open(proj.name, editor="code")
        mc_subprocess.run.assert_called_once_with(
            ["code", f"{self.directory}/{proj.name}"], check=False
        )

    @patch("git_workon.git.subprocess")
    def test_no_suitable_editor_found(self, mc_subprocess):
        # this test assumes that this ENV variable is set
        os.environ["EDITOR"] = "env_editor"
        mc_subprocess.run.return_value = Mock(returncode=1)

        proj = self.add_git_project()

        with pytest.raises(git.CommandError) as exc:
            self.workon.open(proj.name, editor="code")
        assert "No suitable editor" in str(exc.value)

        assert mc_subprocess.run.call_count == 4

    @patch("git_workon.git.subprocess")
    def test_editor_from_env(self, mc_subprocess):
        mc_subprocess.run.side_effect = (Mock(returncode=1), Mock(returncode=0))

        proj = self.add_git_project()

        self.workon.open(proj.name, editor="code")
        assert mc_subprocess.run.call_count == 2


class TestShow(TestWorkingDirBase):
    """Tests for the show command."""

    def test_dir_is_empty_returns_empty_list(self):
        assert not list(self.workon.show())

    def test_one_project_returns_this_project_name(self):
        proj = self.add_git_project()
        assert list(self.workon.show()) == [proj.name]
