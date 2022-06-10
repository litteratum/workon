"""Command Line Interface for the GIT workon."""
import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Iterator, List, Optional

import termcolor

from . import config as config_module
from . import git


class CLIError(Exception):
    """CLI error."""


# pylint:disable=too-few-public-methods
class ExtendAction(argparse.Action):
    """Extend action for `argparse`."""

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)


_COLOR_FOR_STATUS = {
    git.ProjectStatus.CLEAN: "green",
    git.ProjectStatus.DIRTY: "yellow",
    git.ProjectStatus.UNDEFINED: "white",
}


@dataclass
class ArgParseArgument:
    """Wrapper encapsulating `argparse` argument."""

    positional: tuple
    keyword: dict


def _append_args(
    parser, args: Optional[List[ArgParseArgument]]
) -> None:
    if args:
        for arg in args:
            parser.add_argument(*arg.positional, **arg.keyword)


def _append_start_command(
    subparsers, parent, user_config: config_module.UserConfig
):
    start_parser = subparsers.add_parser(
        "start",
        help="start your work on a project",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent],
        add_help=False,
    )
    start_parser.register("action", "extend", ExtendAction)

    start_parser.add_argument(
        "project", help="project name to start with"
    )
    start_parser.add_argument(
        "-s",
        "--source",
        help="git source including username",
        action="extend",
        nargs="+",
        required=user_config.sources is None,
    )
    start_parser.add_argument(
        "-n",
        "--no-open",
        dest="noopen",
        help="don't open a project",
        action="store_true",
    )

    return start_parser


def _append_done_command(subparsers, parent):
    done_parser = subparsers.add_parser(
        "done",
        help="finish your work and clean working directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent],
        add_help=False,
    )

    done_parser.add_argument(
        "project",
        nargs="?",
        help=(
            "project name to finish work for. If not "
            "specified, all projects will be finished"
        ),
    )
    done_parser.add_argument(
        "-f",
        "--force",
        help=(
            "force a project directory removal even if "
            "there are some unpushed/unstaged changes or stashes"
        ),
        action="store_true",
    )

    return done_parser


def _append_config_command(subparsers, parent):
    return subparsers.add_parser(
        "config",
        help="init/show configuration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent],
        add_help=False,
    )


def _append_show_command(subparsers, parent):
    show_parser = subparsers.add_parser(
        "show",
        help="list projects under the working directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent],
        add_help=False,
    )
    show_parser.add_argument(
        "-n",
        "--no-check",
        dest="nocheck",
        help="don't check projects status",
        action="store_true",
    )
    return show_parser


def _parse_args(user_config: config_module.UserConfig):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="command",
        title="script commands",
        help="command to execute",
        required=True,
    )
    parent_parser = argparse.ArgumentParser()
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="get more information of what's going on",
    )

    directory_arg = ArgParseArgument(
        positional=("-d", "--directory"),
        keyword={
            "help": "working directory",
            "default": user_config.dir,
            "required": user_config.dir is None,
        },
    )
    editor_arg = ArgParseArgument(
        positional=("-e", "--editor"),
        keyword={
            "help": "editor used to open a project/configuration",
            "default": user_config.editor,
        },
    )

    start_parser = _append_start_command(
        subparsers, parent_parser, user_config
    )
    done_parser = _append_done_command(subparsers, parent_parser)
    _append_config_command(subparsers, parent_parser)
    show_parser = _append_show_command(subparsers, parent_parser)

    _append_args(
        start_parser,
        [
            directory_arg,
            editor_arg,
        ],
    )
    _append_args(
        done_parser,
        [
            directory_arg,
        ],
    )
    _append_args(
        show_parser,
        [
            directory_arg,
        ],
    )

    args = parser.parse_args()
    if hasattr(args, "project") and args.project:
        args.project = args.project.strip("/ ")
    return args


def _init_logger(verbose):
    level = logging.DEBUG if verbose >= 1 else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")


def main():
    """Execute the script commands."""
    try:
        user_config = config_module.load_config()
        args = _parse_args(user_config)
        _init_logger(args.verbose)

        FUNC_FOR_COMMAND[args.command](args, user_config)
    except KeyboardInterrupt:
        logging.info("\nCanceled by user")
        sys.exit(0)
    except config_module.ConfigError as exc:
        logging.error("Configuration error: %s", exc)
        sys.exit(1)
    except git.CommandError as exc:
        logging.error("Command error: %s", exc)
        sys.exit(1)
    except Exception as exc:  # pylint:disable=broad-except
        logging.error("Unexpected script error: %s", exc)
        sys.exit(2)


def handle_start_command(
    args: argparse.Namespace,
    user_config: config_module.UserConfig,
) -> None:
    """Process start command."""
    workon_dir = git.WorkingDir(args.directory)

    if user_config.sources:
        if args.source:
            args.source.extend(user_config.sources)
        else:
            args.source = user_config.sources

    if args.project not in workon_dir:
        workon_dir.clone(args.project, args.source)

    if not args.noopen:
        workon_dir.open(args.project, args.editor)


# pylint:disable=unused-argument
def handle_done_command(
    args: argparse.Namespace,
    user_config: config_module.UserConfig,
) -> None:
    """Process done command."""
    workon_dir = git.WorkingDir(args.directory)

    if args.project:
        args.project = args.project.strip("/ ")

    workon_dir.remove(args.project, args.force)


def handle_config_command(
    args: argparse.Namespace,
    user_config: config_module.UserConfig,
) -> None:
    """Process config command."""
    config_module.init_config()
    logging.info(config_module.load_config())


def _build_projects_info_text(
    projects_info: Iterator[git.ProjectInfo],
) -> str:
    return "\n".join(
        termcolor.colored(
            f"{info.name}",
            _COLOR_FOR_STATUS[
                info.status or git.ProjectStatus.UNDEFINED
            ],
        )
        for info in projects_info
    )


def handle_show_command(
    args: argparse.Namespace,
    user_config: config_module.UserConfig,
) -> None:
    """Process show command."""
    workon_dir = git.WorkingDir(args.directory)
    projects_info = workon_dir.show(check_status=not args.nocheck)
    logging.info(_build_projects_info_text(projects_info))


# pylint:enable=unused-argument


FUNC_FOR_COMMAND = {
    "start": handle_start_command,
    "done": handle_done_command,
    "config": handle_config_command,
    "show": handle_show_command,
}

if __name__ == "__main__":
    main()
