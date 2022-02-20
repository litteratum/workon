"""Main entry point for the script."""
import logging
import sys

from . import cli, config, script


def init_logger(verbose):
    """Initialize logger based on `verbose`."""
    level = logging.DEBUG if verbose >= 1 else logging.INFO

    logging.basicConfig(level=level, format="%(message)s")


def main():
    """Execute the script commands."""
    try:
        user_config = config.get_config(script.CONFIG_PATH)
        args = cli.parse_args(user_config)
        init_logger(args.verbose)

        if args.command == "start":
            script.start(args)
        elif args.command == "done":
            script.done(args)
        elif args.command == "config":
            script.config(args)
    except KeyboardInterrupt:
        logging.info("\nCanceled by user")
        sys.exit(0)
    except config.ConfigError as exc:
        logging.error("Configuration error: %s", exc)
    except script.ScriptError as exc:
        logging.error(exc)
        sys.exit(1)
    except Exception as exc:  # pylint:disable=broad-except
        logging.error("Unexpected script error: %s", exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
