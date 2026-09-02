# Knowledge graph — Pipeline Bot

Last updated: 2026-09-02

Statuses: `seed` → `introduced` → `practicing` → `understood`

- `seed` — named, never discussed. The honest default.
- `introduced` — explained *to* the learner; not yet demonstrated *by* them.
- `practicing` — the learner reasoned it out in their own words, or has used it.
- `understood` — demonstrated in working code they wrote.

**Evidence rule:** status moves only on what the learner demonstrated in
conversation. Not on self-report, not on having read it, not on it appearing in
`project.md`.

**Session note (2026-09-02):** six probes run. Two clean correct answers, one
partial, two honest "I don't know"s, one taught. Nothing here reached
`understood`, because no code has been written yet — that is expected at this
stage, not a deficit. Everything below marked `practicing` was demonstrated
**verbally only** and should be re-confirmed the first time it appears in code.

---

## Orchestration mechanics

### fan-out-serialisation — `practicing`
Why a stage runs spawn-all → submit-all → wait-all as three separate loops, and
not one loop per agent.
`depends-on:` [[stage-abstraction]]
> **2026-09-02:** Asked what a reviewer costs by folding the three loops into
> one, with 3 writers and no errors. Answered "the same as one agent would've" —
> correct, unprompted: the fan-out still happens but stops being parallel, so 3
> writers cost 3× wall-clock. Also grasped that the only symptom is the clock.

### submit-wait-race — `practicing`
`agent wait` matches *current* state, so waiting immediately after `prompt`
matches the pre-prompt settled state. Fix is to wait for the transition into
`working` first, then wait for settle.
`depends-on:` [[agent-lifecycle-states]]
> **2026-09-02:** Asked what a wait firing inside the 200ms startup window sees.
> Answered "idle" — correct state identification. The consequence chain (empty
> diff → reviewer fed nothing → false PASS) was supplied by me, not retrieved.
> Re-check the consequence half when this gets written.

### stale-artifact-reporting — `practicing`
A file on disk is not evidence that *this run* produced it. Two defences:
clear outputs at startup, and check agent state before trusting any file.
`depends-on:` [[agent-lifecycle-states]] [[filesystem-handoff]]
> **2026-09-02:** Asked what consolidate prints when run 2's writer blocks
> without writing. Answered "pass since its still on the previous files, it can
> pass things without even running the tests on them, thats why its dangerous."
> Correct mechanism *and* correct danger, in own words. Strongest answer of the
> session. Did not separate the two defences — that half was taught.

### stage-abstraction — `seed`
A stage takes a *list* of agents even when there is one, and runs three phases
over it. Paying for the parallel stretch goal in advance.

### agent-lifecycle-states — `introduced`
`idle` `working` `blocked` `done` `unknown`. `idle` requires the tab to have
been *seen* in a focused UI, so background panes settle as `done` — hardcoding
`--until idle` hangs forever. `blocked` is an approval dialog. `unknown` is not
a synonym for finished. `agent wait` with no `--until` matches idle|done|blocked.
> **2026-09-02:** Named `idle` correctly in the race probe. The seen-in-UI
> mechanism and the `done` default were supplied by me.

### resource-cleanup — `seed`
Close only the panes we created; never tear down panes we merely found.

### parallelism-vs-concurrency — `seed`
Underpins the fan-out. Not yet discussed.

---

## The tool boundary (herdr)

### subprocess-exit-contract — `introduced`
`0` success · `1` herdr ran and the world said no (JSON `error` object) ·
`2` herdr never parsed the command — a bug in *your source* (**plain text, not
JSON**). Exit 1 is sometimes retryable; exit 2 never is.
> **2026-09-02:** Probed twice, including a concrete "what do you check first"
> framing. Answered "code 2 instead of 1", then "i dont know". Restated the
> premise without the reasoning. Fully taught by me; zero learner evidence.
> **Highest-value reclaim target in this graph** — everything else sits on it.

### herdr-wait-trap — `introduced`
`herdr wait` is not a command, but `herdr wait --help` **exits 0** printing root
help. `subprocess.run(..., check=True)` sails past it and returns help text as
data. Verified live 2026-09-02.
`depends-on:` [[subprocess-exit-contract]]

