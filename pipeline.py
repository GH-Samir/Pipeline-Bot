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

    try:
        panes = herdr_client.call("pane", "list")
    # The base, so every failure kind lands here -- including ones added later.
    except herdr_client.HerdrError as exc:
        print(f"pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(panes)
