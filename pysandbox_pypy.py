#!/usr/bin/python
#
# File:   pysandbox_pypy.py
# Date:   01-Aug-11
# Author: I. Chuang <ichuang@mit.edu>
#

"""
Run sandboxed python process, using pypy.

This sub-module is imported into pysandbox.

Provides:

 - B{sandbox_run_code}: runs code in sandbox, returning stdout, sterrr, and output_log
 - B{DjangoSandbox}: class encapsulating the PyPySandbox procesor, with overloaded method to provide capture of output to fd=3

G{importgraph}

"""

import os, sys, string, re
import socket


#-----------------------------------------------------------------------------
# pypy / pysandbox setup

#sys.path.append('/home/tutor2/pypy-trunk')
#SANDBOX_BIN = '/home/ike/class/tutor-py/pypy-c-sandbox'

hn = socket.gethostname().lower()
if ('sicp' in hn) or ('zion' in hn):
    sys.path.append('/home/tutor2/pypy-1.5-src')
    SANDBOX_BIN = '/home/tutor2/bin/pypy-sandbox'
else:
    sys.path.append('/local/tutor2/pypy-1.5-src')
    SANDBOX_BIN = '/local/tutor2/bin/pypy-sandbox-osx'

#from pypy.translator.sandbox.sandlib import SandboxedProc
#from pypy_interact import PyPySandboxedProc

from pypy.translator.sandbox.pypy_interact import PyPySandboxedProc
from cStringIO import StringIO

#-----------------------------------------------------------------------------
# class for sandboxed process

class DjangoSandbox(PyPySandboxedProc):
    """
    Class for running python in a sandbox, courtesy of pypy.

    The os.write() hook is overloaded to provide capture of output which is sent
    to fd=3 (and fd=4) by the code being tested.

    """

    output_log = ""
    secondary_log = ""
    virtual_env = {'foo': 'bar'}
    debug = False

    def __init__(self, code):
        super(DjangoSandbox, self).__init__(SANDBOX_BIN, ['-c', code])

    # patch os.write to include fd=3 and fd=4 as outputs
    def do_ll_os__ll_os_write(self, fd, data):
        if fd==3:
            # print "logit: s=",data
            self.output_log += data
            return len(data)
        if fd==4:
            self.secondary_log += data
            return len(data)
        return super(DjangoSandbox, self).do_ll_os__ll_os_write(fd,data)

    # 19-Jul-11 ichuang: also patch get_file
    virtual_fd_range = range(5, 50)
    def get_file(self,fd):
        if fd in [3,4]:
            return fd
        else:
            return super(DjangoSandbox,self).get_file(fd)

#-----------------------------------------------------------------------------
# Tutor2 function: run code in sandbox and return strings

def sandbox_run_code(code,argv):
    """
    Run code in sandbox, returning stdout, stderr, and output_log.

    argv should be a dict, giving the initial virtual environment.  We use it for
    passing argument valies, ie argv1, argv2, ... to the code being run

    """
    code_output = StringIO()
    code_err = StringIO()

    #print "running this code:"
    #print code

    code = "import os\n" + code		# need os.getenv ...
    
    sandproc = DjangoSandbox(code)
    sandproc.virtual_env = argv

    sandproc.interact(stdout=code_output, stderr=code_err)
    sandproc.kill()

    # 19jul11 ichuang
    ce = code_err.getvalue()
    if ce.count('[Subprocess killed by SIGIOT]'):
        ce = ce.replace('[Subprocess killed by SIGIOT]','')
        ce = ce.strip()

    #return(code_output.getvalue(), code_err.getvalue(), sandproc.output_log)
    return(code_output.getvalue(), ce, sandproc.output_log)
