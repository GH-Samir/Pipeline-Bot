"""Pipeline Bot -  orchestrates a WRITER -> REVIEWER -> CONSOLIDATE agent
pipeline inside Herdr."""

import os
import shutil
import sys
import git_client
import herdr_client


# The pipeline's scratch directory. One name, in one place, because two of the
# lines below delete whatever it points at.
WORK_DIR = "work"

# Agent names must not collide with any agent still alive in this herdr
# session. A process id is unique among *live* processes -- exactly the window
# that matters -- and it makes `herdr agent list` readable.
RUN_ID = str(os.getpid())


def clear_work():
    """Delete work/ and recreate it empty.

    Defence one against stale artifacts: nothing a previous run left behind can
    be mistaken for this run's output.
    """

    # Collapse the path first: "work/.." and "" both normalize to ".", so one
    # check below catches every way of accidentally naming the project root.
    target = os.path.normpath(WORK_DIR)

    if os.path.isabs(target) or target == "." or target.startswith(".."):
        raise ValueError(f"refusing to delete {WORK_DIR!r}")

    # Note we delete `target`, not WORK_DIR -- always operate on the exact value
    # you checked, never on the one you checked a copy of.
    shutil.rmtree(target, ignore_errors=True)
    os.makedirs(target)

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
    
    clear_work()
    
    panes_opened = []

    try:
        # The guard. Anything the tree shows after this point is the
        # writer's doing and nobody else's -- require_clean refuses to run
        # otherwise, instead of silently committing or silently ignoring
        # whatever was already dirty.
        git_client.require_clean(WORK_DIR)

        pane_id = herdr_client.split_pane()

        panes_opened.append(pane_id)

        agent = herdr_client.start_agent("writer-"+RUN_ID, pane_id)
        print(f"writer running in {pane_id}, status: {agent["agent_status"]}")

        # Submit and return immediately -- no waiting here, on purpose.
        herdr_client.prompt_agent(pane_id, task)
        print("prompt submitted, waiting for the writer to finish...")

        settled = herdr_client.wait_until_settled(pane_id)

        print(f"writer finished: {settled["agent"]["agent_status"]}")

        # `--until idle` only ever returns on a literal idle match or a
        # timeout -- so this should always read "idle" here. It is written
        # anyway, because "should always" is exactly the belief this reclaim
        # exists to stop trusting blindly. Whatever herdr reports about the
        # writer, checked *before* a single byte of its output is opened.
        writer_status = settled["agent"]["agent_status"]
        if writer_status != "idle":
            print(f"writer did not settle cleanly (status: {writer_status}); "
                  "refusing to trust anything on disk", file=sys.stderr)
            sys.exit(1)

        # pipeline.py is the one file that knows this is a Python project, so
        # this is where "__pycache__" gets named -- git_client.py never sees
        # that string.
        pycache_path = os.path.join(WORK_DIR, "__pycache__")
        diff = git_client.capture_diff(WORK_DIR, exclude=[pycache_path])

        if diff == "":
            print("Diff is empty, not changes have been made", file = sys.stderr)
            sys.exit(1)

        # No scraping anywhere: this string came from git, not from a terminal.
        print(diff)

        # We pick the path. The reviewer is told it; nothing ever hunts for it.
        findings_path = os.path.join(WORK_DIR, "findings.md")

        reviewer_pane = herdr_client.split_pane()

        panes_opened.append(reviewer_pane)

        reviewer_agent = herdr_client.start_agent("reviewer-"+RUN_ID, reviewer_pane)

        # The prompt is data we build, not something typed at a terminal.
        review_prompt = (
            "You are a code reviewer. Another agent was given this task:\n"
            f"{task}\n\n"
            "Here is the complete diff of what it produced:\n" +
            diff +
            "\n\nReview it. Then write your findings to this exact path, " +
            findings_path + " and stop. End your findings with exactly one line reading " +
            "`VERDICT: PASS` or `VERDICT: FAIL`, and nothing else on " +
            "that line. Do not change any other file."
        )

        herdr_client.prompt_agent(reviewer_pane, review_prompt)
        reviewer_settled = herdr_client.wait_until_settled(reviewer_pane)

        print("reviewer finished")

        # Same defence the writer got in 6.3: check state before opening
        # anything. `wait_until_settled` now matches idle/blocked/done for
        # either caller (fixed once, in 7.2, for both stages), so this is
        # reachable through the live pipeline, not just proven in isolation.
        reviewer_status = reviewer_settled["agent"]["agent_status"]
        if reviewer_status != "idle":
            print(f"reviewer did not settle cleanly (status: {reviewer_status}); "
                  "refusing to trust anything it wrote", file=sys.stderr)
            sys.exit(1)

        try:
            with open(findings_path) as f:
                 findings = f.read()
        except FileNotFoundError:
            findings = "no findings file was written"

        verdict = "PASS" if "VERDICT: PASS" in findings else "FAIL"

        print(f"CONSOLIDATE: {verdict}")
        print(findings)

        sys.exit(0 if verdict == "PASS" else 1)
    # Both tool boundaries, because both can raise inside this try. A new
    # boundary added later has to be added here too -- the comment that used to
    # claim "every failure kind" was already false the moment git arrived.
    except (herdr_client.HerdrError, git_client.GitError) as exc:
        print(f"pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)

    finally:
        for pane in panes_opened:
            try:
                herdr_client.close_pane(pane)
            except (herdr_client.HerdrError) as exc:
                print(f"An error occured when closing this pane: {pane} {exc}", file=sys.stderr)

