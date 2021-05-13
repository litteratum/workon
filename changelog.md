# Changelog

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
