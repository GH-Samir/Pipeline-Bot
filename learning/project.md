# Project: Pipeline Bot

## About me
- Comfortable in the terminal; editing in Neovim, running Herdr as an agent multiplexer.
- Goal is understanding the multi-agent orchestration pattern, not shipping polish.
- Wants to write every line and understand it — not receive finished code.
- Stretch goal on the roadmap: fan the WRITER stage out to 3 parallel agents.

## The idea
A Python CLI that orchestrates a sequential WRITER -> REVIEWER -> CONSOLIDATE
agent pipeline inside Herdr. The coding task itself stays trivial on purpose;
the subject is the orchestration mechanics — spawning agents in panes,
detecting completion without blind polling, moving data between stages, and
failing honestly when an agent gets stuck.

## Verified environment (checked 2026-09-02, not from memory)
- `herdr 0.8.2`, binary `/usr/bin/herdr`, **protocol 20**.
- `herdr --skill` (195 lines) is Herdr's own agent-control doc. First stop.
- `herdr api schema --output <path>` dumps the full JSON schema and works
  with no server running. This is how you check response shapes.

### Corrections to my original assumptions
1. **`herdr wait` does not exist.** `herdr wait --help` prints root help and
   **exits 0**. Real primitives: `herdr agent wait`, `herdr pane wait-output`.
2. **`agent start` never creates layout.** The pane must already exist and be
   at a shell prompt. Always `pane split` then `agent start`.
3. **Protocol is 20**, not 16/17.
4. **The `--lines` cap is not the real constraint.** Agents run on the
   terminal's *alternate screen*; rows leaving it never enter Herdr's
   scrollback, so no `--lines` value recovers a long transcript.

### Response shapes (from `herdr api schema`)
- Success: `{"id":..., "result": {"type": <discriminator>, ...}}`
- Error:   `{"id":..., "error": {"code":..., "message":...}}`, exit status 1.
- CLI syntax error: exit status 2.
- `pane split`  -> `result.pane.pane_id`
- `agent get`   -> `result.agent.agent_status`
- `agent read`  -> `result.read.text`   (note: `read`, not `text` directly)
- `agent wait`  -> `result.event.data.*` — a **wait_matched event**, not an
  agent object, and the payload key varies by event kind. Re-reading status
  via `agent get` after a wait is shape-stable and simpler.

### Agent lifecycle states
`idle` `working` `blocked` `done` `unknown`
- `idle` requires the tab to have been *seen* in the focused UI. CLI reads do
  not mark it seen. Background panes therefore settle as **`done`**, not
  `idle`. Hardcoding `--until idle` hangs forever.
- `blocked` = an approval/question dialog. `agent prompt` refuses a blocked
  agent with `agent_blocked` before writing any bytes.
- `unknown` = present but unclassifiable. **Not** a synonym for finished.

## MVP
### In
- Preflight: refuse to run unless `HERDR_ENV=1`.
- WRITER: split a pane, start an agent, submit a task, wait for it to settle.
- Handoff via the **filesystem**, not scrollback: the writer writes to a path
  we choose; the script captures `git diff`.
- REVIEWER: second pane, second agent, fed the path and the diff, writes its
  findings to a path we choose.
- CONSOLIDATE: read the files, print a summary, emit PASS/FAIL and an exit code.
- Clean up only the panes we created.

### Parking lot (v2)
- Fan WRITER out to 3 parallel agents.
- Raw Unix socket API instead of the CLI wrappers.
- Retry-on-`blocked` with a human confirmation step.

## The trunk — core components
### Source control (git)
Already initialised here. Doubles as a working part of the pipeline, not just
a safety net: `git diff` is how the reviewer learns what the writer did.

### Subprocess wrapper
One function that runs `herdr`, parses JSON, and turns the exit contract into
Python exceptions. Everything else builds on it. Getting the error handling
right here is what stops the `herdr wait` trap from silently passing.

### The pane/agent primitives
Thin one-call-per-function layer: split, start, submit, wait, read, close.
No pipeline logic. Read it once, trust it, move on.

### The stage abstraction
Takes a *list* of agents even when there is one, and runs three phases —
spawn all, submit to all, wait on all. This is the whole parallel stretch goal,
paid for in advance. Reversing the submit and wait loops is what silently
serialises a fan-out.

### The submit/wait split
`agent prompt --wait` couples the two and is the one thing that would break
the fan-out. Splitting them reintroduces a race (`agent wait` matches
*current* state), which you handle by first observing the transition into
`working`, then waiting for settle.

### Data handoff
Herdr sequences the agents; the filesystem carries the data. Nothing in the
pipeline parses a long transcript.

### Failure reporting
Check agent state *before* trusting files on disk, and clear last run's
outputs at startup — otherwise a stale artifact gets reported as this run's
pass.

## Next
Write `herdr.py` then `pipeline.py`. Worked example given for the subprocess
wrapper; the rest is mine to write.
