"""Task 3/5's stopwatch: puts a real number on the folded (serial) stage,
so [[fan-out-serialisation]] rests on a clock instead of just reasoning."""

import time
import pipeline

TASKS = [
    "write is_even.py that checks if a number is even",
    "write is_odd.py that checks if a number is odd",
    "write is_positive.py that checks if a number is positive",
]

panes_opened = []

start = time.monotonic()

results = pipeline.run_writer_stage_serial(TASKS, panes_opened)

elapsed = time.monotonic() - start

for pane_id, settled in results:
    print(pane_id, settled["agent"]["agent_status"])

print(f"serial: {elapsed:.1f}s for {len(TASKS)} writers")

for pane in panes_opened:
    pipeline.herdr_client.close_pane(pane)

panes_opened_parallel = []

start = time.monotonic()

results = pipeline.run_writer_stage(TASKS, panes_opened_parallel)

elapsed = time.monotonic() - start

for pane_id, settled in results:
    print(pane_id, settled["agent"]["agent_status"])

print(f"parallel: {elapsed:.1f}s for {len(TASKS)} writers")

for pane in panes_opened_parallel:
    pipeline.herdr_client.close_pane(pane)
