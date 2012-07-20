#
# Configuration file for pyxserver
#

import socket

if 'eecs1' in socket.gethostname():
    PYXSERVER_PORT = 8889
else:    
    PYXSERVER_PORT = 80

PYXSERVER_LIB_PATH = '../python_lib'
