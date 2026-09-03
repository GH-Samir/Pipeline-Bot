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
refuses to. ~~The justification is the alternate-screen constraint.~~
> **Re-verified live 2026-09-03 (Section 5.1) — the justification was FALSE.**
> `herdr agent read w1:pC --source recent --lines 400`, after a Claude Code
> agent printed 300 numbered lines, returned **all 300** plus the startup
> banner that preceded them. Rows leaving the alternate screen are recoverable
> on this install. Sixth correction to the original brief.
>
> **The decision stands, on new grounds.** Two of them, both visible in that
> same output:
> 1. *It is UI, not data.* Learner's own words: "ui stuff might get mixed in
>    with the diff". The 300 numbers arrived wrapped in a Claude Code banner,
>    four hook errors, `●` bullets, box rules and a prompt box. Reading it means
>    parsing somebody else's interface, which changes whenever they ship.
> 2. *It is width-dependent.* `~/…/Pipeline-Bot` came back split as `Pipelin` /
>    `e-Bot` because the pane is narrow. A diff read this way breaks at
>    arbitrary columns, and the breaks move when the window is resized — the
>    same run yields different text. `git diff --cached` returns identical
>    bytes at any width.
>
> Not tested: whether a *much* longer transcript (3000 lines, not 300) still
> comes back whole. 300 is what was proven; do not claim more.

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
- [x] 5. Deliverable: `herdr pane list` with no server running raises a clean,
      correctly-typed exception. Commit.

---

### Section 2 — COMPLETE (2026-09-02)
All five tasks done. `pipeline.py` catches `HerdrError` and exits 1 with a
one-line message; no traceback reaches the user. Known gap carried forward: the
exit-1 branch's `json.loads(completed.stderr)` is not inside a `try`.

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

**Tasks:**
- [x] 1. `split_pane()` — wrap `pane split --current --direction right` and
      return the new pane id. The first call that succeeds: exit 0, real JSON,
      and a visible second pane. Must be run from inside a Herdr session.
- [x] 2. Reclaim: [[json-response-shapes]] — read the real response, then break
      it on purpose (`result["pane_id"]` instead of `result["pane"]["pane_id"]`)
      and predict the failure before running it.
- [x] 3. `start_agent()` — wrap `agent start --pane <id> --kind claude`, and
      revisit the inherited `--kind claude` decision now that it is being used.
- [x] 4. Deliverable: one run of `pipeline.py` splits a pane and a live Claude
      Code agent appears in it. Commit.

---

### Section 3 — COMPLETE (2026-09-03)
`pipeline.py` splits a pane and boots a live Claude Code agent into it in one
run. Known gap carried forward: nothing records the pane id for cleanup, and
nothing waits for the agent — both are Sections 4 and 7.

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

> **Finding 2026-09-03, read live from `agent prompt --help`:** herdr's own
> `--wait` already requires an observed state change within 5000ms before
> matching a settled state, returning `agent_prompt_stalled` if none comes. So
> the two-phase wait `project.md` prescribes is **one** answer to the race, not
> the only one. Task 3 makes that an explicit decision instead of an inherited
> assumption.

**Tasks:**
- [x] 1. `prompt_agent()` — wrap `agent prompt <TARGET> <TEXT>` with no waiting
      at all, and watch the race happen live.
- [x] 2. Reclaim: [[submit-wait-race]] — prompt, then immediately `agent wait`,
      and predict what it matches before running it.
- [x] 3. The decision: herdr's `prompt --wait --until` versus the manual
      two-phase wait. Pick one, record why, and write `wait_for_agent()`.
      > **Decided 2026-09-03: the manual two-phase wait (B).** herdr's
      > `prompt --wait` is less code and closes the race server-side, but it
      > blocks submission until that agent finishes -- which serialises a
      > fan-out. Three writers would cost 3x wall-clock and the stage's list
      > would be decorative. Submission must return immediately for
      > spawn-all -> submit-all -> wait-all to mean anything.
      > **Revisit if** the parallel stretch goal is ever dropped: with one
      > agent per stage, A is the better choice.
- [x] 4. Timeouts everywhere, including the edge where a trivial task finishes
      before the first wait ever sees `working`.
- [x] 5. Deliverable: the writer takes a real task and the pipeline detects
      genuine completion. Commit.

---

### Section 4 — COMPLETE (2026-09-03)
`python3 pipeline.py "<task>"` splits a pane, boots a writer, hands it the task
from argv, and blocks until it genuinely settles. Verified live: the writer
wrote `work/reverse.py` and the pipeline waited for it instead of returning in
5ms.

