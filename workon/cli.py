"""Command Line Interface processing."""
import argparse
import os

from .errors import ScriptError


# pylint:disable=too-few-public-methods
class ExtendAction(argparse.Action):
    """Extend action for `argparse`."""

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)


def _append_start_command(subparsers, parent, user_config):
    start_command = subparsers.add_parser(
        'start', help='start your work on a project',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent], add_help=False,
    )
    start_command.register('action', 'extend', ExtendAction)

    start_command.add_argument('project', help='project name to start with')
    start_command.add_argument(
        '-s', '--source', help='git source including username',
        action='extend', nargs='+'
    )
    start_command.add_argument(
        '-e', '--editor', help='editor to use to open a project',
        default=user_config.get('editor')
    )
    start_command.add_argument(
        '-n', '--no-open', dest='noopen',
        help='don\'t open a project', action='store_true'
    )


def _append_done_command(subparsers, parent):
    done_command = subparsers.add_parser(
        'done', help='finish your work and clean working directory',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent], add_help=False,
    )

    done_command.add_argument(
        'project', nargs='?', help=(
            'project name to finish work for. If not '
            'specified, all projects will be finished'
        )
    )
    done_command.add_argument(
        '-f', '--force', help=(
            'force a project directory removal even if '
            'there are some unpushed/unstaged changes or stashes'
        ), action='store_true'
    )


def _append_open_command(subparsers, parent, user_config):
    open_command = subparsers.add_parser(
        'open', help='open an already started project',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent], add_help=False,
    )

    open_command.add_argument(
        'project', help='project name under working directory to open')

    open_command.add_argument(
        '-e', '--editor', help='editor to use to open a project',
        default=user_config.get('editor')
    )


def _parse_args(user_config):
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        dest='command', title='script commands',
        help='command to execute', required=True
    )

    parent_parser = argparse.ArgumentParser()
    parent_parser.add_argument(
        '-d', '--directory', help='working directory',
        default=user_config.get('dir')
    )
    parent_parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='get more information of what\'s going on'
    )

    _append_start_command(subparsers, parent_parser, user_config)
    _append_done_command(subparsers, parent_parser)
    _append_open_command(subparsers, parent_parser, user_config)

    return parser.parse_args()


def parse_args(user_config):
    """Parse CLI args."""
    args = _parse_args(user_config)

    if not args.directory:
        raise ScriptError(
            'Working directory is not specified. Please see script --help or '
            'the documentation to know how to configure the script'
        )

    args.directory = os.path.expanduser(args.directory)

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
        if user_config.get('source'):
            if args.source:
                args.source.extend(user_config['source'])
            else:
                args.source = user_config['source']

        if not args.source:
            raise ScriptError(
                'GIT source is not specified. Please see script --help or '
                'the documentation to know how to configure the script'
            )

    return args
