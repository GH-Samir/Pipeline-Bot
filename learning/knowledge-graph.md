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

### subprocess-exit-contract — `practicing`
`0` success · `1` herdr ran and the world said no (JSON `error` object) ·
`2` herdr never parsed the command — a bug in *your source* (**plain text, not
JSON**). Exit 1 is sometimes retryable; exit 2 never is.
> **2026-09-02:** Probed twice, including a concrete "what do you check first"
> framing. Answered "code 2 instead of 1", then "i dont know". Restated the
> premise without the reasoning. Fully taught by me; zero learner evidence.
> **2026-09-02 (Section 1.4):** Asked which status fits "ran outside Herdr",
> given herdr's 1-vs-2 split. Answered "1 since the code is working fine its
> just run in the wrong place, the wrong world" — correct, in own words, applied
> to a case never discussed. The gap from this morning is closing.
> Capped at `practicing`: introduced and demonstrated the same day.
> **2026-09-02 (Section 2.1):** Predicted `2` for `pane list` with no server;
> actual was `1`. Same distinction they had just argued correctly, inverted when
> the failure came from herdr rather than their own script. Not downgraded --
> the earlier evidence stands -- but the miss is worth a revisit in task 3.
> **2026-09-02 (Section 2.3):** Revisit done, and it settled. Asked to classify
> the misspelled `--untill` concretely: "bug" -- correct, unprompted. Then
> predicted `call("pane", "list")` with no server: "exit code 1, herdr world
> eroor" -- correct, and the inversion from task 2.1 did not recur. Held at
> `practicing` only because the ceiling rule forbids `understood` on a concept
> introduced the same day; this is the strongest evidence in the graph for it.

### herdr-wait-trap — `practicing`
`herdr wait` is not a command, but `herdr wait --help` **exits 0** printing root
help. `subprocess.run(..., check=True)` sails past it and returns help text as
data. Verified live 2026-09-02.
`depends-on:` [[subprocess-exit-contract]]

### json-response-shapes — `introduced`
Success `{"id":…,"result":{"type":…}}`; error `{"id":…,"error":{"code","message"}}`.
`pane split` → `result.pane.pane_id`; `agent get` → `result.agent.agent_status`;
`agent read` → `result.read.text`. `agent wait` returns a *wait_matched event*,
not an agent — re-read via `agent get` instead.
Two layers: the transport envelope (`id` + `result`, or `id` + `error`) and the
typed payload inside `result` (`type` names the kind, a sibling key holds the
thing). `call()` returns the whole envelope, so reads start `response["result"]`.
> **2026-09-02 (Section 3.1):** Ran `pane split` by hand and read the real
> reply. The key chain took three attempts: `["type"]["paneid"]`, then
> `["pane_info"]["PANE_ID"]`, then correct. Both misses were the same root
> confusion -- indexing with a *value* (`pane_info`) instead of a *key*
> (`pane`), plus exact-spelling drift. Landed only after being handed the
> literal key list at each level. Task 3.2 (the reclaim) is where this gets
> probed for real.

### pane-agent-primitives — `introduced`
`pane split` then `agent start` — a pane must already exist at a shell prompt;
`agent start` never creates layout.
> **2026-09-02 (Section 3.1):** Split a pane from the CLI and then from Python,
> and saw the empty shell prompt that `agent start` will later take over.
> `split_pane()` is the only function in the wrapper that creates layout.

### default-parameter-values — `introduced`
`def split_pane(direction="right")` — a parameter with a fallback, so callers
who don't care can omit it. Agent-written in the signature, explained at the
time.

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

### git-diff-tracked-vs-untracked — `understood`
`git diff` compares index against working tree. A brand-new **untracked** file
appears in neither, so it shows nothing — regardless of how many commits exist.
`git add -A` then `git diff --cached`.
> **2026-09-02:** Asked what the reviewer receives when the writer creates a new
> file in this zero-commit repo. Answered "nothing sinfe zero commits" — right
> outcome, wrong mechanism. Conflated untracked-ness with absence of history.
> Partial credit logged as partial.
> **2026-09-02:** self-reported prior knowledge.

### git-baseline-commit — `understood`
"What did the writer change?" is meaningless without a commit marking the state
*before* it ran. `git diff` is a functional component of this pipeline, not a
safety net.
`depends-on:` [[git-diff-tracked-vs-untracked]]
> **2026-09-02:** self-reported prior knowledge.

### git-basics — `understood`
`init`, `add`, `commit`, `log`, `status`. Repo is initialised; **zero commits.**
> **2026-09-02:** self-reported prior knowledge.

### gitignore-purpose — `understood`
`depends-on:` [[generated-vs-authored]]
> **2026-09-02:** self-reported prior knowledge.

### generated-vs-authored — `understood`
Which files you write and which a machine regenerates.

---

## Python
> **2026-09-02:** self-reported prior knowledge.

