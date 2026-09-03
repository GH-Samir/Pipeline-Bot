"""Thin wrapper over the git CLI.

Mirrors herdr_client.py on purpose: one module per external tool. Nothing in
this file knows what a pipeline is, and nothing in it imports herdr.
"""

import subprocess


class GitError(Exception):
    """A git command that did not succeed.

    git's contract is simpler than herdr's -- there is no 1-vs-2 split to
    honour, so one exception type is enough. Anything nonzero is a failure.
    """


def run_git(*args):
    """Run `git <args>` and return its stdout.

    Unlike herdr_client.run(), this one DOES raise on failure -- there is no
    caller here that needs to inspect a status code, so hiding it behind an
    exception is the simpler contract.
    """

    argv = ["git"] + list(args)

    # check is left at its default False, so this does NOT raise when git exits
    # nonzero -- it comes back as a CompletedProcess with .returncode set. The
    # only thing that raises here is git failing to launch at all.
    completed = subprocess.run(argv, capture_output=True, text=True)

    # So the failure check is ours to make. Without it, a failed git command
    # returns an empty string that reads exactly like success.
    if completed.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")

    return completed.stdout


def baseline_commit(message):
    """Snapshot the repo so that anything appearing afterwards is the writer's.

    Without this, `git diff` after the run would also show whatever you had
    half-finished before you started it, and the reviewer would be handed your
    unfinished work as if the writer had done it.

    Returns True if a commit was made, False if the tree was already clean.
    """

    run_git("add", "-A")

    # `git status --porcelain` prints one line per changed path and nothing at
    # all when there is nothing staged or modified. `git commit` with nothing
    # to commit exits nonzero -- which run_git would raise on -- so we ask
    # first instead of committing and catching.
    # run_git already puts "git" in front, so the subcommand starts here.
    changes = run_git("status", "--porcelain")
    if changes == "":
        return False

    run_git("commit", "-m", message)
    return True


def capture_diff(extra_path):
    """Stage everything that changed since the baseline and return the diff.

    The diff is *returned as a string*, not printed. That is the whole point of
    this section: the reviewer gets handed a Python value, so nothing anywhere
    has to scrape a terminal to find out what the writer did.

    `extra_path` is force-staged even if .gitignore excludes it -- this module
    has no idea what "work/" is, so the caller says which path to include.
    """

    run_git("add", "-A")

    # -f overrides .gitignore for this one command. Nothing here commits, so
    # the ignored path still never enters history.
    run_git("add", "-f", extra_path)

    diff = run_git("diff", "--cached")


    run_git("reset")


    return diff
