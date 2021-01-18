"""
Setup for apparmor-based sandbox.
"""

import logging

import settings

log = logging.getLogger(__name__)

def record_suspicious_submission(msg, code_str):
    """
    Record a suspicious submission:

    TODO: upload to edx-studentcode-suspicious bucket on S3.  For now, just
    logging to avoids need for more config changes (S3 credentials, python
    requirements).
    """
    log.warning(f'Suspicious code: {msg}, {code_str}')

def sandbox_cmd_list():
    """
    Return a command to use to run a python script in a sandboxed env.

    NOTE: this is kind of ugly--we should really have all copy-to-tmp dir and
    run logic here too, but then we'd have to duplicate it for testing in the
    content repo.
    """
    if settings.DO_SANDBOXING:
        return ['sudo', '-u', 'sandbox', settings.SANDBOX_PYTHON]
    else:
        return ['python']
