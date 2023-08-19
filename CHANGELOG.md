# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
### Fixed
* Strip project name. So now `gw start project/` is the same as `gw start project`

### Added
* Support for Python 3.11
* Better CI/CD


## [3.0.0] - 2022-11-29
### Changed

* `done` command now does not remove non-git files because in some cases it may be dangerous


## [2.1.0] - 2022-02-22
### Added
* `show` command


## [2.0.0] - 2022-02-13
### Changed
* `config` command now does not open the configuration. Instead, it only inits and shows it

### Refactored
* Completely reorganized the codebase


## [1.3.0] - 2022-02-13
### Added
* `config` command
* `poetry` integration
* `tox` integration
* Integrate and improve linting

### Removed
* Config template copy on installation


## [1.2.5] - 2022-02-12
### Fixed
* Strip a project name to support command like `gw done project/`

### Added
* Apply `black` formatter
* Handling for `KeyboardInterrupt`


## [1.2.4] - 2021-11-14
### Fixed
* Don't check directories without ".git" folder
* `pylint` warnings
* Handling of unexpected script errors


## [1.2.3] - 2021-10-31
### Fixed
* A project(s) now is/are not removed if the check for unpushed git tags fails


## [1.2.2] - 2021-09-30
### Fixed
* Adjust for git_workon -> gw update (completions and README.md)


## [1.2.1] - 2021-09-29
### Fixed
* Log appropriate error when clone fails for all configured sources
* `done` command: check `force` first to speedup execution (if `force` is True, there is no need to check for unpushed
  entities)

## [1.2.0] - 2021-09-29
### Changed
* `done` command now shows ALL not pushed entities
* `start` command: log clone errors only in verbose mode
* Console script was renamed: `git_workon` -> `gw`

### Added
* `done` command now shows information about unpushed tags
* Better description for commands


## [1.1.2] - 2021-09-28
### Added
* Package meta
* Improved documentation
* Improved packaging

## [1.1.1] - 2021-09-22
### Fixed
* Add setup.cfg and include `config.json` into distribution
* Remove user config creation from the top level of `setup.py`

## [1.1.0] - 2021-09-22
### Changed
* Rename to `git_workon`

### Added
* LICENSE file

## [1.0.0] - 2021-07-31
### Added
* Simple bash completions
* Better logging for `start` command
* Small README.md improvements

### Changed
* Install user config file manually in "setup.py"

## [0.3.0] - 2021-07-26
### Removed
* `open` command
* `errors.py` module. Now all script exceptions live inside `script.py` module

### Changed
* `start` command now opens a project if it exists
* Default logging level is INFO (was ERROR before). Logging generally improved

## [0.2.1] - 2021-06-23
### Fixed
* `done` command: also remove named pipes and symbolic links

### Added
* Describe how to run integration tests
* Show detailed information about left stashes

## [0.2.0] - 2021-06-05
### Changed
* Use configuration file instead of environment variables

## [0.1.0] - 2021-05-13
### Added
* Tests coverage target to Makefile
* `open` command description
* Improve force logs for `done` command

### Fixed
* Made some unit tests to be environment-agnostic

### Changed
* Remove `-f/--force` flag from `start` command. Allow multiple projects

## [0.0.4] - 2021-05-08
### Added
* `done` command now also removes files
* `done` command now really tries to remove all projects
* `open` command for opening already started projects

### Fixed
* Correctly handle exception raised when specified editor does not exist

## [0.0.3] - 2021-05-06
### Added
* `done` command now also checks unstaged changes

### Fixed
* Add `--no-open` flag to integration tests to prevent unwanted opens

## [0.0.2] - 2021-05-06
### Added
* `start` command: open cloned project in a specified editor
  * `-e/--editor` and `-n/--no-open` arguments

### Fixed
* Small script help fixes/improvements

## [0.0.1] - 2021-05-05
### Added
* Initial tested version
