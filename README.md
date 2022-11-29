[![tests](https://github.com/ReturnedVoid/workon/actions/workflows/ci.yml/badge.svg)](https://github.com/ReturnedVoid/workon)

# GIT workon

Do you often need to clone some project, solve one task and remove it from your filesystem?

Are you often afraid that you might leave something unpushed or stashed?

Do you like to leave a perfectly clean desk after your work is done?

Then this script is for you.

## Installation

The package is available on `PyPi` and can be installed with `pip`:

```bash
pip install git-workon
```

## Usage

### Configuration

The script commands can be fully controlled by CLI arguments, but it is much convenient to have a configuration file
defining most of parameters. There is a special `config` command that will help you to prepare suitable configuration.

```bash
gw config [options]
```

This command will:

* Create configuration directory if it does not exist. It will use OS-specific config directory, e.g.
  `~/.config/git_workon` for Linux
* Copy template configuration file to the configuration directory if it does not exist

The configuration file is a simple JSON contains the following parameters:

* `sources` - the array of sources from which projects will be cloned. Clone attempts will be done sequentially.
  Example:

  ```json
  "sources": [
    "https://github.com/<my_username>",
    "git@github.com:<my_username>"
  ]
  ```

  May be overridden by `-s/--source` argument. You can also define multiple sources: `-s first second -s third`
* `dir` - the working directory. All projects will be cloned to this directory. May be overridden by `-d/--directory`
  argument. `~` in path is supported
* `editor` - the editor used to open a cloned project or the configuration. May be overridden by `-e/--editor` argument.
  If not specified and `-e/--editor` argument is not provided, the script will try to use the editor specified by
  `$EDITOR` environment variable. If that variable is not set, the script will try `vi` and `vim` consequently

Configuration example:

```json
{
  "dir": "~/git_workon",
  "editor": "vim",
  "sources": [
    "https://github.com/pallets",
    "https://github.com/pypa"
  ]
}
```

### Start to work on a project

When it is time to work on some project, use the `start` command:

```bash
gw start <my_project> [options]
```

This command will:

* If the project with a given name already exists in the working directory:
  * open it with a configured editor
* If the project with a given name does not exist:
  * clone it from git sources into the working directory
  * open the project with a configured editor

See `gw start --help` for other available options on how to control the command.

### Finish your work with a project

When you are done with your work, use `done` command:

```bash
gw done [<my_project>] [options]
```

This command will:

* Check for left stashes
* Check for unpushed commits
* Check for left unstaged changes
* Check for unpushed tags
* If anything from above was not pushed:
  * fail with an error describing what was left unpushed
* If everything was pushed:
  * remove a project from the working directory

If a project name was not passed, the command will try to remove all git repos from the working directory.

See `gw done --help` for other available options on how to control the command.

### Show all tracked projects

To list all projects under the working directory, use `show` command:

```bash
gw show [options]
```

This command will check every project status and colorize the output according to it:

* Clean (everything is pushed) - green color
* Dirty (something is not pushed) - yellow color
* Undefined (not a git project) - white color

See `gw show --help` for other available options on how to control the command.

## Bash completions

Implemented as a bash script `workon_completions`. Currently, it adds completions only for basic commands.
To enable completions, simply copy the script to `/etc/bash_completion.d/` or copy it anywhere and source when you
need.
