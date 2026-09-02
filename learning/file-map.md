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

### `herdr_client.py` — `parked` (empty, 0 bytes)
The thin wrapper layer over the `herdr` CLI. One function per primitive
(split, start, prompt, wait, read, close), plus the subprocess/JSON/exit-code
plumbing they all sit on. Nothing in here knows what a "pipeline" is.
→ [[subprocess-exit-contract]] [[json-response-shapes]] [[custom-exceptions]]
→ [[pane-agent-primitives]] [[herdr-wait-trap]]

**Comes due: Section 2.** This is the first file written, and the exit-code
handling in it is what stops the `herdr wait` trap from silently passing.

> Naming note: `project.md` calls this file `herdr.py`; on disk it is
> `herdr_client.py`. `herdr_client.py` is the better name — `herdr.py` would
> shadow nothing today, but a module named after the tool it wraps is a trap
> waiting for the day something does `import herdr`.

### `pipeline.py` — `parked` (empty, 0 bytes)
The orchestration itself: preflight, the three stages, the spawn/submit/wait
structure, handoff, consolidate, cleanup, exit code. Imports `herdr_client`
and contains no `subprocess` calls of its own.
→ [[stage-abstraction]] [[submit-wait-race]] [[fan-out-serialisation]]
→ [[filesystem-handoff]] [[stale-artifact-reporting]] [[preflight-env-guard]]
→ [[argv-and-cli-args]] [[resource-cleanup]]

**Comes due: Sections 3–6**, one stage at a time. Not written in one sitting.

### `.gitignore` — `parked` (3 lines)
Keeps machine-made and per-run files out of version control:
`__pycache__/`, `*.pyc` (Python bytecode), and `work/` (the pipeline's own
scratch directory, where the writer and reviewer drop their artifacts).
→ [[gitignore-purpose]] [[generated-vs-authored]]

**Comes due: Section 1.** Small file, real concept: the line between files you
author and files a machine regenerates.

> Note: `work/` is ignored but does not exist yet. It is created at runtime and
> **cleared at the start of every run** — see [[stale-artifact-reporting]].

### `.git/` — `generated`
Git's own database: every commit, branch, and object. Machine-made, never
edited by hand. Deleting it destroys all history; it cannot be rebuilt from the
working tree.

**Current state: zero commits.** Nothing here is protected yet. This is the
single most urgent fact in this map, and it is why Section 1 is Section 1.

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