**Carried forward, honestly: the stage abstraction was not built.** This
section's description prescribes a stage that takes a *list* of agents and runs
spawn-all → submit-all → wait-all as three loops. `pipeline.py` calls the three
wrapper functions inline, for one agent, in order.
> **Decided 2026-09-03:** leave it. A "list of one" abstraction with nothing to
> fan out is structure written against a guess, and the three-loop shape is
> only *observable* when there are three writers to time. It moves to
> **Section 8**, which now builds the structure it was going to spend.
> The cost is named: Section 8 is bigger than its description claims, because
> the down payment Section 4 promised was never made.

Known gap also carried: nothing checks that the writer produced anything. The
pipeline prints `idle` whether the file was written or not — Sections 5 and 6.

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
> **Done 2026-09-03. The constraint is not real** — see the corrected inherited
> decision above. The section's design survives on the UI-parsing and
> width-dependence arguments instead, so tasks 2–5 proceed unchanged.

**Tasks:**
- [x] 1. Reclaim, and it goes first: re-verify [[alternate-screen-constraint]]
      live. Let an agent produce a long transcript, then try to recover it with
      `agent read --lines`. Everything below is built on the answer, so the
      answer comes before the building.
- [x] 2. `clear_work()` — create `work/` and wipe it at the start of every run.
      The first of the two defences against [[stale-artifact-reporting]].
- [x] 3. The baseline commit — where git belongs in this codebase (not in
      `herdr_client.py`), and taking the "before" snapshot that makes "what did
      the writer change?" a answerable question.
- [x] 3b. Guard `WORK_DIR` before `shutil.rmtree` touches it — refuse empty,
      absolute, `"."`, or anything climbing out with `..`.
      > **Pulled forward from Section 7 on 2026-09-03, at the learner's
      > request.** Reason: `clear_work()` runs for real several times a session
      > and the only thing between it and the whole project is one string on
      > line 12. Nothing depended on the original ordering, so the trade is
      > only that task 4 slides by one. Section 7 keeps [[resource-cleanup]] as
      > its reclaim; this line leaves it.

- [x] 4. Capture the change — `git add -A` then `git diff --cached`, captured
      into a Python string rather than left to print itself.
      > **Blocker found in 5.3, and it must be resolved here:** `work/` is in
      > `.gitignore`, so `git add -A` never stages the writer's output and the
      > diff comes back empty. The `.gitignore` line written in Section 1 and
      > the handoff design written in the brief contradict each other. Options
      > are force-staging (`git add -f work`), un-ignoring `work/`, or having
      > the writer edit tracked files instead. Decide it out loud and record
      > why, the way the wait strategy was decided in 4.3.
      > **Decided 2026-09-03: force-staging (A).** `git add -f work` overrides
      > `.gitignore` for that one command, `git diff --cached` reads the
      > result, and `git reset` puts the index back so no human commit ever
      > carries the artifacts. **B was rejected** because un-ignoring `work/`
      > writes every run's artifacts into history permanently. **C was
      > rejected** because letting the writer edit tracked project files hands
      > every unattended agent a licence to edit real source -- a much larger
      > decision than a diff, and not one to make as a side effect of one.
      > **Revisit if** the writer's job ever becomes editing the project itself
      > rather than producing artifacts; then C is the natural design and the
      > force-stage disappears.
- [x] 5. Deliverable: print exactly what the writer changed, with no terminal
      scraping anywhere in the codebase. Commit.

---

### Section 5 — COMPLETE (2026-09-03)
`python3 pipeline.py "<task>"` clears `work/`, commits a baseline, spawns the
writer, waits for genuine completion, and prints the writer's diff and nothing
else. Verified live: three lines of `work/greet.py`, no UI chrome, no wrapping.
Grep confirms no `agent read` anywhere in the codebase — the deliverable's
"no terminal scraping" half is a fact about the code, not an intention.

**The section's own premise was disproven in task 1** and the design
re-grounded on better arguments; see the corrected inherited decision above.

Known gaps carried forward:
- An empty diff exits 1, but a *wrong* diff still passes. Nothing reads the
  content — that is Section 6's reviewer.
- Panes still accumulate; nothing closes what it opened. Section 7.
- `agent start` still hardcodes the name `"writer"`, so a second run in the
  same herdr session fails with `agent_name_taken`.

---

### Section 5 — COMPLETE (2026-09-03)
`python3 pipeline.py "<task>"` clears `work/`, commits a baseline, spawns the
writer, waits for genuine completion, and prints the writer's diff and nothing
else. Verified live: three lines of `work/greet.py`, no UI chrome, no wrapping.
Grep confirms no `agent read` anywhere in the codebase — the "no terminal
scraping" half of the deliverable is a fact about the code, not an intention.

