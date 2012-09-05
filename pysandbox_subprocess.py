#!/usr/bin/python
#
# File:   pysandbox_subprocess.py
# Date:   30-Aug-11
# Author: Adam Hartz <hartz@alum.mit.edu>


#-----------------------------------------------------------------------------
# Tutor2 function: run code in sandbox and return strings

import subprocess
import re
import resource
import os
import pyxserver_config

def mangle_code(code,argv):

    # mangle code to change os.getenv(foo) to ENV[foo]
    code = re.sub('os\.getenv\(([a-z0-9\'\"]+)\)','ENV[\\1]',code)
    code = re.sub("os\.fdopen\(3,'w'\)",'LOG_OUTPUT',code)

    # remove import os
    code = code.replace('import os','')

    # remove f.close()
    code = code.replace('f.close()','')

    # remove sys.exit(0)
    code = code.replace('sys.exit(0)','')

    # clean up CR's
    code = code.replace('\r','')
    

    # check for malicious statements
    x = code.replace(' ','')
    x = re.sub("os\.fdopen\(3,'w'\)",'LOG_OUTPUT',x)	# fdopen(3.. is ok

    if (x.count('/etc/passwd')
        or x.count('importsystem') 
        or x.count('sys.path') or x.count('tutor.tutor') or x.count('importtutor')
        or x.count('__builtin')):

        return code, False

    #head = "import sys\noldpath = sys.path\nsys.path = ['/usr/lib/python2.6','/home/tutor2/tutor/python_lib/lib601']\n\n"
    #head = "import sys\noldpath = sys.path\nsys.path = ['/usr/lib/python2.6', '%s']\n\n" % pyxserver_config.PYXSERVER_LIB_PATH
    head = "import sys\noldpath = sys.path\nsys.path = ['/usr/lib/python2.6', '/usr/lib/python2.6/dist-packages', '/usr/lib/python2.6/lib-dynload/','%s']\n\n" % pyxserver_config.PYXSERVER_LIB_PATH
    head += "from cStringIO import StringIO\nLOG_OUTPUT = StringIO()\n\n"
    head += "ENV = %s\n\n" % repr(argv)
    
    footer = "\n\nprint \"!LOGOUTPUT\"\n"
    footer += "print LOG_OUTPUT.getvalue()\n"
    code = head + code + footer
    return code, True

def setlimits():
    """
    Helper to set CPU time limit for check_code, so that infinite loops
    in submitted code get caught instead of running forever.
    """
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))

def sandbox_run_code(code,argv):
    """
    Run code, returning stdout, stderr, and output_log.

    argv should be a dict, giving the initial virtual environment.  We use it for
    passing argument valies, ie argv1, argv2, ... to the code being run

    """
    
    (code, code_ok) = mangle_code(code,argv)

    if not code_ok:
        return('','BAD CODE - this will be logged','')
    
    # mangle code to change os.getenv(foo) to ENV[foo]
    code = re.sub('os\.environ','ENV',code)
    code = re.sub('os\.getenv\(([a-z0-9\'\"]+)\)','ENV[\\1]',code)
    code = re.sub("os\.fdopen\(3,'w'\)",'LOG_OUTPUT',code)

    # remove import os
    code = code.replace('import os','')

    # remove f.close()
    code = code.replace('f.close()','')

    code = code.replace('\r','')
    
    
    python = subprocess.Popen(["python"],stdin = subprocess.PIPE,\
                                         stdout = subprocess.PIPE,\
                                         stderr = subprocess.PIPE,\
                                         preexec_fn = setlimits)
    output = python.communicate(code)
    
    out,err = output
    
    n = out.split("!LOGOUTPUT")
    
    if len(n) == 2: #should be this
        out,log = n
    elif len(n) == 1: #code didn't run to completion
        if err.strip() == "":
            err = "Your code did not run to completion, but no error message was returned."
            err += "\nThis normally means that your code contains an infinite loop or otherwise took too long to run."            
        log = ''
    else: #someone is trying to game the system
        out = ''
        log = ''
        err = "BAD CODE - this will be logged"
    if len(out) >= 10000:
       out = out[:10000]+"\n\n...OUTPUT TRUNCATED..."
    
    return out,err,log
