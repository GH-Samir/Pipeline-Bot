# Plan — Pipeline Bot

Written 2026-09-02, at the end of the adoption. Sections only; `/next-lesson`
breaks one section into tasks at a time.

---

## Inherited decisions

These were chosen before the adoption. Each is recorded with how well it is
currently understood, and where it gets revisited.

### Python — **understood as a decision, boring choice, correct**
Zero dependencies: `subprocess` and `json` are standard library. Verified
Python 3.14.7 on this machine.
> Challenged 2026-09-02 ("would it be better to write this in rust?"). Answer:
> no, for this project. The program waits on other processes ~100% of its
> runtime, so Rust's advantages buy nothing, and it would stack ownership,
> borrowing and async on top of the orchestration curriculum. **Rust is logged
> as a legitimate v3** — a raw-socket client in Rust, once the orchestration
> pattern is internalised, is one new thing instead of three.

### Herdr CLI wrappers, not the raw socket API — **understood, boring choice**
Herdr's own recommended starting point. The socket API stays in the parking lot.
> Checked forward 2026-09-02 (what survives a transport swap). Partial: the
> transport-layer answer was supplied by me, not retrieved. Logged `introduced`.
> **Revisited in Section 2**, where the wrapper is actually written — the
> file/module split only pays off if the reason for it is understood.

### Claude Code as the agent kind — **not yet examined**
`--kind claude`, one of 22 kinds the installed version supports. Nothing in the
design depends on which kind it is.
> **Revisited in Section 3**, with `agent start`.

### Filesystem + `git diff` for handoff, not scrollback — **the unusual one**
Most people's instinct is to read the agent's terminal output. This design
refuses to. The justification is the alternate-screen constraint — **which has
not been re-verified on this machine.**
> **Revisited in Section 5**, where re-proving it is the reclaim task. If it
> turns out to be false, this decision gets re-opened honestly.

### No framework, no database, no hosting — **deliberate**
A local CLI script needs none of the three. Worth knowing these were dodged on
purpose rather than forgotten.

---

## Sections

Eight sections. Each ends in something demonstrable, and each carries **exactly
one reclaim task** — take a `parked` file or a fuzzy inherited decision, explain
it, break it on purpose, predict the failure, fix it.

---

### Section 1 — Make the ground solid
*Receipt: fixed by the method, and urgent here — the repo has **zero commits**.*

Git baseline, `learning/` committed, and the preflight guard proven. This is not
housekeeping: `git diff` is a **functional component** of the pipeline, so a
baseline commit is a build dependency, not a safety net.

**Deliverable:** your work can never be lost, and `git log` shows a real
history. `HERDR_ENV` refusal demonstrated from a plain terminal.

**Reclaim task:** `.gitignore` and [[git-diff-tracked-vs-untracked]] — the
partial-credit concept. Create an untracked file, run `git diff`, watch it show
nothing, then `git add -A` and watch it appear. Break the belief that "zero
commits" was the cause.

**Tasks:**
- [x] 1. The baseline commit — the three places a file can live in git, and
      getting `.gitignore` + `learning/` into real history.
- [~] 2. ~~Reclaim: prove `git diff` ignores untracked files.~~ **Dropped
      2026-09-02** — git self-reported as prior knowledge, so this reclaim task
      has no target. Section 2's reclaim (the exit contract) is unaffected.
- [~] 3. ~~Prove `.gitignore` actually works.~~ **Dropped 2026-09-02** — same
      reason.
- [x] 4. Write the preflight guard in `pipeline.py`: read `HERDR_ENV`, refuse
      with a nonzero exit code. First real code of the project.
- [x] 5. Run it outside Herdr and watch it refuse; run it with the variable set
      and watch it pass. Commit.
- [x] 6. Push to GitHub — `gh auth login`, then create the repo and push.
      *Receipt: asked for during Section 1. Placed last because `git push`
      sends commits, so it depends on tasks 1 and 5 existing first.*

---

### Section 2 — The subprocess wrapper and the exit contract
*Receipt: `project.md`'s trunk, first item. `herdr_client.py` is 0 bytes today.*

One function that runs `herdr`, parses JSON, and turns the exit contract into
Python exceptions. Exit 1 → an error from the world (JSON `error` object).
Exit 2 → a bug in your own source (**plain text, not JSON** — `json.loads` will
throw here). Everything else in the project sits on this.

**Deliverable:** call `herdr pane list` with no server running and get a clean,
correctly-typed Python exception instead of a traceback.

**Reclaim task:** [[subprocess-exit-contract]] — the largest gap in the graph,
probed twice and taught entirely by me. Then break it on purpose: write the
`herdr wait` trap, watch `check=True` sail past exit 0, and watch root help text
get returned as if it were data.

**Tasks:**
- [x] 1. `run()` — build an argv list and call `subprocess.run`, capturing
      output as text and deliberately *not* raising on a nonzero exit.
