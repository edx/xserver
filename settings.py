# Not django (for now), but use the same settings format anyway

import json
import os
from .logsettings import get_logger_config
from path import Path
import sys

ROOT_PATH = Path(__file__).dirname()
REPO_PATH = ROOT_PATH
ENV_ROOT = REPO_PATH.dirname()

# DEFAULTS

DEBUG = False


LOGGING = get_logger_config(ENV_ROOT / "log",
                            logging_env="dev",
                            local_loglevel="DEBUG",
                            dev_env=True,
                            debug=True)

GRADER_ROOT = os.path.abspath(os.path.join(ENV_ROOT, 'data/6.00x/graders'))

# Dev setting.
DO_SANDBOXING = False

# AWS

if os.path.isfile(ENV_ROOT / "env.json"):
    print("Opening env.json file")
    with open(ENV_ROOT / "env.json") as env_file:
        ENV_TOKENS = json.load(env_file)

    # True by default!  Don't want messed up config to let students run regular python!
    DO_SANDBOXING = ENV_TOKENS.get('DO_SANDBOXING', True)


    LOG_DIR = ENV_TOKENS['LOG_DIR']
    local_loglevel = ENV_TOKENS.get('LOCAL_LOGLEVEL', 'INFO')
    LOGGING = get_logger_config(LOG_DIR,
                                logging_env=ENV_TOKENS['LOGGING_ENV'],
                                local_loglevel=local_loglevel,
                                debug=False)

    # Should be absolute path to 6.00 grader dir.
    # NOTE: This means we only get one version of 6.00 graders available--has to
    # be the same for internal and external class.  Not critical -- can always
    # use different grader file if want different problems.
    GRADER_ROOT = ENV_TOKENS.get('GRADER_ROOT')

    SANDBOX_PYTHON = ENV_TOKENS.get('SANDBOX_PYTHON', '/opt/edx/bin/sandbox-python')