### json-response-shapes — `seed`
Success `{"id":…,"result":{"type":…}}`; error `{"id":…,"error":{"code","message"}}`.
`pane split` → `result.pane.pane_id`; `agent get` → `result.agent.agent_status`;
`agent read` → `result.read.text`. `agent wait` returns a *wait_matched event*,
not an agent — re-read via `agent get` instead.

### pane-agent-primitives — `seed`
`pane split` then `agent start` — a pane must already exist at a shell prompt;
`agent start` never creates layout.

### herdr-protocol-version — `introduced`
Protocol 20 on herdr 0.8.2. Verified live, twice. The brief's "16 → 17" was wrong.

### alternate-screen-constraint — `seed`
Agents render on the terminal's alternate screen; rows leaving it never enter
scrollback, so no `--lines` value recovers a long transcript. **This is the
justification for the entire filesystem-handoff design and it has NOT been
re-verified** — it comes from `project.md`, not from a live test.
> Flagged 2026-09-02 as the one load-bearing claim still resting on a note.

### filesystem-handoff — `seed`
Herdr sequences the agents; the filesystem carries the data. Nothing parses a
transcript.
`depends-on:` [[alternate-screen-constraint]]

---

## Git

### git-diff-tracked-vs-untracked — `introduced`
`git diff` compares index against working tree. A brand-new **untracked** file
appears in neither, so it shows nothing — regardless of how many commits exist.
`git add -A` then `git diff --cached`.
> **2026-09-02:** Asked what the reviewer receives when the writer creates a new
> file in this zero-commit repo. Answered "nothing sinfe zero commits" — right
> outcome, wrong mechanism. Conflated untracked-ness with absence of history.
> Partial credit logged as partial.

### git-baseline-commit — `introduced`
"What did the writer change?" is meaningless without a commit marking the state
*before* it ran. `git diff` is a functional component of this pipeline, not a
safety net.
`depends-on:` [[git-diff-tracked-vs-untracked]]

### git-basics — `seed`
`init`, `add`, `commit`, `log`, `status`. Repo is initialised; **zero commits.**

### gitignore-purpose — `seed`
`depends-on:` [[generated-vs-authored]]

### generated-vs-authored — `seed`
Which files you write and which a machine regenerates.

---

## Python

### custom-exceptions — `seed`
Distinct exception types are how the exit contract becomes usable by callers.
`depends-on:` [[subprocess-exit-contract]]

### subprocess-module — `seed`
`run`, `capture_output`, `returncode`, and why `check=True` is the wrong default
here.
`depends-on:` [[herdr-wait-trap]]

### json-parsing-python — `seed`
`json.loads`, and why it must not run on an exit-2 response.
`depends-on:` [[json-response-shapes]]

### argv-and-cli-args — `seed`
Taking the task string as an argument.

### timeouts — `seed`
Every wait needs one. Covers the edge where an agent finishes before
`--until working` ever matches.
`depends-on:` [[submit-wait-race]]

### module-imports — `introduced`
Why `pipeline.py` importing `herdr_client` keeps subprocess calls in one file:
the transport can be swapped without `pipeline.py` noticing.
> **2026-09-02 (Phase 3):** Asked what survives swapping the CLI for the raw
> socket. Answered "would have to change to trust" — ambiguous; on a leading
> re-ask ("did you mean transport?") answered "yeah". Recognition, not recall —
> I supplied the word. Logged `introduced`, no credit claimed.
> Revisit in Section 2, where the split is actually built.

### language-choice-tradeoffs — `introduced`
Choosing a language by what the program spends its time doing. A program that
waits on other processes ~100% of the time gains nothing from a fast language.
> **2026-09-02 (Phase 3):** Learner asked, unprompted, "would it be better to
> write this in rust?" — a genuinely good instinct and the right question to
> ask about an inherited decision. Reasoning supplied by me. Rust logged as a
> real v3 option, not dismissed.

---

## Engineering practices (absent — curriculum too)

### version-control-discipline — `seed`
Committing as you go. **Zero commits exist.** Section 1.

### testing-absent — `seed`
No tests, no runner. Acute here: the signature failure is a green run that did
nothing.

### preflight-env-guard — `introduced`
Fail at step 0 before side effects. `HERDR_ENV=1` checks "am I inside a Herdr
pane" — a *different* question from `server_not_running`, and the one
`pane split` actually needs.
> **2026-09-02:** Asked where it fails without the guard. "i dont know."
> Taught, with the live error captured. No learner evidence.

### env-vars — `seed`
Reading environment variables and why config arrives that way.
