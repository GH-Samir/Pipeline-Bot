"""The first automated test: proves a blocked writer produces FAIL, not PASS."""

import pipeline

# assert checks a condition and raises AssertionError -- which crashes the
# script with a nonzero exit code -- if it's False. No human has to read this
# and judge it; the exit code is the verdict.
assert pipeline.check_writer_status("blocked") == False

# The opposite case: a writer that settled "idle" should be trusted.
assert pipeline.check_writer_status("idle") == True

print("all tests passed")