**The section's own premise was disproven in task 1** and the design re-grounded
on better arguments; see the corrected inherited decision above.

Known gaps carried forward:
- An empty diff exits 1, but a *wrong* diff still passes. Nothing reads the
  content — that is Section 6's reviewer.
- Panes still accumulate; nothing closes what it opened. Section 7.
- `agent start` hardcodes `"writer"`, so a second run while the first writer is
  still alive fails with `agent_name_taken`. **Observed live 2026-09-03**
  (Section 6.1): `agent name writer is already used`. Earlier runs had not hit
  it, and I recorded it as "not observed" — that note was wrong within the hour,
  and this is the corrected record. Recovered by hand with `herdr pane close`.

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

**Tasks:**
- [x] 1. The reviewer stage — a second pane, a second agent, and a prompt built
      from the diff string the pipeline already holds. The reviewer is told
      *where to write*, so nothing has to hunt for its output.
- [x] 1b. Unique agent names per run — pulled forward from Section 7 because it
      **blocks repeat runs**: the second run of a session dies on
      `agent_name_taken` and needs a manual `herdr pane close` to recover.
- [x] 1c. Fix the over-staging your own reviewer found: `git add -f work` in
      `capture_diff` overrides *every* ignore rule beneath that directory, so
      `work/__pycache__/*.pyc` lands in the diff and goes straight into the
      reviewer's prompt. Confirmed by the learner against the evidence.
- [x] 2. Read the findings back — the pipeline opens the path it chose, and
      handles the file simply not being there.
      > **Live incident 2026-09-03, unplanned:** the same-tab-unfocused
      > deliverable run hung for 60-90s inside phase two's wait, well inside
      > its own 300s budget, even though a fresh `herdr agent wait` on the same
      > pane matched `idle` instantly. Interrupted with Ctrl+C; traceback
      > confirmed the hang was in `subprocess.run`, waiting on herdr, not in
      > our Python. Re-ran with the writer's new tab kept focused throughout,
      > and it completed cleanly. **Real evidence, not proof**, for the
      > already-flagged, previously-untested claim under
      > [[agent-lifecycle-states]]: idle detection for a *standing wait* may
      > depend on the pane having been seen/focused, even though a one-off
      > query reads state directly regardless of focus. One repeat with one
      > variable changed -- worth a deliberate re-test, not treated as settled.
- [x] 3. Reclaim: [[stale-artifact-reporting]] — check agent state **before**
      opening any file. Force a writer that settles without finishing, run
      again, and prove the state check catches what `clear_work()` alone
      cannot: a file that exists but is half-written.
      > **Done 2026-09-03, with an honest limitation.** Wrote the check --
      > `if writer_status != "idle": ... sys.exit(1)` -- right after the wait,
      > before `capture_diff` touches anything. But `herdr agent wait --until
      > idle` (per its own `--help`) matches **only** a literal idle transition
      > or times out; there is no third path where it returns holding
      > `"blocked"` or `"done"`. So through the live pipeline as written, this
      > branch is currently unreachable -- a genuinely blocked writer still
      > gets caught, just slower, via the existing `HerdrTimeout` -> `except`
      > path. Proven instead as isolated logic: same lines, run against a
      > fabricated `{"agent_status": "blocked"}`, correctly exited 1 with the
      > message. Then re-ran the real deliverable and confirmed a genuine PASS
      > still sails through unaffected. **To make this branch live-reachable,
      > `wait_for_agent` would need to pass multiple `--until` values (herdr
      > supports repeating the flag) so a real block returns fast instead of
      > timing out** -- named here as a design option, not built; it overlaps
      > Section 7's blocked-handling and belongs there.
