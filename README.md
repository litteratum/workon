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

### Start to work on a project

When it is time to work on some project, use the `start` command:

```bash
git_workon start <my_project>
```

This command will open the project if it already exist in the working directory, otherwise, it will clone "my_project"
from a GIT source, save it to the working directory and open it in the specified editor.
Please refer to the [Configuration section](#configuration) to know how to configure the script.

See `git_workon start --help` for other available options on how to control the command.

### Finish your work with a project

When you are done with your work, use `done` command:

```bash
git_workon done [<my_project>]
```

It will check:

* unpushed changes
* left stashes
* unstaged changes

and then remove the project folder from the working directory. If there is something left, the command will fail. But
you can use `-f/--force` flag if you are confident.

If the command run without arguments, it will try to remove ALL projects from a working directory.

See `git_workon done --help` for other available options on how to control the command.

## Configuration

The script commands can be fully controlled by CLI arguments, but it is much convenient to adjust the configuration
file located under `~/.config/git_workon/config.json`:

* `source` - the array of sources from which projects will be cloned. Clone attempts will be done sequentially.
  Example:

  ```json
  "source": [
    "https://github.com/<my_username>",
    "git@github.com:<my_username>"
  ]
  ```

  May be overridden by `-s/--source` argument. You can also define multiple sources: `-s first second -s third`
* `dir` - the directory to which projects will be cloned. May be overridden by `-d/--directory` argument. `~` in path
  is supported
* `editor` - the editor used to open a cloned project. May be overridden by `-e/--editor` argument. If not
  specified and `-e/--editor` argument is not provided, the script will try to use the editor specified by `$EDITOR`
  environment variable. If that variable is not set, the script will try `vi` and `vim` consequently

### Bash completions

Implemented as a bash script `workon_completions`. Currently, it adds completions only for basic commands.
To enable completions, simply copy the script to `/etc/bash_completion.d/` or copy it anywhere and source when you
need.
