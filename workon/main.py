"""Main entry point for the script."""
import logging
import sys

from . import cli, errors, script


def init_logger(verbose):
    """Initialize logger based on `verbose`."""
    level = logging.ERROR
    if verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG

    logging.basicConfig(
        level=level, format='%(message)s'
    )


def main():
    """Execute the script commands."""
    try:
        user_config = script.get_config()
        args = cli.parse_args(user_config)
        init_logger(args.verbose)

        if args.command == 'start':
            script.start(args)
        elif args.command == 'done':
            script.done(args)
        elif args.command == 'open':
            script.open_project(args)
    except errors.ScriptError as exc:
        logging.error(exc)
        sys.exit(1)


if __name__ == '__main__':
    main()
