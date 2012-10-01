# Not django (for now), but use the same settings format anyway

import json
import os
from logsettings import get_logger_config
from path import path
import sys

ROOT_PATH = path(__file__).dirname()
REPO_PATH = ROOT_PATH
ENV_ROOT = REPO_PATH.dirname()

# DEFAULTS

DEBUG = False

# Must end in '/'
RUN_URL = 'http://172.16.27.128:8080/'  # Victor's VM ...
RUN_URL = 'http://sandbox-runserver-001.m.edx.org:8080/'
RUN_URL = 'http://sandbox-runserver.elb.edx.org:80/'


LOGGING = get_logger_config(ENV_ROOT / "log",
                            logging_env="dev",
                            local_loglevel="DEBUG",
                            dev_env=True,
                            debug=True)

GRADER_ROOT = os.path.abspath(os.path.join(ENV_ROOT, 'data/6.00x/graders'))

# AWS

if os.path.isfile(ENV_ROOT / "env.json"):
    print "Opening env.json file"
    with open(ENV_ROOT / "env.json") as env_file:
        ENV_TOKENS = json.load(env_file)

    RUN_URL = ENV_TOKENS['RUN_URL']

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
