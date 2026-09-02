"""Thin wrapper over the herdr CLI.

Nothing in this file knows what a pipeline is. Swapping the CLI for the raw
socket API should change this file and nothing above it.
"""

import json
import subprocess


class HerdrError(Exception):
    """Base for every failure this wrapper reports.

    Never raised directly. A caller who doesn't care which kind of failure it
    was catches this one and gets them all.
    """


class HerdrWorldError(HerdrError):
    """Exit 1: herdr parsed the command fine and the world said no.

    No server running, pane doesn't exist, agent is blocked. Sometimes
    retryable -- the command was valid, the conditions weren't.
    """


class HerdrUsageError(HerdrError):
    """Exit 2: herdr never parsed the command -- the bug is in our source.

    A misspelled subcommand or flag. Never retryable: the same argv produces
    the identical failure every time, so the fix is in this file, not in the
    world. herdr reports these as plain text, not JSON.
    """


def run(*args):
    """Run `herdr <args>` and hand back the finished process, untouched.

    Deliberately does not raise on failure. Reading the exit status is the
    caller's job, because this project needs to tell exit 1 from exit 2 --
    and needs to distrust exit 0.
    """

    argv = ["herdr"] + list(args)
    
    completed = subprocess.run(argv, capture_output=True, text=True)

    return completed


def call(*args):
    """Run `herdr <args>` and return the parsed JSON result.

    The exit contract, enforced in one place: success gives you a dict,
    failure gives you an exception with a name that says which kind.
    """

    completed = run(*args)

    # Checked first: exit 2's plain text must never reach json.loads.
    if completed.returncode == 2:
        raise HerdrUsageError(completed.stderr.strip())

    if completed.returncode == 1:
        payload = json.loads(completed.stderr)
        error = payload["error"]
        raise HerdrWorldError(f"{error['code']}: {error['message']}")

    # Exit 0: JSON on stdout.
    return json.loads(completed.stdout)
