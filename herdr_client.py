"""Thin wrapper over the herdr CLI.

Nothing in this file knows what a pipeline is. Swapping the CLI for the raw
socket API should change this file and nothing above it.
"""

import subprocess


def run(*args):
    """Run `herdr <args>` and hand back the finished process, untouched.

    Deliberately does not raise on failure. Reading the exit status is the
    caller's job, because this project needs to tell exit 1 from exit 2 --
    and needs to distrust exit 0.
    """

    argv = ["herdr"] + list(args)
    
    completed = subprocess.run(argv, capture_output=True, text=True)

    return completed
