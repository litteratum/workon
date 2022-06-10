"""Tests or cli.py."""
# pylint:disable=missing-function-docstring, no-self-use, too-many-instance-attributes
import os
import sys
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import pytest
from git_workon import cli, config, git


class TestBase(TestCase):
    """Base tester for CLI."""

    def setUp(self) -> None:
        self.mc_clone = MagicMock()
        self.mc_open = MagicMock()
        self.mc_remove = MagicMock()
        self.mc_show = MagicMock()

        self.patch_clone = patch("git_workon.git.WorkingDir.clone", new=self.mc_clone)
        self.patch_open = patch("git_workon.git.WorkingDir.open", new=self.mc_open)
        self.patch_remove = patch(
            "git_workon.git.WorkingDir.remove", new=self.mc_remove
        )
        self.patch_show = patch("git_workon.git.WorkingDir.show", new=self.mc_show)
        for patch_ in (
            self.patch_clone,
            self.patch_open,
            self.patch_remove,
            self.patch_show,
        ):
            patch_.start()
        return super().setUp()

    def tearDown(self) -> None:
        for patch_ in (
            self.patch_clone,
            self.patch_open,
            self.patch_remove,
            self.patch_show,
        ):
            patch_.stop()
        return super().tearDown()


class TestParseErrors(TestBase):
    """Tests for args parsing errors."""

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_no_args(self):
        sys.argv = ["git_workon"]
        with pytest.raises(SystemExit):
            cli.main()

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_parse_args_command_no_args(self):
        sys.argv = ["git_workon", "start", "my_project"]

        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert int(str(exc.value)) == 2

        sys.argv = ["git_workon", "done"]
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert int(str(exc.value)) == 2


class TestStartCommand(TestBase):
    """Tests for the start command."""

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_noopen_only_cloned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "start",
                "my_project",
                "-d",
                tmp_dir,
                "-s",
                "any",
                "-n",
            ]
            cli.main()

        assert not self.mc_open.called
        self.mc_clone.assert_called_once_with("my_project", ["any"])

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_cloned_and_opened(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "start",
                "my_project",
                "-d",
                tmp_dir,
                "-s",
                "any",
            ]
            cli.main()

        self.mc_clone.assert_called_once_with("my_project", ["any"])
        self.mc_open.assert_called_once_with("my_project", None)

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_already_cloned_opened(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_name = os.path.basename(tempfile.mkdtemp(dir=tmp_dir))
            sys.argv = [
                "git_workon",
                "start",
                os.path.basename(project_name) + "/",
                "-d",
                tmp_dir,
                "-s",
                "any",
            ]
            cli.main()

        assert not self.mc_clone.called
        self.mc_open.assert_called_once_with(os.path.basename(project_name), None)

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_with_specified_editor(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "start",
                "my_project",
                "-d",
                tmp_dir,
                "-s",
                "any",
                "-e",
                "code",
            ]
            cli.main()

        self.mc_clone.assert_called_once_with("my_project", ["any"])
        self.mc_open.assert_called_once_with("my_project", "code")

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_command_error(self):
        self.mc_clone.side_effect = git.CommandError("Oops")
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "start",
                "my_project",
                "-d",
                tmp_dir,
                "-s",
                "any",
            ]
            with pytest.raises(SystemExit) as exc:
                cli.main()
            assert int(str(exc.value)) == 1

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_source_not_defined_exception_raised(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = ["git_workon", "start", "my_project", "-d", tmp_dir]
            with pytest.raises(SystemExit) as exc:
                cli.main()
            assert int(str(exc.value)) == 2

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, sources=["third", "fourth"])),
    )
    def test_user_config_sources_used(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "start",
                "my_project",
                "-d",
                tmp_dir,
            ]
            cli.main()
        self.mc_clone.assert_called_once_with("my_project", ["third", "fourth"])

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, sources=["third", "fourth"])),
    )
    def test_user_config_is_extended_by_sources(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "start",
                "my_project",
                "-d",
                tmp_dir,
                "-s",
                "first",
                "-s",
                "second",
            ]
            cli.main()
        self.mc_clone.assert_called_once_with(
            "my_project", ["first", "second", "third", "fourth"]
        )


class TestDoneCommand(TestBase):
    """Tests for the done command."""

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_one_project(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "done",
                "my_project",
                "-d",
                tmp_dir,
            ]
            cli.main()

        assert not self.mc_clone.called
        assert not self.mc_open.called
        self.mc_remove.assert_called_once_with("my_project", False)

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_one_project_name_stripped(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "done",
                "my_project/",
                "-d",
                tmp_dir,
            ]
            cli.main()

        assert not self.mc_clone.called
        assert not self.mc_open.called
        self.mc_remove.assert_called_once_with("my_project", False)

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_all_projects(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "done",
                "-d",
                tmp_dir,
            ]
            cli.main()

        assert not self.mc_clone.called
        assert not self.mc_open.called
        self.mc_remove.assert_called_once_with(None, False)

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_command_error(self):
        self.mc_remove.side_effect = git.CommandError("Oops")
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = [
                "git_workon",
                "done",
                "-d",
                tmp_dir,
            ]
            with pytest.raises(SystemExit) as exc:
                cli.main()
            assert int(str(exc.value)) == 1


class TestConfigCommand(TestBase):
    """Tests for the config command."""

    @patch("git_workon.config.load_config")
    @patch("git_workon.config.init_config")
    def test_initialize(self, mc_init_config, mc_load_config):
        sys.argv = ["git_workon", "config"]
        cli.main()

        mc_init_config.assert_called_once_with()
        assert mc_load_config.call_count == 2


class TestShowCommand(TestBase):
    """Tests for the show command."""

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_dir_is_not_specified_exit(self):
        sys.argv = ["git_workon", "show"]

        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert int(str(exc.value)) == 2

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_show_no_check(self):

        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = ["git_workon", "show", "-d", tmp_dir, "-n"]
            cli.main()

            self.mc_show.assert_called_once_with(check_status=False)

    @patch(
        "git_workon.config.load_config",
        Mock(return_value=config.UserConfig(None, None, None)),
    )
    def test_show_with_check(self):

        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.argv = ["git_workon", "show", "-d", tmp_dir]
            cli.main()

            self.mc_show.assert_called_once_with(check_status=True)
