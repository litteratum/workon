"""Tests for git.py."""
import os
import re
import shutil
import subprocess
import tempfile
from typing import Iterable
from unittest.mock import patch

import pytest
from workon import git
from workon.script import ScriptError


class TmpGitDir:
    """Temporary GIT directory."""

    def __init__(self, initial_commit=False) -> None:
        self.path = tempfile.mkdtemp()
        self.initial_commit = initial_commit

        self._git_init()

    def _git_init(self):
        subprocess.run(['git', 'init'], cwd=self.path, check=True)

        if self.initial_commit:
            os.mknod(os.path.join(self.path, 'some'))
            self.add()
            self.commit()

    def add(self, files: Iterable[str] = None):
        if not files:
            subprocess.run(['git', 'add', '--all'], cwd=self.path, check=True)
        else:
            for file in files:
                subprocess.run(['git', 'add', file], cwd=self.path, check=True)

    def stash(self, include_untracked=True):
        command = ['git', 'stash']
        if include_untracked:
            command.append('--include-untracked')

        subprocess.run(command, cwd=self.path, check=True)

    def checkout(self, branch, create=True):
        command = ['git', 'checkout', '-b' if create else '', branch]
        subprocess.run(command, cwd=self.path, check=True)

    def commit(self, message='dummy'):
        subprocess.run(
            ['git', 'commit', '-m', message], cwd=self.path, check=True
        )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.path)


def test_get_stash_info_returns_empty_str_if_no_stash():
    with TmpGitDir() as git_repo:
        assert git.get_stash_info(git_repo.path) == ''


def test_get_stash_info_returns_info_when_there_is_some_stash():
    with TmpGitDir(initial_commit=True) as git_dir:
        os.mknod(os.path.join(git_dir.path, '1.txt'))
        git_dir.stash()
        pattern = r'stash@\{0\}: WIP on master: .+? dummy'
        assert re.match(pattern, git.get_stash_info(git_dir.path))


def test_get_stash_info_not_a_git_repo_returns_empty_str():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        assert git.get_stash_info(tmp_dir_path) == ''


def test_get_unpushed_branches_info_no_unpushed_returns_empty_str():
    with TmpGitDir() as git_dir:
        assert git.get_unpushed_branches_info(git_dir.path) == ''


def test_get_unpushed_branches_info_with_unpushed_returns_info():
    with TmpGitDir(initial_commit=True) as git_dir:
        git_dir.checkout('test')
        os.mknod(os.path.join(git_dir.path, '1.txt'))
        git_dir.add()
        git_dir.commit('example')

        info = git.get_unpushed_branches_info(git_dir.path)
        assert '(master) dummy' in info
        assert '(HEAD -> test) example' in info


def test_get_unpushed_branches_info_not_a_git_repo():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        assert git.get_unpushed_branches_info(tmp_dir_path) == ''


def test_get_unstaged_info_no_unstaged_returns_empty_str():
    with TmpGitDir() as git_dir:
        assert git.get_unstaged_info(git_dir.path) == ''


def test_get_unstaged_info_not_a_git_repo():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        assert git.get_unstaged_info(tmp_dir_path) == ''


def test_get_unstaged_info_with_unstaged_returns_info():
    with TmpGitDir(initial_commit=True) as git_dir:
        git_dir.checkout('test')
        os.mknod(os.path.join(git_dir.path, '1.txt'))

        info = git.get_unstaged_info(git_dir.path)
        assert '?? 1.txt\n' in info


@patch('workon.git.subprocess.run')
def test_clone(mc_subprocess_run):
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        mc_subprocess_run.side_effect = lambda *args, **kwargs: os.mkdir(
            os.path.join(tmp_dir_path, 'a')
        )
        git.clone('http://localhost:3000/gogs/a', tmp_dir_path)
        assert os.path.exists(os.path.join(tmp_dir_path, 'a'))


@patch('workon.git.subprocess.run')
def test_clone_no_such_project(mc_subprocess_run):
    mc_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], '', 'not found'
    )
    with tempfile.TemporaryDirectory() as tmp_dir_path:

        with pytest.raises(git.GITError) as exc:
            git.clone('http://localhost:3000/gogs/c', tmp_dir_path)
        assert 'not found' in str(exc.value)


@patch('workon.git.subprocess.run')
def test_clone_already_exists(mc_subprocess_run):
    mc_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], '', 'already exists'
    )
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        directory = os.path.join(tmp_dir_path, 'a')
        os.mkdir(directory)
        os.mknod(os.path.join(directory, 'some'))

        with pytest.raises(git.GITError) as exc:
            git.clone('http://localhost:3000/gogs/a', tmp_dir_path)
        assert 'already exists' in str(exc.value)
