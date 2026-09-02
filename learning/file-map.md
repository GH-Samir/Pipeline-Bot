# File map — Pipeline Bot

Last updated: 2026-09-02

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

**Still comes due: Sections 4–6**, one stage at a time.

### `.gitignore` — `parked` (3 lines)
Keeps machine-made and per-run files out of version control:
`__pycache__/`, `*.pyc` (Python bytecode), and `work/` (the pipeline's own
scratch directory, where the writer and reviewer drop their artifacts).
→ [[gitignore-purpose]] [[generated-vs-authored]]

**Comes due: Section 1.** Small file, real concept: the line between files you
author and files a machine regenerates.

> Note: `work/` is ignored but does not exist yet. It is created at runtime and
> **cleared at the start of every run** — see [[stale-artifact-reporting]].

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

## Not on disk yet, but designed

### `work/` — `parked`
Runtime scratch directory. The writer's code and the reviewer's findings land
here at paths *the pipeline chooses*, so the pipeline never has to parse a
terminal transcript to find them. Gitignored, and wiped at the start of each
run.
→ [[filesystem-handoff]] [[stale-artifact-reporting]]

**Comes due: Section 4**, with the handoff.

### Tests — `parked` (do not exist)
There is no test file and no test runner. For a script whose failure mode is
"prints PASS while having done nothing," that absence is itself curriculum.
→ [[testing-absent]]

**Comes due: Section 5**, where the consolidate logic gets complex enough that
manual checking stops being honest.
