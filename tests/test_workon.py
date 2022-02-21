"""Tests for script."""
# pylint:disable=missing-function-docstring, no-self-use
import os
import shutil
import tempfile
from collections import namedtuple
from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import Mock, call, patch

import pytest
from git_workon import git, workon

DummyGitProject = namedtuple("DummyProject", ["name", "path"])


class TestBase(TestCase):
    """Base tester for script.py."""

    def setUp(self) -> None:
        self.directory = tempfile.mkdtemp()
        self.workon = workon.WorkOnDir(self.directory)
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


class TestInit(TestBase):
    """Tests for initialization."""

    @patch("git_workon.workon.os.makedirs")
    def test_creates_working_dir_if_it_does_not_exist(self, mc_makedirs):
        workon.WorkOnDir("~/_test_workon")
        assert mc_makedirs.call_args[1] == {"exist_ok": True}
        assert mc_makedirs.call_args[0][0].startswith("/")
        assert "_test_workon" in mc_makedirs.call_args[0][0]


class TestRemove(TestBase):
    """Tests for done command."""

    def test_no_such_project_exception_raised(self):
        with pytest.raises(workon.CommandError) as exc:
            self.workon.remove("nonex")
        assert "not found" in str(exc.value)

    @patch("git_workon.workon.git.check_all_pushed", Mock(return_value=None))
    def test_existing_project_gets_removed(self):
        proj = self.add_git_project()
        self.workon.remove(proj.name)
        assert not os.path.exists(proj.path)

    @patch("git_workon.workon.git.check_all_pushed", Mock(return_value=None))
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
        "git_workon.workon.git.check_all_pushed",
        Mock(side_effect=git.GITError("something")),
    )
    def test_existing_project_unpushed_error_raised(self):
        proj = self.add_git_project()

        with pytest.raises(workon.CommandError):
            self.workon.remove(project_name=proj.name)
        assert os.path.exists(proj.path)

    @patch("git_workon.workon.git.check_all_pushed", Mock(return_value="something"))
    def test_existing_project_unpushed_forced_ok(self):
        proj = self.add_git_project()

        self.workon.remove(proj.name, force=True)
        assert not os.path.exists(proj.path)

    @patch("git_workon.workon.git.check_all_pushed")
    def test_all_projects_couple_are_dirty_but_all_tried_to_be_removed(
        self, mc_check_all_pushed
    ):
        for _ in range(4):
            self.add_git_project()

        mc_check_all_pushed.side_effect = (git.GITError, None, git.GITError, None)
        self.workon.remove()

        assert len(os.listdir(self.directory)) == 2


class TestClone(TestBase):
    """Tests for the clone command."""

    @patch("git_workon.workon.git.clone")
    def test_clone_error(self, mc_clone):
        mc_clone.side_effect = git.GITError

        with pytest.raises(workon.CommandError):
            self.workon.clone("some", ["some"])

    def test_project_already_exist_error_raised(self):
        proj = self.add_git_project()
        with pytest.raises(workon.CommandError) as exc:
            self.workon.clone(proj.name, [])
        assert "already cloned" in str(exc.value)

    @patch("git_workon.workon.git.clone")
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

                workon_ = workon.WorkOnDir(tmp_dir)
                workon_.clone("some", [case.source])
                assert os.path.isdir(proj_path)

                mc_clone.assert_called_once_with(case.expected, proj_path)
                mc_clone.reset_mock()

    @patch("git_workon.workon.git.clone")
    def test_cloned_couple_of_sources_tried(self, mc_clone):
        mc_clone.side_effect = (git.GITError, None)
        self.workon.clone("any", ["fail_source", "success_source"])

        mc_clone.assert_has_calls(
            [
                call("fail_source/any.git", f"{self.directory}/any"),
                call("success_source/any.git", f"{self.directory}/any"),
            ]
        )


class TestOpen(TestBase):
    """Tests for the open command."""

    def test_no_project_exception_raised(self):
        with pytest.raises(workon.CommandError):
            self.workon.open("nonex", editor="code")

    @patch("git_workon.workon.subprocess")
    def test_with_specified_editor(self, mc_subprocess):
        mc_subprocess.run.return_value = Mock(returncode=0)

        proj = self.add_git_project()
        self.workon.open(proj.name, editor="code")
        mc_subprocess.run.assert_called_once_with(
            ["code", f"{self.directory}/{proj.name}"], check=False
        )

    @patch("git_workon.workon.subprocess")
    def test_no_suitable_editor_found(self, mc_subprocess):
        # this test assumes that this ENV variable is set
        os.environ["EDITOR"] = "env_editor"
        mc_subprocess.run.return_value = Mock(returncode=1)

        proj = self.add_git_project()

        with pytest.raises(workon.CommandError) as exc:
            self.workon.open(proj.name, editor="code")
        assert "No suitable editor" in str(exc.value)

        assert mc_subprocess.run.call_count == 4

    @patch("git_workon.workon.subprocess")
    def test_editor_from_env(self, mc_subprocess):
        mc_subprocess.run.side_effect = (Mock(returncode=1), Mock(returncode=0))

        proj = self.add_git_project()

        self.workon.open(proj.name, editor="code")
        assert mc_subprocess.run.call_count == 2