- [x] 4. CONSOLIDATE — summarise, emit PASS/FAIL, and exit with a status that
      matches. The whole project's failure mode is a green run that did nothing.
      > **Done 2026-09-03.** Design worked out in conversation, not handed
      > down: since code can't judge English prose, the reviewer is told (in
      > `review_prompt`, the same "we pick it, it's told it" pattern already
      > used for `findings_path`) to end `findings.md` with an exact line,
      > `VERDICT: PASS` or `VERDICT: FAIL`. Learner caught unprompted that a
      > naive `"PASS" in findings` check would misread `"did NOT PASS
      > review"`, which is why the check is `"VERDICT: PASS" in findings`
      > against an anchored line, not a bare keyword search. Wrote
      > `verdict = "PASS" if "VERDICT: PASS" in findings else "FAIL"` and
      > `sys.exit(0 if verdict == "PASS" else 1)` themselves. Verified both
      > branches: PASS live end-to-end (`work/is_palindrome.py`, real
      > reviewer output, exit 0), FAIL via isolated logic against the exact
      > expression (same reason as 6.3 -- forcing a real reviewer to fail on
      > command isn't reliable to trigger live). One real gap named and
      > deliberately left open: `reviewer_settled`'s own status is still never
      > checked before `findings.md` is opened -- parked for Section 7,
      > tracked under [[stale-artifact-reporting]].
- [x] 5. Deliverable: WRITER → REVIEWER → CONSOLIDATE end to end from one
      command, printing a real summary. Commit.
      > **Done 2026-09-04, and not the task as originally scoped.** Orienting
      > for this task surfaced that task 4's commit (`da4dfa1`) only contained
      > `learning/` files -- the CONSOLIDATE code itself had been silently
      > swept into the *previous* run's auto-generated "pipeline baseline:
      > ..." commit. Chased that to its root and fixed it properly rather than
      > patching around it:
      > - `baseline_commit`'s unscoped `git add -A` silently skipped
      >   gitignored `work/` every single run this whole project -- it had
      >   *never* actually baselined `work/`, only ever whatever else happened
      >   to be dirty (which is exactly what caused the leak above).
      > - Scoping it to `work/` alone (`git add -A -f -- work`) proved the
      >   function's whole "commit" behaviour is permanently dead: `clear_work()`
      >   already empties `work/` on disk before this runs, so there is never
      >   anything left there for git to see.
      > - Retired `baseline_commit`. Replaced with `git_client.require_clean(path)`
      >   -- refuses (raises `GitError`) if anything *outside* `work/` is dirty,
      >   instead of silently committing it under a fake message or silently
      >   letting it leak into the next diff. Called from inside the `try:`
      >   block this time, so a real failure gets `pipeline failed: ...`
      >   instead of a raw traceback.
      > - Proven live at every step: the pre-fix leak actually happened and
      >   was caught by the reviewer (who correctly spotted out-of-scope
      >   changes but wrongly blamed the writer and wrongly recommended
      >   reverting -- judged and rejected, not accepted at face value); the
      >   post-fix guard correctly refused with a dirty tree (exit 1, clean
      >   message); and the final clean run passed end to end (`work/is_anagram.py`,
      >   real reviewer output, `CONSOLIDATE: PASS`, exit 0) with the learner's
      >   own fix committed under their own message (`dd81913`), pushed.
      > **Section 6 deliverable reached.** The full WRITER → REVIEWER →
      > CONSOLIDATE pipeline runs end to end from one command and prints a
      > real PASS/FAIL summary with a matching exit code -- proven on both
      > outcomes, live.

---

### Section 6 — COMPLETE (2026-09-04)
`python3 pipeline.py "<task>"` now runs the full three-stage pipeline: WRITER
writes, REVIEWER reviews against the diff and writes `VERDICT: PASS` or
`VERDICT: FAIL` to `findings.md`, CONSOLIDATE reads it, prints `CONSOLIDATE:
PASS`/`FAIL`, and exits 0/1 to match. Both outcomes proven live, not just in
isolation: a genuine PASS (`work/is_anagram.py`) and a genuine FAIL (a
diff-leak the reviewer correctly flagged, even though it misattributed the
cause).

Task 5 turned into more than its own scope: task 4's commit had silently
absorbed the CONSOLIDATE code under an unrelated auto-generated message,
which traced back to `baseline_commit` never having worked correctly for
`work/` in the first place -- see [[git-baseline-commit]]. It's retired now,
replaced by `git_client.require_clean()`, an explicit refuse-to-run guard --
see [[explicit-refusal-over-silent-absorption]].

Known gaps carried forward:
- `reviewer_settled`'s own status is never checked before `findings.md` is
  opened -- a reviewer that settles `blocked` mid-write would still be read
  as if it finished cleanly. Section 7.
- Panes still accumulate; nothing closes what it opened. Section 7.
- `capture_diff`'s own `git add -A` is unscoped by design (it needs to catch
  a writer that strays outside `work/`) -- this is why `require_clean` had to
  exist, not a leftover bug to fix.

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

> ~~**Carried in from Section 5.2:** a guard on `WORK_DIR`.~~ **Moved to
> Section 5, task 3b on 2026-09-03** at the learner's request — the risk was
> live, not hypothetical. See there.

---

### Section 8 — Fan WRITER out to three agents
*Receipt: promoted from `project.md`'s parking lot; the stated stretch goal.*

~~The structure was paid for in advance in Section 4. This section spends it.~~
**Corrected 2026-09-03:** it was not. Section 4 shipped the WRITER stage as
three inline calls, and deferred the list/three-loop structure to here — see
Section 4's completion note. This section builds it *and* proves it with the
clock, which is more work than the line above promised.

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