### custom-exceptions — `practicing`
Distinct exception types are how the exit contract becomes usable by callers.
A base class nobody raises (`HerdrError`) plus one sibling per failure kind, so
`except HerdrWorldError:` means "retry" and `except HerdrError:` means "either".
`depends-on:` [[subprocess-exit-contract]] [[class-definition]]
> **2026-09-02 (Section 2.2):** Hierarchy taught, then written by me at the
> learner's request ("do this for me i dont have time"). Trade named out loud.
> Two real misconceptions surfaced first and are worth re-probing in task 3:
> wrote `class HerdrWorldError(except HerdrUsageError):` (mixing the moment a
> class is *defined* with the moment it is *caught*), and `return exit(2)` in a
> class body (expecting the class itself to perform the exit). Asked what the
> parent should be, answered "i do not know" -- taught with the tree diagram.
> Zero learner code in this concept. Stays `introduced` on purpose.
> **2026-09-02 (Section 2.4):** Wrote the fourth type unaided --
> `class HerdrOutputError(HerdrError):` with a docstring, and spelled it
> identically in the `raise` two branches down. Exactly the work handed off in
> 2.2, done alone this time. Moves to `practicing`; the handoff is paid back.

### class-definition — `practicing`
`class Name(Parent):` creates a name, once, when Python reads the file. The
parentheses answer "what is this a kind of?", not "when do I catch it?". A body
of nothing but a docstring is a complete class -- these three run zero lines.
Classes are `CapWords`.
> **2026-09-02 (Section 2.2):** First class the learner has met. See the two
> misconceptions logged under [[custom-exceptions]]. Corrected the stray
> `except` themselves between saves; the parent name and the third class were
> supplied by me.
> **2026-09-02 (Section 2.3):** Asked which of the three names means "the typo
> is in our source" and answered "1" -- a digit, not a name. Exit codes and
> exception names were the same vocabulary in their head. Taught the split
> explicitly (numbers are herdr's language, names are ours; `call()` is the
> translator), after which the concrete classification came out right. This is
> the mapping to re-probe first next session.

### subprocess-module — `introduced`
`subprocess.run` takes an argv **list** (no shell, so no quoting or glob
surprises), `capture_output=True` returns output on the object, `text=True`
decodes to str, and `check` is left at its default `False` on purpose.
`depends-on:` [[herdr-wait-trap]]
> **2026-09-02 (Section 2.1):** Wrote `argv = ["herdr"] + list(args)` correctly
> and unaided. The `subprocess.run(...)` call took four attempts — first calling
> their own `run` recursively, then wrapping it in `str()`, then two stray-paren
> typos — and the final line was supplied by me after the third. Stays
> `introduced`: the argv half is theirs, the call half is not yet.

### completed-process-object — `introduced`
`subprocess.run` returns a `CompletedProcess` carrying `.returncode`, `.stdout`
and `.stderr`. Flattening it with `str()` throws the exit code away.
> Explained 2026-09-02 after `str(run(argv))` appeared in the fill-in.
> **Live finding (Section 2.1):** herdr writes *both* the JSON error object and
> plain-text usage errors to `.stderr`; `.stdout` is empty on failure.

### recursion-limit — `practicing`
A function that calls itself with no base case does not hang — Python caps call
depth (1000 here) and raises `RecursionError`.
> **2026-09-02 (Section 2.1):** Wrote `str(run(argv))` inside `run`, then
> predicted "infinite recursion" before it was run. Correct, and the guardrail
> detail was new.

### json-parsing-python — `introduced`
`json.loads` turns a JSON string into a Python dict. Handed something that is
not JSON it raises `JSONDecodeError` -- a traceback that blames the parser and
never mentions the misspelled flag that actually caused it. That misdirection is
why the exit-2 guard is checked first.
`depends-on:` [[json-response-shapes]] [[stdout-vs-stderr]]
> **2026-09-02 (Section 2.3):** Predicted that plain text reaching `json.loads`
> "would not even show that a bug has occured" -- the opposite of what happens.
> Ran it themselves and read the `JSONDecodeError`. The correction landed: the
> failure IS reported, it just names the wrong culprit. Wrote
> `json.loads(completed.stdout)` in the exit-0 branch, with the call itself
> scaffolded and only the stream left to choose -- so `introduced`, not more.