- [x] 2. The exception types — a base plus one per failure kind, so callers can
      tell "the world said no" from "your source has a typo".
- [x] 3. Wire the exit contract in: 0 parses JSON, 1 parses the JSON `error`
      object, 2 is plain text and must never reach `json.loads`.
- [x] 4. Reclaim + break on purpose: write the `herdr wait` trap, watch
      `check=True` sail past exit 0 and hand back help text as if it were data.
- [ ] 5. Deliverable: `herdr pane list` with no server running raises a clean,
      correctly-typed exception. Commit.

---

### Section 3 — The pane and agent primitives
*Receipt: `project.md`'s trunk, "the pane/agent primitives".*

Thin one-call-per-function layer: `split`, `start`, `prompt`, `wait`, `read`,
`close`. No pipeline logic. A pane must already exist at a shell prompt —
`agent start` never creates layout.

**Deliverable:** from inside Herdr, one Python call splits a pane and starts a
live Claude Code agent in it. You watch it appear.

**Reclaim task:** [[json-response-shapes]] — `result.pane.pane_id`,
`result.agent.agent_status`, `result.read.text`. Break it by reading
`result.text` instead of `result.read.text` and predict the failure.

---

### Section 4 — The WRITER stage and a wait that actually works
*Receipt: MVP "In" list. The heart of the whole project.*

The stage abstraction — takes a *list* of agents even with one, and runs
spawn-all → submit-all → wait-all as three separate loops. The two-phase wait:
`--until working` to confirm it started, then settle. Timeouts on both, covering
the edge where a trivial task finishes before the first wait matches.

**Deliverable:** a writer agent takes a real task, and your pipeline correctly
detects when it is genuinely finished — not 1ms after submitting.

**Reclaim task:** [[submit-wait-race]] — confirm in code what was answered
verbally. Delete the `--until working` wait, run it, and watch the pipeline
declare victory instantly against an empty diff.

---

### Section 5 — Handoff: baseline, diff, capture
*Receipt: MVP "In" list, plus the flagged unverified claim in the graph.*

Clear `work/` at startup, baseline commit, `git add -A`, `git diff --cached`,
capture the result for the reviewer. The filesystem carries the data; Herdr only
sequences the agents.

**Deliverable:** print exactly what the writer changed, with no terminal
scraping anywhere in the codebase.

**Reclaim task:** [[alternate-screen-constraint]] — **re-verify it live.** This
is the one load-bearing claim still resting on a note rather than a test, and it
justifies this entire section's design. Start an agent, let it produce a long
transcript, and try to recover it with `agent read --lines`. If it turns out the
constraint is not real, the handoff decision gets re-opened.

---

### Section 6 — REVIEWER and CONSOLIDATE
*Receipt: MVP "In" list. Completes the three-stage pipeline.*

Second pane, second agent with a reviewer persona, fed the path and the diff,
writing findings to a path you choose. Then consolidate: **check agent state
before opening any file**, read, summarise, emit PASS/FAIL and an exit code.

**Deliverable:** the full WRITER → REVIEWER → CONSOLIDATE pipeline runs end to
end from one command and prints a real summary.

**Reclaim task:** [[stale-artifact-reporting]] — confirm in code. Run it once
successfully, then force the writer to block, run again, and prove the state
check catches what clearing outputs alone would miss on a half-written file.

---

### Section 7 — Failing honestly, and the first tests
*Receipt: `project.md`'s trunk, "failure reporting"; tests are absent and that
absence is curriculum.*

`blocked` handling (`agent prompt` refuses a blocked agent with `agent_blocked`
before writing any bytes), cleanup of **only** the panes we created, timeouts
everywhere. Then the first tests — placed here, where consolidate has grown
complex enough that checking by hand stops being honest.

**Deliverable:** a test that proves a blocked writer produces FAIL, not PASS.
The signature failure mode of this project, caught automatically.

**Reclaim task:** [[resource-cleanup]] — closing a pane you merely found rather
than created. Break it deliberately in a scratch session and watch what it costs.

---

### Section 8 — Fan WRITER out to three agents
*Receipt: promoted from `project.md`'s parking lot; the stated stretch goal.*

The structure was paid for in advance in Section 4. This section spends it.

**Deliverable:** three writers run genuinely in parallel, and **the clock proves
it** — time the three-loop version against a folded single-loop version.

**Reclaim task:** [[fan-out-serialisation]] — confirm in code what was answered
cleanly in conversation. The stopwatch is the test; nothing else distinguishes
the two versions.

---

## Still in the parking lot after Section 8

- Raw Unix socket API instead of the CLI wrappers.
- Retry-on-`blocked` with a human confirmation step.
- A Rust client against the raw socket — logged 2026-09-02 as a genuine v3.
