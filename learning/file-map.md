# File map — Pipeline Bot

Last updated: 2026-09-03

Every path on disk, with **why it exists**. Statuses are evidence-based:
- `known` — explained in conversation, in the learner's own words.
- `generated` — machine-made. Never edit by hand; always rebuildable.
- `parked` — not yet earned. Each carries an honest note on when it comes due.

This map is parked-heavy on purpose. There are **two empty source files and zero
commits**, so there is almost nothing yet to know. Every parked line below is a
lesson already scheduled, not a gap to feel bad about.

---

## Root

### `herdr_client.py` — `known` (the `run()` function only)
The thin wrapper layer over the `herdr` CLI. One function per primitive
(split, start, prompt, wait, read, close), plus the subprocess/JSON/exit-code
plumbing they all sit on. Nothing in here knows what a "pipeline" is.
→ [[subprocess-exit-contract]] [[json-response-shapes]] [[custom-exceptions]]
→ [[pane-agent-primitives]] [[herdr-wait-trap]]

**Written so far (Section 2.1):** `run(*args)` — builds `["herdr"] + list(args)`
and calls `subprocess.run` with `capture_output=True, text=True` and `check` left
at its default `False`. Returns the `CompletedProcess` untouched; raises nothing.

**Written so far (Section 2.2):** the exception hierarchy — `HerdrError` (base,
never raised) with `HerdrWorldError` (exit 1) and `HerdrUsageError` (exit 2) as
siblings under it. Definitions only; nothing raises them yet.

**Written so far (Section 2.3):** `call(*args)` — the exit contract in one
place. Exit 2 raises `HerdrUsageError` from the plain-text stderr **first**, so
it never reaches the parser; exit 1 parses the JSON `error` object off stderr
into `HerdrWorldError`; exit 0 returns `json.loads(completed.stdout)`. Callers
get a dict or an exception, never a return code.

**Written so far (Section 2.4, learner-authored):** `HerdrOutputError` — the
fourth failure kind, for exit 0 with output that is not JSON. The exit-0 parse
in `call()` is wrapped in `try`/`except json.JSONDecodeError` so the
`herdr wait --help` trap raises a named error instead of returning help text as
data. → [[herdr-wait-trap]] [[try-except]]

**Written so far (Section 3.1):** `split_pane(direction="right")` — wraps
`pane split --current --direction <dir>` and returns
`response["result"]["pane"]["pane_id"]`. The only layout-creating call in the
wrapper. → [[pane-agent-primitives]] [[json-response-shapes]]

**Written so far (Section 3.3):** `start_agent(name, pane_id, kind="claude")` —
wraps `agent start <NAME> --kind <KIND> --pane <ID>` and returns
`response["result"]["agent"]`, the AgentInfo object (`agent_status`, `pane_id`,
`interactive_ready`, …). → [[pane-agent-primitives]] [[agent-kind-choice]]

**Written so far (Section 4.1, learner-authored):** `prompt_agent(target, text)`
— wraps `agent prompt <TARGET> <TEXT>`, submits without waiting, returns
`response["result"]["agent"]`. → [[submit-wait-race]]

**Written so far (Section 4.3, learner-authored):** `wait_for_agent(target,
until, timeout_ms=300000)` — wraps `agent wait <TARGET> --until <STATUS>
--timeout <MS>`, converting the int timeout with `str()` because argv is always
text. Returns the matched result. → [[submit-wait-race]] [[timeouts]]

**Written so far (Section 4.4):** `HerdrTimeout(HerdrWorldError)` plus the
`code == "timeout"` branch in `call()` (learner-authored), and
`wait_until_settled(target, timeout_ms=300000)` — phase one swallows a timeout,
phase two does not. → [[timeouts]] [[submit-wait-race]]

**Written so far (Section 7.2, learner-authored):** `wait_for_agent` now takes
`*until` instead of a single `until` -- `def wait_for_agent(target, *until,
timeout_ms=300000)`, building one `"--until"` + state pair per value in a
loop, then unpacking that list back into `call(...)` with `*until_args`.
`wait_until_settled`'s phase two now matches `"idle", "blocked", "done"`
instead of only `"idle"` -- a genuinely blocked writer can be noticed in
seconds instead of only after the full timeout. → [[variadic-parameters]]
[[agent-lifecycle-states]]

