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


class HerdrOutputError(HerdrError):
    """Herdr passed with exit code 0 however returned something that wasn't JSON"""


class HerdrTimeout(HerdrWorldError):
    """Did not produce the state in time, try increasing timeout"""

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
        if error['code'] == "timeout":
            raise HerdrTimeout(f"{error['code']}: {error['message']}")
        raise HerdrWorldError(f"{error['code']}: {error['message']}")

    # Exit 0 is not proof of anything -- `herdr wait --help` exits 0 with help
    # text. Trust the shape of the reply, not the status.
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise HerdrOutputError(
            f"herdr exited 0 but did not return JSON: {completed.stdout[:60]!r}"
        )


def split_pane(direction="right"):
    """Split the current pane and return the new pane's id.

    The only call in this wrapper that creates layout. `direction` defaults to
    "right" so callers that don't care don't have to say.
    """

    response = call("pane", "split", "--current", "--direction", direction)

    # envelope -> payload -> the pane itself.
    return response["result"]["pane"]["pane_id"]


def start_agent(name, pane_id, kind="claude"):
    """Start an interactive agent in an existing pane, and return its info.

    The pane must already exist and be sitting at a shell prompt -- this call
    never creates layout. `name` is ours to choose ("writer", "reviewer");
    `kind` is which program herdr launches.
    """

    response = call("agent", "start", name, "--kind", kind, "--pane", pane_id)

    return response["result"]["agent"]


def prompt_agent(target, text):
    """Submit a prompt to a running agent and return its agent object.

    Submits and returns immediately -- no waiting of any kind. `target` is a
    pane id or an agent name; `text` is the whole prompt as one argument.
    """

    response = call("agent", "prompt", target, text)
    return response["result"]["agent"]


def wait_for_agent(target, *until, timeout_ms=300000):
    """Block until the agent reaches `until`, or the timeout expires.

    Returns the matched result. Verified live 2026-09-03: herdr 0.8.2 answers a
    wait with an `agent_info` payload, so the agent's state is right there --
    `result["agent"]["agent_status"]`, no follow-up `agent get` needed.
    """
    until_args = []
    for state in until:
        until_args.append("--until")
        until_args.append(state)
    # argv is always text: timeout_ms is an int and must be converted.
    response = call("agent", "wait", target, *until_args, "--timeout", str(timeout_ms))

    return response["result"]


def wait_until_settled(target, timeout_ms=300000):
    """The two-phase wait: confirm it started, then wait for it to finish.

    Phase one exists only to defeat the submit/wait race -- without it, the
    settle wait matches the state the agent was in before the prompt.
    """

    try:
        wait_for_agent(target, "working", timeout_ms=5000)
    except HerdrTimeout:
        # Not a failure: the agent may have finished before we looked. Phase
        # two settles it either way.
        pass

    return wait_for_agent(target, "idle", "blocked", "done", timeout_ms=timeout_ms)


