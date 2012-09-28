from settings import *

import json
from logsettings import get_logger_config

with open(ENV_ROOT / "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

RUN_URL = ENV_TOKENS['RUN_URL']

LOG_DIR = ENV_TOKENS['LOG_DIR']
local_loglevel = ENV_TOKENS.get('LOCAL_LOGLEVEL', 'INFO')
LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS['LOGGING_ENV'],
                            syslog_addr=(ENV_TOKENS['SYSLOG_SERVER'], 514),
                            local_loglevel=local_loglevel,
                            debug=False)