**Section 2 complete (2026-09-02).** `run()` + `call()` + four exception types.
Known gap: the exit-1 branch parses stderr outside any `try`. — wiring the exit codes to those types, and
the exit-code handling that stops the `herdr wait` trap from silently passing.

> Naming note: `project.md` calls this file `herdr.py`; on disk it is
> `herdr_client.py`. `herdr_client.py` is the better name — `herdr.py` would
> shadow nothing today, but a module named after the tool it wraps is a trap
> waiting for the day something does `import herdr`.

### `pipeline.py` — `known` (preflight guard only)
The orchestration itself: preflight, the three stages, the spawn/submit/wait
structure, handoff, consolidate, cleanup, exit code. Imports `herdr_client`
and contains no `subprocess` calls of its own.
→ [[stage-abstraction]] [[submit-wait-race]] [[fan-out-serialisation]]
→ [[filesystem-handoff]] [[stale-artifact-reporting]] [[preflight-env-guard]]
→ [[argv-and-cli-args]] [[resource-cleanup]]

**Written so far (Section 1.4, learner-authored):** the `preflight()` guard —
reads `HERDR_ENV`, refuses on anything but `"1"`, message to stderr, exits 1.
Plus the `if __name__ == "__main__":` entry point.

**Written so far (Section 2.5, learner-authored):** `import herdr_client`, and a
`try`/`except herdr_client.HerdrError` around the first real call that prints one
clean line to stderr and exits 1. → [[module-imports]] [[custom-exceptions]]

**Written so far (Section 3.4, learner-authored):** the entry point now splits a
pane, starts a `writer` agent in it, and prints the pane id and
`agent["agent_status"]` — all inside the one `try` that maps any `HerdrError` to
one stderr line and exit 1. → [[pane-agent-primitives]] [[agent-lifecycle-states]]

**Written so far (Section 4.5, learner-authored):** the WRITER stage, end to
end. Reads the task from `sys.argv[1]` and refuses with **exit 2** when it is
missing -- the same 1-vs-2 contract `herdr` speaks to us, now spoken to our own
caller. Then `prompt_agent(pane_id, task)` and `wait_until_settled(pane_id)`,
printing the settled `agent_status`. → [[argv-and-cli-args]]
→ [[exit-status-produced]] [[submit-wait-race]] [[timeouts]]

**Written so far (Section 5.3b, learner-authored):** the guard in front of
`shutil.rmtree` — normalize `WORK_DIR` with `os.path.normpath`, then refuse to
proceed if it is absolute, `"."`, or climbs out with `..`. Proven in both
directions: `ValueError` on `WORK_DIR = "."`, still works on `"work"`.
→ [[destructive-file-operations]] [[path-normalization]]

**Written so far (Section 5.3):** `import git_client`, and the
`baseline_commit()` call between `clear_work()` and the writer -- agent-written
at the learner's request. → [[git-baseline-commit]]

**Written so far (Section 5.2, learner-authored):** `WORK_DIR = "work"` and
`clear_work()` -- `shutil.rmtree(..., ignore_errors=True)` then `os.makedirs`,
called after the usage check and before anything reads `work/`. Defence one
against stale artifacts. → [[stale-artifact-reporting]]
→ [[destructive-file-operations]]

**Written so far (Section 5.5, learner-authored):** the handoff wired in —
`capture_diff(WORK_DIR)` after the wait, an empty diff treated as a failure
(stderr + exit 1), and the diff printed. The `except` widened to
`(herdr_client.HerdrError, git_client.GitError)` — agent-written at the
learner's request, after they spotted the stale comment themselves.
→ [[filesystem-handoff]] [[stale-artifact-reporting]] [[exit-status-produced]]

**Section 5 complete (2026-09-03).** `pipeline.py` prints exactly what the
writer changed. No `agent read`, no `--lines`, no terminal parsing anywhere in
the project.

**Written so far (Section 6.1, learner-authored):** the REVIEWER stage — a
second `split_pane()`, an agent named `reviewer`, `findings_path` chosen by the
pipeline (`os.path.join(WORK_DIR, "findings.md")`), a prompt assembled in Python
with the diff concatenated in, then `prompt_agent` + `wait_until_settled`.
→ [[filesystem-handoff]] [[pane-agent-primitives]]

