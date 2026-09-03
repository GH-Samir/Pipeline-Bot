"""Pipeline Bot -  orchestrates a WRITER -> REVIEWER -> CONSOLIDATE agent
pipeline inside Herdr."""

import os
import shutil
import sys
import herdr_client


# The pipeline's scratch directory. One name, in one place, because two of the
# lines below delete whatever it points at.
WORK_DIR = "work"


def clear_work():
    """Delete work/ and recreate it empty.

    Defence one against stale artifacts: nothing a previous run left behind can
    be mistaken for this run's output.
    """

    # TODO(you): two lines, in this order.
    #   shutil.rmtree(<path>, ignore_errors=True)
    #       Deletes the directory and everything in it. ignore_errors=True so
    #       the very first run -- where work/ does not exist yet -- is not a
    #       crash.
    #   os.makedirs(<path>)
    #       Recreates it, empty.
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    os.makedirs(WORK_DIR)

def preflight():
    """Refuse to run unless we are inside a Herdr-managed pane."""

    herdr_env = os.environ.get("HERDR_ENV", "")

    if herdr_env != "1":
        print("You are not inside a Herdr-managed pane!, ", file = sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    preflight()
    print("preflight ok: inside Herdr")

    # sys.argv is a list of strings: argv[0] is this script's own name, and
    # everything after it is what the caller typed.
    if len(sys.argv) < 2:
        print('usage: python3 pipeline.py "<task for the writer>"', file=sys.stderr)
        sys.exit(2)

    task = sys.argv[1]

    # TODO(you): call clear_work(). The placement is the real decision here --
    # it has to run before anything could read work/, and nowhere near where it
    # could delete this run's output.
    clear_work()

    try:
        pane_id = herdr_client.split_pane()
        agent = herdr_client.start_agent("writer", pane_id)
        print(f"writer running in {pane_id}, status: {agent["agent_status"]}")

        # Submit and return immediately -- no waiting here, on purpose.
        herdr_client.prompt_agent(pane_id, task)
        print("prompt submitted, waiting for the writer to finish...")

        settled = herdr_client.wait_until_settled(pane_id)

        print(f"writer finished: {settled["agent"]["agent_status"]}")

    # The base, so every failure kind lands here -- including ones added later.
    except herdr_client.HerdrError as exc:
        print(f"pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)