### try-except — `understood`
`try:` attempts the risky lines; `except SomeError:` runs instead if that
specific failure happens. Scope is the block -- lines outside `try` are not
covered, which is why guarding the exit-0 parse leaves exit 1 and 2 untouched.
> **2026-09-02:** self-reported prior knowledge ("i know how try except works
> from another projects"). Not taught from here.
> **2026-09-02 (Section 2.4):** Structure agent-written; filled the `raise`
> inside the `except` and correctly predicted the scoping -- consistent with
> the self-report.
> **Known gap, deliberately left:** the exit-1 branch calls
> `json.loads(completed.stderr)` outside any `try`. Non-JSON on a failing exit 1
> still crashes with a raw `JSONDecodeError`. Named out loud 2026-09-02; fix
> when it bites, or in Section 7 with the rest of the failure handling.

### f-strings-and-dict-indexing — `introduced`
`payload["error"]["code"]` walks a nested dict; `f"{x}: {y}"` builds a string
with values substituted in. Both agent-written in the exit-1 branch, explained
line by line at the time.
> **2026-09-02 (Section 2.3):** Copied the f-string into the `raise` blank as if
> it were the exception itself -- `raise f"{error['2']: ..."`. The misread was
> structural: an f-string is a *message*, and `raise Name(message)` needs a name
> in front of the parentheses. Worth re-checking when a string is next built.

### argv-and-cli-args — `seed`
Taking the task string as an argument.

### timeouts — `seed`
Every wait needs one. Covers the edge where an agent finishes before
`--until working` ever matches.
`depends-on:` [[submit-wait-race]]

### module-imports — `practicing`
Why `pipeline.py` importing `herdr_client` keeps subprocess calls in one file:
the transport can be swapped without `pipeline.py` noticing.
> **2026-09-02 (Phase 3):** Asked what survives swapping the CLI for the raw
> socket. Answered "would have to change to trust" — ambiguous; on a leading
> re-ask ("did you mean transport?") answered "yeah". Recognition, not recall —
> I supplied the word. Logged `introduced`, no credit claimed.
> **2026-09-02 (Section 2.5):** Wrote `import herdr_client` and used
> `herdr_client.call(...)` and `herdr_client.HerdrError` through the module
> prefix. One miss first: `herdr_client.herdr_env`, reaching for a local
> variable from `preflight()` as if it lived in the imported module. Corrected
> after being pointed at the four class names. The split is now real --
> `pipeline.py` contains no `subprocess` call and never mentions exit codes.

### language-choice-tradeoffs — `introduced`
Choosing a language by what the program spends its time doing. A program that
waits on other processes ~100% of the time gains nothing from a fast language.
> **2026-09-02 (Phase 3):** Learner asked, unprompted, "would it be better to
> write this in rust?" — a genuinely good instinct and the right question to
> ask about an inherited decision. Reasoning supplied by me. Rust logged as a
> real v3 option, not dismissed.

---

## Engineering practices (absent — curriculum too)

### version-control-discipline — `understood`
Committing as you go. **Zero commits exist.** Section 1.
> **2026-09-02:** self-reported prior knowledge.

### testing-absent — `seed`
No tests, no runner. Acute here: the signature failure is a green run that did
nothing.

### preflight-env-guard — `practicing`
Fail at step 0 before side effects. `HERDR_ENV=1` checks "am I inside a Herdr
pane" — a *different* question from `server_not_running`, and the one
`pane split` actually needs.
> **2026-09-02:** Asked where it fails without the guard. "i dont know."
> Taught, with the live error captured.
> **2026-09-02 (Section 1.4):** Wrote the guard in `pipeline.py` themselves.
> Verified against herdr's own documented check `test "${HERDR_ENV:-}" = 1`.
> Correctly tests the *value* `"1"`, so `HERDR_ENV=0` is rejected too.

### env-vars — `introduced`
Reading environment variables and why config arrives that way. `os.environ` is
a dict of the variables the process was handed; names are case-sensitive and
conventionally UPPER_SNAKE. Herdr sets `HERDR_ENV`, `HERDR_PANE_ID`,
`HERDR_TAB_ID`, `HERDR_WORKSPACE_ID`.
> **2026-09-02 (Section 1.4):** Wrote `os.environ.get("0")` — looked up a
> variable named `0` rather than `HERDR_ENV`, so the guard refused even inside
> Herdr. Found it via a failed prediction, not by being told. Second attempt
> `herdr-env` (lowercase, hyphen) needed the case/underscore convention
> supplied. The lookup-by-name mechanic took two corrections — stays
> `introduced`.

### stdout-vs-stderr — `practicing`
Two output streams: stdout carries the program's real output, stderr carries
messages *about* the run. Keeps diagnostics out of a redirected PASS/FAIL summary.
> **2026-09-02 (Section 1.4):** Used `file=sys.stderr` correctly, unprompted,
> in the fill-in.
> **2026-09-02 (Section 2.5):** Hit stream buffering live -- the stderr
> diagnostic printed before the stdout status line, because stdout is block
> -buffered when captured to a pipe and stderr never is. Explained by me, not
> retrieved; worth a re-probe when output ordering next matters.

### exit-status-produced — `practicing`
The mirror of reading exit codes: `sys.exit(n)` sets what your process reports.
0 = success, nonzero = failure.
`depends-on:` [[subprocess-exit-contract]]
> **2026-09-02 (Section 1.4):** Wrote `sys.exit(1)` and defended the choice of
> 1 over 2 on the right grounds.
> **2026-09-02 (Section 2.5):** Filled `sys.exit(1)` in the failure handler
> without hesitating or asking. Routine now.

### main-guard — `introduced`
`if __name__ == "__main__":` — run this only when the file is executed directly,
not when it is imported. Keeps `pipeline.py` from firing a preflight on import.
> Agent-written in the skeleton and explained; not yet demonstrated.

### shell-exit-status — `introduced`
`$?` holds the exit status of the previous command **in that same shell**. A
fresh shell reports 0 regardless of what happened elsewhere.
> **2026-09-02 (Section 1.4):** Hit this live — `echo $?` in a separate `!`
> command returned 0 while the script had exited 1. My dictation caused it;
> corrected by joining the commands with `;`.
