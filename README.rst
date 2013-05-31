Part of `edX code`__.

__ http://code.edx.org/

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

License
-------

The code in this repository is licensed under version 3 of the AGPL unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How to Contribute
-----------------

Contributions are very welcome. The easiest way is to fork this repo, and then
make a pull request from your fork. The first time you make a pull request, you
may be asked to sign a Contributor Agreement.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org

Mailing List and IRC Channel
----------------------------

You can discuss this code on the `edx-code Google Group`__ or in the
``edx-code`` IRC channel on Freenode.

__ https://groups.google.com/forum/#!forum/edx-code
