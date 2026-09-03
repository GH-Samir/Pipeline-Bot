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


def require_clean(path):
    """Raise GitError if anything outside `path` is dirty.

    `path` is excluded from the check: clear_work() already manages it at the
    filesystem level, and it's gitignored anyway, so git has nothing
    meaningful to say about it.
    """

    status = run_git("status", "--porcelain", "--", ".", f":(exclude){path}")

    if status != "":
        raise GitError(
            f"working tree has uncommitted changes outside {path!r}; "
            "commit your own work before running the pipeline"
        )

def capture_diff(extra_path, exclude=()):
    """Stage everything that changed since the baseline and return the diff.

    The diff is *returned as a string*, not printed. That is the whole point of
    this section: the reviewer gets handed a Python value, so nothing anywhere
    has to scrape a terminal to find out what the writer did.

    `extra_path` is force-staged even if .gitignore excludes it -- this module
    has no idea what "work/" is, so the caller says which path to include.
    `exclude` is the same idea in reverse: paths under `extra_path` to leave
    out even though -f would otherwise force them in. This module has no idea
    what "__pycache__" is either -- the caller says what to leave out, the same
    way it says what to include.
    """

    run_git("add", "-A")

    # -f overrides .gitignore for this one command. A ":(exclude)" pathspec
    # overrides -f right back, so the caller's exclusions still win. Nothing
    # here commits, so the ignored path never enters history either way.
    run_git("add", "-f", extra_path, *[f":(exclude){p}" for p in exclude])

    diff = run_git("diff", "--cached")


    run_git("reset")


    return diff
