xserver
=======

XServer accepts student code submissions from the LMS and runs the code
using courseware graders.  This repo does not include the grader code.

The repo currently contains some scripts used for manual testing in
`tests/test.py`.  These should be run AFTER setting up a sandbox
environment (see `AppArmor.md` for details).

**Warning**: Do NOT run `nosetests` within the `xserver` directory. 
The `tests` and `evil_tests` directories contain scripts that go into
infinite loops to test sandboxing.  `nosetests` will run these while
looking for test cases.
