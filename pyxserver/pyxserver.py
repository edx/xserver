#!/usr/bin/python
#
# File:   pyxserver.py
# Date:   03-Jan-12
# Author: I. Chuang <ichuang@mit.edu>
#
# External response mechanism executable for checking of 6.01 python code problems.

import os, sys, string, re
import json
import string,cgi,time
import urllib
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import pysandbox
from lxml import etree

#-----------------------------------------------------------------------------
# debugging

LOGFILE = "pyxserver.log"
PIDFILE = "pyxserver.pid"

open(PIDFILE,'w').write(str(os.getpid()))

def LOG(x):
    fp = open(LOGFILE,'a')
    if type(x)==dict:
        for k in x:
            if not k:
                continue
            s = '  %s : %s' % (k,x[k])
            fp.write(s)
            print s
    #if type(x)==type('str'):
    else:
        fp.write(x)
        fp.write('\n')
        print x

    fp.close()

#-----------------------------------------------------------------------------
# run code

def run_code_sandbox(processor,code,tests,getans=False):
    """
    Run code using pysandbox from Tutor2.

    Arguments:
        
        processor = string, with python definitions for answer, preamble, test_program
        code      = student response code
        tests     = string specifying tests (see pysandbox.py)
        
    Returns:
        
        award, message

    """

    # build processor environment
    # exec(pcode,globals(),penv) # evaluate code given in template, with its own local frame

    g = globals()
    penv = {}
    penv['__builtins__'] = g['__builtins__']

    try:
        exec(processor,penv,penv) # evaluate code given in template, with its own local frame
    except Exception,err:
        LOG('processor = %s' % processor)
        s = "<br/><font color='red'>Errror in problem code: %s</font>" % str(err).replace('<','&lt;')
        s += "<br/><font color='red'>Please see staff</font>"
        return 'WRONG_FORMAT', s

    if getans:
        try:
            ans = penv['answer']
            anshtml = '<font color="blue"><span class="code-answer"><br/><pre>%s</pre><br/></span></font>' % ans.replace('<','&lt;')
            return anshtml,"got answer"
        except Exception,err:
            return "","<font color='red'>Failed to get expected answer!</font>"

    context = {'aboxname': 'loncapa',
               'processor_env' : penv,
               #'is_admin' : True,
               'is_admin' : False,
               }

    (check_ok, html, ntests_passed, error_line_numbers) = pysandbox.check(context,code,tests)
    if check_ok:
        return 'EXACT_ANS', html
        #pass

    return 'WRONG_FORMAT', html

#-----------------------------------------------------------------------------

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type',	'text/html\n')
        self.end_headers()
        self.wfile.write("hey, today is the" + str(time.localtime()[7]))
	#self.send_error(404,'File Not Found: %s' % self.path)
        return

    def do_xserver_response(self,award,message):

        if 1:
            self.wfile.write("<edxgrade>");
            self.wfile.write('<awarddetail>%s</awarddetail>' % award);
            #self.wfile.write('<message>%s</message>' % message);
            self.wfile.write('<message><![CDATA[%s]]></message>' % message);
            self.wfile.write('<awarded></awarded>');
            self.wfile.write('</edxgrade>');

    def do_POST(self):

        print "in POST"
        if 1:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            #if ctype == 'multipart/form-data':
            #    query=cgi.parse_multipart(self.rfile, pdict)
            length = int(self.headers.getheader('content-length'))
            if ctype == 'application/x-www-form-urlencoded':
                qs = self.rfile.read(length)
                self.body = cgi.parse_qs(qs, keep_blank_values=1)
                            
            LOG('-----------------------------------------------------------------------------')
            LOG('connect at %s' % time.ctime(time.time()))
            LOG(self.body)

            self.send_response(200)
            self.send_header('Content-type',	'text/html\n')
            self.end_headers()

            #self.do_xserver_response('WRONG_FORMAT',urllib.quote(repr(self.body)))
            #self.do_xserver_response('WRONG_FORMAT',urllib.quote(repr(self.headers.getheader('content-type'))))
            #self.do_xserver_response('WRONG_FORMAT',urllib.quote(repr(dir(self.headers))))
            #self.do_xserver_response('WRONG_FORMAT',urllib.quote(repr(self.path)))
            #return

            pdict = self.body
            
            cmd = str(pdict.get('edX_cmd','')[0]).strip()
            tests = pdict['edX_tests'][0]
            processor = pdict['processor'][0].strip()
            if 'edX_student_response' in pdict:
                student_response = json.loads(pdict['edX_student_response'][0])[0]

            LOG('cmd = %s' % cmd)
            LOG('tests = %s' % tests)

            if cmd=='get_score':

                LOG('doing get_score')
                award, message = run_code_sandbox(processor,student_response,tests)
                LOG('message = %s' % message)
                self.do_xserver_response(award,message)

            elif cmd=='get_answers':

                LOG('doing get_answers')
                expected, message = run_code_sandbox(processor,"",tests,getans=True)
                LOG('message = %s' % message)
                self.wfile.write("<edxgrade>");
                self.wfile.write('<message><![CDATA[%s]]></message>' % message);
                self.wfile.write('<expected><![CDATA[%s]]></expected>' % json.dumps([expected]));
                self.wfile.write('</edxgrade>');
            
        if 0:
            print "err: ", err
            self.do_xserver_response('WRONG_FORMAT',err)

def main():
    try:
        server = HTTPServer(('', 8889), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()



