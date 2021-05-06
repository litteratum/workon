"""High level integration tests."""
import os
import tempfile
from .utils import get_script_output


def test_start_clone_project_to_empty_folder():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        _, code = get_script_output(
            (
                'start', 'a', '-s', 'http://localhost:10080/gogs',
                '-d', tmp_dir_path, '--no-open'
            )
        )
        assert code == 0


def test_start_clone_project_to_not_empty_folder():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        out, code = get_script_output(
            (
                'start', 'a', '-s', 'http://localhost:10080/gogs',
                '-d', tmp_dir_path, '--no-open'
            )
        )
        assert 'not empty' in out
        assert code == 1


def test_start_clone_project_to_not_empty_folder_forced():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        _, code = get_script_output(
            (
                'start', 'a', '-s', 'http://localhost:10080/gogs',
                '-d', tmp_dir_path, '--force', '--no-open'
            )
        )
        assert code == 0


def test_start_clone_project_does_not_exist():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        tempfile.mkdtemp(dir=tmp_dir_path)
        out, code = get_script_output(
            (
                'start', 'z', '-s', 'http://localhost:10080/gogs',
                '-d', tmp_dir_path, '--force', '--no-open'
            )
        )
        assert 'not found' in out
        assert code == 1


def test_done_remove_single():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(tmp_dir_path + '/a')
        _, code = get_script_output(['done', 'a', '-d', tmp_dir_path])
        assert code == 0
        assert len(os.listdir(tmp_dir_path)) == 0


def test_done_remove_all():
    with tempfile.TemporaryDirectory() as tmp_dir_path:
        os.mkdir(tmp_dir_path + '/a')
        os.mkdir(tmp_dir_path + '/b')
        _, code = get_script_output(['done', '-d', tmp_dir_path])
        assert code == 0
        assert len(os.listdir(tmp_dir_path)) == 0
