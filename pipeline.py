"""Pipeline Bot -  orchestrates a WRITER -> REVIEWER -> CONSOLIDATE agent
pipeline inside Herdr."""

import os
import sys
import herdr_client


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
