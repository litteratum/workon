"""Command Line Interface processing."""
import argparse
import os

from .errors import ScriptError


def _append_start_command(subparsers, parent):
    start_command = subparsers.add_parser(
        'start', help='Start your work on a project',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent], add_help=False,
    )

    start_command.add_argument('project', help='Project name to start with')
    start_command.add_argument(
        '-s', '--source', help='GIT source including username',
        default=os.environ.get('WORKON_GIT_SOURCE')
    )
    start_command.add_argument(
        '-f', '--force', help=(
            'Force GIT clone even if your working directory'
            ' is not empty'
        ), action='store_true'
    )


def _append_done_command(subparsers, parent):
    done_command = subparsers.add_parser(
        'done', help='Finish your work and clean working directory',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent], add_help=False,
    )

    done_command.add_argument(
        'project', nargs='?', help=(
            'Project name to finish work for. If not '
            'specified, all projects will be finished'
        )
    )
    done_command.add_argument(
        '-f', '--force', help=(
            'Force a project directory removal even if '
            'there are some unpushed changes or stashes'
        ), action='store_true'
    )


def _parse_args():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        dest='command', title='script commands',
        help='Command to execute', required=True
    )

    parent_parser = argparse.ArgumentParser()
    parent_parser.add_argument(
        '-d', '--directory', help='Working directory',
        default=os.environ.get('WORKON_DIR')
    )
    parent_parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Get more information of what\'s going on'
    )

    _append_start_command(subparsers, parent=parent_parser)
    _append_done_command(subparsers, parent=parent_parser)

    return parser.parse_args()


def parse_args():
    """Parse CLI args."""
    args = _parse_args()

    if not args.directory:
        raise ScriptError(
            'Working directory is not specified. Please see script --help or '
            'the documentation to know how to configure the script'
        )

    try:
        os.makedirs(args.directory, exist_ok=True)
    except OSError as exc:
        raise ScriptError(
            'Failed to create working directory: %s' % exc) from exc

    if not os.access(args.directory, os.R_OK) \
            or not os.access(args.directory, os.W_OK):
        raise ScriptError(
            'Oops. Specified working directory is not readable/writable'
        )

    if args.command == 'start':
        if not args.source:
            raise ScriptError(
                'GIT source is not specified. Please see script --help or '
                'the documentation to know how to configure the script'
            )

    return args
