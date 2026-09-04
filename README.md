# Pipeline Bot

A small Python CLI that orchestrates a sequential **WRITER → REVIEWER →
CONSOLIDATE** agent pipeline inside [Herdr](https://herdr.dev) (a
terminal-native agent multiplexer). Give it a task, and it spawns an agent to
do the work, spawns a second, independent agent to review the diff, and
prints a `PASS`/`FAIL` verdict with a matching exit code — no human has to
babysit either step.

## Requirements

- `herdr` on your `PATH`, and you must be running **inside a Herdr-managed
  pane** — the script refuses to start otherwise (`preflight()`).
- `git` — the project itself must be a git repository. The writer's changes
  are captured via `git diff`, not by reading agent output.
- Python 3, no third-party packages.

## Usage

From inside the project directory:

```
python3 pipeline.py "<task for the writer>"
```

Example:

```
python3 pipeline.py "write is_even.py that checks if a number is even"
```

This will:
1. Refuse to run unless your working tree is clean (aside from `work/`,
   which the pipeline manages itself).
2. Spawn a writer agent in a new pane, submit the task, and wait for it to
   settle.
3. Capture exactly what changed via `git diff` and print it — no scrollback
   scraping anywhere in the codebase.
4. Spawn a reviewer agent, hand it the diff, and wait for its findings.
5. Print `CONSOLIDATE: PASS` or `CONSOLIDATE: FAIL` plus the reviewer's
   findings, and exit `0` or `1` to match — scriptable, e.g.
   `python3 pipeline.py "..." && git commit`.
6. Close every pane it opened, whether the run succeeded or failed.

**Known limitation:** paths inside the script (`work/`, `git`/`herdr` calls)
are resolved relative to your shell's current directory, not the script's own
location — so you currently need to `cd` into the project first. Running
`python3 /path/to/pipeline.py "..."` from elsewhere will create a stray
`work/` folder and run git commands against the wrong repo.

## The parallel fan-out (stretch goal)

`pipeline.py` also exposes `run_writer_stage(tasks, panes_opened)` — spawn,
submit, and wait for a *list* of writers, running three separate loops
(spawn-all → submit-all → wait-all) instead of one loop per writer, so
multiple writers genuinely run at once instead of one after another. It's
proven out with real timing data in `time_fanout.py` (run
`python3 time_fanout.py` to reproduce), but it isn't wired into `pipeline.py`'s
own CLI yet — the command-line entry point still takes exactly one task.

`run_writer_stage_serial(tasks, panes_opened)` is the folded counterpart —
the same three operations in a single loop per writer — kept around
specifically to measure what serializing the fan-out costs.

## Files

| File | What it is |
|---|---|
| `pipeline.py` | The orchestration: preflight, the three stages, cleanup, exit code. |
| `herdr_client.py` | Thin wrapper over the `herdr` CLI — knows nothing about pipelines. |
| `git_client.py` | Thin wrapper over the `git` CLI — knows nothing about pipelines. |
| `test_pipeline.py` | The project's first automated test (`python3 test_pipeline.py`). |
| `time_fanout.py` | Benchmark script comparing the parallel and serial writer stages. |

## Status

Built as a learning project using the [Altitude](https://learnaltitude.com)
method — see `learning/plan.md` for the full build history, and
`learning/knowledge-graph.md` for what's actually understood versus just
written. All planned sections are complete.