**Written so far (Section 6.1b, learner-authored):** `RUN_ID = str(os.getpid())`
at module level, and both agents named from it (`writer-<pid>`,
`reviewer-<pid>`). Two runs back to back now survive where the second used to
die on `agent_name_taken`. → [[process-identity]] [[resource-cleanup]]

**Section 6.1b/1c fixed (2026-09-03):** unique agent names via `RUN_ID`, and
`capture_diff` now excludes `work/__pycache__` explicitly — the exclusion path
is built in `pipeline.py` (the file that knows this is a Python project) and
passed into `git_client.capture_diff`, which still knows nothing about Python.
→ [[module-boundary-ownership]] [[git-pathspec-exclusion]]

**Written so far (Section 6.2, learner-authored):** reading the findings back
-- `try: with open(findings_path) as f: findings = f.read()` /
`except FileNotFoundError`, printed at the end of the run. Agent-written at the
learner's request. → [[filesystem-handoff]]

**Live incident (Section 6.2):** a real hang in `wait_until_settled`, diagnosed
together rather than fixed silently -- see [[agent-lifecycle-states]] and
[[reading-a-traceback]] in the graph. No code changed as a result; it is a
finding, not yet a fix.

**Written so far (Section 6.3, learner-provoked, agent-written):** the second
stale-artifact defence -- `writer_status = settled["agent"]["agent_status"]`,
refusing to trust the diff unless it reads `"idle"`. Live-unreachable through
the current wait mechanics (documented, not hidden); proven as isolated logic
instead. → [[stale-artifact-reporting]] [[agent-lifecycle-states]]

