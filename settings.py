# Not django (for now), but use the same settings format anyway

import os
from logsettings import get_logger_config
from path import path

ROOT_PATH = path(__file__).dirname()
REPO_PATH = ROOT_PATH
ENV_ROOT = REPO_PATH.dirname()

# DEFAULTS

DEBUG = False

# Must end in '/'
RUN_URL = 'http://172.16.27.128:8080/'  # Victor's VM ...
RUN_URL = 'http://sandbox-runserver-001.m.edx.org:8080/'

LOGGING = get_logger_config(ENV_ROOT / "log",
                            logging_env="dev",
                            local_loglevel="DEBUG",
                            dev_env=True,
                            debug=True)


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


print "LOGGING is ", LOGGING
