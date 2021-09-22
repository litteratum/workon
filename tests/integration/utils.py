"""Shared integration tests utilities."""
import os
import subprocess
import sys
from typing import Iterable

SCRIPT_EXE = os.path.join(sys.prefix, 'bin', 'git_workon')


def get_script_output(params: Iterable) -> tuple:
    """Run script in subprocess and return its output.

    Output contains: (script output, script exit code)
    """
    cmd = subprocess.run(
        '{} {}'.format(SCRIPT_EXE, ' '.join(params)),
        shell=True,
        check=False,
        capture_output=True,
        text=True
    )
    return cmd.stdout or cmd.stderr, cmd.returncode