**Written so far (Section 6.4, learner-authored):** CONSOLIDATE.
`review_prompt` gained one more explicit rule for the reviewer, the "VERDICT:
PASS`/`VERDICT: FAIL`" line contract, designed in conversation rather than
handed down. `verdict = "PASS" if "VERDICT: PASS" in findings else "FAIL"`,
`print(f"CONSOLIDATE: {verdict}")`, `sys.exit(0 if verdict == "PASS" else
1)`. Both branches verified: PASS live end to end, FAIL via isolated logic.
→ [[reading-a-review]] [[exit-status-produced]]

**Written so far (Section 6.5, learner-authored):** call site moved --
`git_client.require_clean(WORK_DIR)` is now the first line inside `try:`
(replacing the old `baseline_commit` if/else), so a dirty tree outside
`work/` now produces a clean `pipeline failed: ...` instead of a raw
traceback. → [[explicit-refusal-over-silent-absorption]]

**Section 6 complete.** The deliverable ran end to end live on both PASS and
FAIL, with the learner's own fix committed under their own message (`dd81913`).
`reviewer_settled`'s own status is still never checked before `findings.md`
is opened -- a real, named gap, parked for Section 7.

**Written so far (Section 7.3, agent-written):** the reviewer gets the same
state-before-file guard the writer got in 6.3 -- `reviewer_status =
reviewer_settled["agent"]["agent_status"]`, refusing `findings.md` unless it
reads `"idle"`. Agent-written at the learner's request; live-reachable this
time (task 7.2 fixed the shared `wait_until_settled` for both callers).
→ [[stale-artifact-reporting]] [[agent-lifecycle-states]]

### `git_client.py` — `known`
The boundary for the *other* external tool. Mirrors `herdr_client.py`: builds
argv, runs the CLI, turns failure into a named Python exception, and knows
nothing about pipelines. Exists as a separate module because one file per tool
boundary means swapping herdr's transport never touches git.
→ [[module-imports]] [[git-baseline-commit]] [[custom-exceptions]]
[[explicit-refusal-over-silent-absorption]]

**Written so far (Section 5.3):** `GitError` (one type -- git has no 1-vs-2
split to honour), `run_git(*args)` which raises on any nonzero exit, and
`baseline_commit(message)` which stages everything, skips the commit when
`git status --porcelain` comes back empty, and returns whether it committed.
The argv line and the porcelain guard are learner-authored; **the returncode
check in `run_git` was written by me** at the learner's request and is on the
re-earn list.

**Retired (Section 6.5):** `baseline_commit` is gone. Proven live that its
unscoped `git add -A` had *never* actually captured gitignored `work/` in any
run this project -- it only ever found and committed whatever unrelated files
happened to be dirty, which is how task 4's CONSOLIDATE code ended up buried
in an auto-generated "pipeline baseline: ..." message. Replaced by:

**Written so far (Section 6.5, learner-authored):** `require_clean(path)` --
raises `GitError` if `git status --porcelain -- . :(exclude)path` is
non-empty, i.e. anything *outside* `path` is dirty. A guard, not a committer:
refuses loudly instead of silently absorbing or silently leaking uncommitted
work into the next diff. → [[explicit-refusal-over-silent-absorption]]
[[git-pathspec-exclusion]]

**Written so far (Section 5.4, learner-authored):** `capture_diff(extra_path)` —
`git add -A`, then `git add -f <extra_path>` to override `.gitignore` for that
one command, then `git diff --cached` captured into a **string**, then
`git reset` so the index is left as it was found. The diff is returned, never
printed: that is what makes the handoff a Python value instead of something to
scrape. → [[filesystem-handoff]] [[git-diff-tracked-vs-untracked]]

### `.gitignore` — `parked` (3 lines)
Keeps machine-made and per-run files out of version control:
`__pycache__/`, `*.pyc` (Python bytecode), and `work/` (the pipeline's own
scratch directory, where the writer and reviewer drop their artifacts).
→ [[gitignore-purpose]] [[generated-vs-authored]]

**Comes due: Section 1.** Small file, real concept: the line between files you
author and files a machine regenerates.

> Note: `work/` is created at runtime and **cleared at the start of every run**
> by `clear_work()` — see [[stale-artifact-reporting]].
>
> **Collision found 2026-09-03 (Section 5.3):** because `work/` is ignored,
> `git add -A` never stages it, so `git diff --cached` shows nothing the writer
> wrote there. The `.gitignore` line and the handoff design disagree. Resolved
> in Section 5.4, not before.

### `__pycache__/` — `generated`
Python's cache of compiled bytecode, written automatically whenever a module is
imported or compiled. Machine-made, never edited, always regenerable — deleting
it costs nothing but a few milliseconds. Gitignored.

### `.git/` — `generated`
Git's own database: every commit, branch, and object. Machine-made, never
edited by hand. Deleting it destroys all history; it cannot be rebuilt from the
working tree.

**Current state (2026-09-02):** four commits, pushed to
`GH-Samir/Pipeline-Bot` (private). Section 1's deliverable, done.

---

## `learning/`

### `learning/project.md` — `known`
Triage output: who the learner is, the idea, the verified environment, the MVP
In/Parking-lot split, and the "trunk" of core components. Its four corrections
to the original brief are load-bearing and were re-verified on 2026-09-02.

### `learning/file-map.md` — `known`
This file.

### `learning/knowledge-graph.md` — `known`
What is understood, what is merely introduced, and what is untouched. The
honest ledger that decides what `/next-lesson` teaches next.

### `learning/plan.md` — `known`
The forward plan: the inherited decisions with an honest note on how well each
is understood, then eight sections, each with a deliverable you can demo and
exactly one reclaim task. This is what `/next-lesson` reads.

---

## Runtime and still-missing

### `work/` — `known` (exists as of 2026-09-03)
Runtime scratch directory. The writer's code and the reviewer's findings land
here at paths *the pipeline chooses*, so the pipeline never has to parse a
terminal transcript to find them. Gitignored, and wiped at the start of each
run.
→ [[filesystem-handoff]] [[stale-artifact-reporting]]

**Created and wiped by `clear_work()` since Section 5.2.** Before that it was
made by the writer agent itself, as a side effect of Section 4.5's task. Now the
pipeline owns it: deleted and recreated empty at the start of every run, so
anything found in it afterwards was necessarily produced by that run.

Contents are gitignored, so `git status` shows nothing after a run — which is
exactly why Section 5's handoff needs `git add -A` before `git diff --cached`.

### Tests — `parked` (do not exist)
There is no test file and no test runner. For a script whose failure mode is
"prints PASS while having done nothing," that absence is itself curriculum.
→ [[testing-absent]]

**Comes due: Section 5**, where the consolidate logic gets complex enough that
manual checking stops being honest.
