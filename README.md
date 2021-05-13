# GIT workon

Do you often need to clone some project, solve one task and remove it from your filesystem?

Do you often afraid that you might leave something unpushed or stashed?

Do you like to leave a perfectly clean desk after your work is done?

Then this script is for you.

## Usage

### CLI

#### Start to work on a project

When it is time to work on some project, use the `start` command:

```bash
workon start <my_project>
```

It will clone "my_project" from the GIT source, save it to the working directory and open the project in the specified
editor. Please refer to the [Configuration section](#configuration) to know how to configure the script.

See `workon start --help` for other available options on how to control the command.

#### Finish your work with a project

When you are done with your work, use `done` command:

```bash
workon done [<my_project>]
```

It will check:

* unpushed changes
* leaved stashes
* unstaged changes
 
and then remove a project folder from the working directory. If there is something left, the command will fail. But you
can use `-f/--force` flag if you are confident.

If the command ran without arguments, it will remove ALL projects from a working directory.

See `workon done --help` for other available options on how to control the command.

#### Open a project

Usually, you don't want to remember where are your projects are stored, but you need to open them. That's why `open`
command exists.

Usually, it is enough to run:

```bash
workon open <my_project>
```

See `workon open --help` for other available options on how to control the command.

### Configuration

The script's commands can be fully controlled by CLI arguments, but a couple of environment variables are supported for
convenience:

* `WORKON_GIT_SOURCE` - the project will be cloned from this source. Examples: "https://github.com/<my_username>",
  "git@github.com:<my_username>". May be overridden by `-s/--source` argument
* `WORKON_DIR` - the directory to which projects will be cloned. May be overridden by `-d/--directory` argument
* `WORKON_EDITOR` - the editor used to open a cloned project. May be overridden by `-e/--editor` argument. If not
  specified and `-e/--editor` argument is not provided, the script will try to use the editor specified by `$EDITOR`
  environment variable. If that variable not set, the script will try `vi` and `vim` consequently.

It is expected, that you will set all those variables once and then will only override them with CLI arguments when
needed.

The script will fail if both CLI argument not specified and environment variables are not set (except `WORKON_EDITOR`).
