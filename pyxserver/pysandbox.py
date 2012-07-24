#!/usr/bin/python
#
# File:   pysandbox.py
# Date:   17-May-10
# Author: I. Chuang <ichuang@mit.edu>
#
# 01-Aug-11 ichuang: this module is now fairly generic; it can use one of several
#                    other different sub-modules to actually run the code, using
#                    either pypy, or a sandbox over sockets, or no sandbox at all.
#
# 04-Feb-12 ichuang: version for pyloncapa

"""
Run sandboxed python process, using to check tutor code (student and expected)

Provides:

 - B{check(context,code,tests)}: runs code using sandbox_run_code and returns HTML output 
 - B{mangle_tutor1_python}: fix tutor1 python testing code to work with sandbox (no files, sys.argv)

Not yet done: no lib601 in sandbox

G{importgraph}

"""

import os, sys, string, re, time
import socket
import random
import traceback

import showhide
from util import *
from style_guide import check_static_style_guide

#-----------------------------------------------------------------------------
# import one sanbox python sub-module

#from pysandbox_pypy import sandbox_run_code
from pysandbox_subprocess import sandbox_run_code	# adam hartz's module

#-----------------------------------------------------------------------------
# Tutor2 function

def mangle_tutor1_python(code):
    """
    mangle python code (fix tutor1 python testing code)
    
    The TUT description of a problem may take an input which describes which test
    to perform.  This is typically something like "test = sys.argv[2]".  We 
    rewrite that as "test = os.getenv('argv2')".  The test code also writes
    its output to a specific place.  In the scheme code, this was to a named
    file, where the filename was specified by an argument to the code.  In the
    auto-translated python code, this is typically "open(sys.argv[3],'w')".
    We rewrite this as a "os.fdopen(3,'w')", where fd=3 is a special device
    captured by the sandbox into an output stream.

    Note that the old scheme code had an inconsistency about which argument was
    used for the test description, and which for the output file.  Thus, in the
    rewriting, we map both "open(sys.argv[2],'w')" and "open(sys.argv[3],'w')" 
    to "os.fdopen(3,'w')" and then turn all other requests for sys.argv[2] and
    sys.argv[1] to os.getenv('argv2').

    """

    # replace open(sys.argv[3],'w') with os.fdopen(3,'w')
    # this is because in a pypy sandbox, we can't write to files.
    # instead, we have a special version of the function do_ll_os__ll_os_write
    # defined to hard-code fd=3 as our log file

    code = code.replace("open(sys.argv[3],'w')","os.fdopen(3,'w')")
    code = code.replace("open(sys.argv[2],'w')","os.fdopen(3,'w')")

    # replace sys.argv[2] with os.getenv('argv2')
    # we then place argv2 as a key/value in the sandproc.virtual_env dict

    code = code.replace("sys.argv[2]","os.getenv('argv2')")
    code = code.replace("sys.argv[1]","os.getenv('argv1')")

    return code

#-----------------------------------------------------------------------------
# Tutor2 function: check if code has been run before, and return if so, else run
#
# NOT USED YET (01aug11)

def sandbox_run_code_cached(code,argv):
    """
    Check if code + argv (minus rndlist) has been run before, by looking up
    hash value in database table.  If so, return result from previous run.
    Else run the code, and save the result in the database table.
    """

    # use hashlib, pickle

    return sandbox_run_code(code,argv)

#-----------------------------------------------------------------------------
# input-check function processing

def do_input_check(penv,code_provided):
    """
    run the input_check function if it exists in the processor environment
    this is used, for example, to check if the code provided has a specific string, 
    or if the code provided does recursion (or not).
    
    input_check should be defined as a function, which accepts a single argument,
    which is the code provided by the student.  It should return False if the input
    is ok, and some comment string otherwise.  For example:
    
    def input_check(code):
        if code.count('elif'):
            return False	# contains elif, so is OK
        return 'Code should include "elif"'

    """
    (isok,msg) = code_has_suspicious_statements(code_provided)
    if not isok:
        return msg

    # the style check is only done if DO_STYLE_CHECK is defined in the script
    if 'DO_STYLE_CHECK' in penv:
        try:
            msg = check_static_style_guide(code_provided)
            if msg:
                return msg
        except Exception as err:
            if 1: 	# TODO: make this 'DEBUG' in penv:
                msg = "Oops, our code inspector failed in check_static_style_guide! Error:"
                msg += "<pre>%s</pre>" % str(err).replace('<','&lt;')
                msg += "Traceback: <pre>%s</pre>" % traceback.format_exc().replace('<','&lt;')
                return msg

    if penv.has_key('input_check'):
        incheck = penv['input_check']
        if (incheck == None):
            return False	# code is OK
        return incheck(code_provided)
    return False	# code is OK

#-----------------------------------------------------------------------------
# check for potentially malicious statements in the code

def code_has_suspicious_statements(code):

    # check for malicious statements
    x = code.replace(' ','')
    x = re.sub("os\.fdopen\(3,'w'\)",'log_output',x)	# fdopen(3.. is ok

    if (x.count('importos') or x.count('fromosimport') or x.count('/etc/passwd')
        or x.count('importsystem') or x.count('file') or x.count('open(')
        or x.count('sys.path') or x.count('tutor.tutor') or x.count('importtutor')
        or x.count('__builtin') or x.count('exec(')):
        return False, "Code is suspicious.  This will be logged.  Not testing." 
    return True, ""

#-----------------------------------------------------------------------------
# output-check function processing

def do_output_check(penv,student_output,expected_output):
    """
    Compare student output with expected answer output.

    If "output_check" is defined in the {% processor %} environment, then call
    that function to produce the comparison output.  Otherwise, just use
    an equality test.  The output_check function takes as arguments two strings,
    student_output, expected_output, and should return True if ok, and either
    a string or False otherwise.
    
    Example:
    
    def output_check(student_output, expected_output):
        if (student_output==expected_output):
            return True
        return 'Wrong answer'

    """
    if penv.has_key('output_check'):
        ocheck = penv['output_check']
        try:
            return ocheck(student_output, expected_output)
        except:
            return "Oops, output_check function failed!  The output from your code is likely wrong."
        
    return (student_output==expected_output)

#-----------------------------------------------------------------------------
# construct a string of HTML containing some debug information about code checking

def debug_code_checking(context,code_expected,code_provided,tests,testlist):
    s = ''
    myname = context['aboxname']	# name of this answer box 
    s += showhide.start(myname) 
    s += '<b>Debug info:</b>'
    #s += "<li>code_expected = <blockquote><pre>%s</pre></blockquote>" % code_expected
    s += showhide.link(myname) + showhide.content(myname)
    s += "<li>code_provided = <blockquote><pre>%s</pre></blockquote>" % code_provided.replace('&','&amp;').replace('<','&lt;')
    s += "<li>tests = %s" % tests
    s += "<li>testlist = %s" % repr(testlist)
    s += '<hr/>'
    s += showhide.end(myname)
    return s

#-----------------------------------------------------------------------------
# Tutor2 function: import code fragment from DB

def ImportTUTCode(code):
    """
    If the preamble includes any "include tutcode.foo" lines then retrieve the
    code fragment "foo" from the TUTcode database table.
    """
    return code
    #m = re.search('#include tutcode.([^ \n\r]+)',code)
    #if m:
    #    tcname = m.group(1).strip()
    #    # looup the code in the db
    #    try:
    #        tcode = models.TUTcode.objects.get(name=tcname).code
    #        tcode = tcode.replace('\r','')
    #    except (models.TUTcode.DoesNotExist):
    #        tcode = "# Failed to #inlcude %s !!!" % tcname
    #    # replace #include tutcode.foo with code from db
    #    ncode = re.sub('#include tutcode.%s' % tcname,tcode,code)
    #    return ncode
    #return code

#-----------------------------------------------------------------------------
# Tutor2 function: assemble student code and test code

def AssembleCode(penv,student_code_fragment,answer_select=None):
    """
    Assemble student code and test code fragments into full test code programs.
    Returns code_expected and code_provided, to be run in the sandbox.  Also returns
    initial_code (to check if the student's code has changed from it).

    If multiple expected answers are provided, then answer_select selects which one to use.
    """

    #preamble = penv['preamble'] + "import os\n"
    preamble = penv['preamble']
    expected = penv['answer']
    initial_code = penv['initial_display']	# code provided for students as a start stub
    tprog = penv['test_program']

    if type(expected)==list:	# if multiple answers provided, use first for checking
        if answer_select:
            expected = expected[answer_select]	# choose the one selected
        else:
            expected = expected[0]	# default to first

    code_expected = mangle_tutor1_python(ImportTUTCode(preamble + expected + tprog))
    code_provided = mangle_tutor1_python(ImportTUTCode(preamble + student_code_fragment + tprog))
    
    return code_expected, code_provided, initial_code 

#-----------------------------------------------------------------------------
# Tutor2 function to turn string of tests to list of tests

def TestStringToTestList(tests):
    """
    Turn a string description of tests to a list of tests.  The string
    is expected to be a comma seprated list, which may have a "repeat:XX"
    term.  If any term is "repeat:XX" then replace the next term by 
    XX times repetition of that term.
    """
    testlist = tests.split(',')
    ntl = []
    while len(testlist):
        tt = testlist.pop(0)	# get first element
        m = re.match('repeat:([0-9]+)',tt)	# if this is repeat:XX then repeat next
        if m:
            reptest = [testlist.pop(0)] *int(m.group(1))	# pop next and repeat
            ntl += reptest
        else:
            ntl += [tt]		# else add to new testlist
    testlist = ntl
    return testlist

#-----------------------------------------------------------------------------
# Tutor2 function to check python code

def check(context,code,tests,dosubmit=False,answer_select=None):
    """
    Main Tutor2 function to check python code, against expected results, using
    the pypy sandbox.

    Produces HTML output, depending on whether we're just checking or doing a submit.

    This is called by functions in templatetags/tut.py when a TUT problem template is rendered.

    context - dict of state of ABox and node being rendered, including processor code for checking
    code - student's code to be checked (ie run in the sandbox)
    tests - string of tests, specified in the TUT problem description (given in the abox args)
    dosubmit - flag, if true, will display expected answer
    answer_select - index into answer[] which is used if penv['answer'] is a list with length > 1

    returns (check_ok, html, ntests_passed, error_line_numbers)

    When penv['answer'] is a list with length>1, then if answer_select is unspecified,
    this function calls itself for each of the expected answers provided, and returns check_ok
    if any of the check_ok = True.  Otherwise, it returns the return information from processing 
    the first expected answer.

    """

    # the python code to be run is preamble + answer + test_program
    # this is specified in a TUT {% processor %} stanza
    penv = context['processor_env']

    # check to see if the provided expected answers is a list of length > 1
    expected = penv['answer']
    if type(expected)==list:
        nanswers = len(expected)
        if nanswers > 1:
            if answer_select==None:	# yes, so see if student's answer matches ANY of the expected ones
                firstret = None
                for k in range(nanswers):
                    ret = check(context,code,tests,dosubmit,answer_select=k)
                    check_ok = ret[0]
                    if check_ok:
                        return ret	# this answer matched the students, so return with it
                    if not firstret:	# save first return set
                        firstret = ret
                return firstret		# no answer matched; return the first

    # assemble expected and provided code for testing
    (code_expected, code_provided, initial_code) = AssembleCode(penv,code,answer_select)

    # run the input-check function if it exists in the processor environment
    # this is used, for example, to check if the code provided has a specific string, 
    # or if the code provided does recursion (or not).

    if 1:
        ret = do_input_check(penv,code)
        #ret = do_input_check(penv,code_provided)
        if ret:		# non-False return: reply with error (and debugging info)
            s = "<font color='red'><div class='progerr'>%s</div></font>" % ret
            # s += debug_code_checking(context,code_expected,code_provided,'','')
            check_ok = False
            ntests_passed = 0
            return (check_ok, s, ntests_passed, [])

    # run each test, one at a time
    tests = stripquotes(tests)
    # the tests are specified by a string of comma separated terms.
    # if any term is "repeat:XX" then replace the next term by XX times that term
    testlist = TestStringToTestList(tests)

    # provide some debugging information (only for admin)
    s = ''
    if context.has_key('is_admin'):
        if context['is_admin']:
            s += debug_code_checking(context,code_expected,code_provided,tests,testlist)

    # construct actual reply to the user
    pa = penv['answer']
    if dosubmit and not penv.has_key('hide_answer'):
        extra = ''
        if type(pa)==list:
            extra = ' (%d possibilities given)' % len(pa)
        s += '<b>This is the answer we wrote%s:</b> ' % extra
        if type(pa)==list:
            s += string.join(['<blockquote><pre>%s</pre></blockquote>' % x for x in pa],'<hr width="30%"/><br/>')
        else:
            s += '<blockquote><pre>%s</pre></blockquote>' % pa

    check_ok = True
    ntests_passed = 0
    error_line_numbers = []

    s += "<br/><b>Here are the results of your input on the test cases:</b><br/>"

    pre_length = len(penv['preamble'].splitlines())
    code_length = len(code.splitlines())

    def fix_error(match):
        g = match.groups()
        fname = g[0]
        line = int(g[1])
        instr = g[2] if len(g) > 2 else ""
        if fname.strip() == "<stdin>":
            if pre_length+9 < line <= pre_length+code_length+9:
                out = "Submitted code, line %i%s" % (line-pre_length-9,instr)
                error_line_numbers.append(line-pre_length-9)
            else:
                out = "Test code"
        else:
            out = "File \"%s\", line %i%s" % (fname.replace('/home/tutor2/tutor/python_lib/lib601/','lib601/'),line,instr)
        return out 

    def clean_error(error):
        lines = error.splitlines()
        regex =  re.compile("[ \t]*File \"(.*)\", line ([0-9]+)[(, in .*)]?")
        for ix in xrange(len(lines)):
            match = regex.match(lines[ix])
            if match:
                lines[ix] = fix_error(match)
        return "\n".join(lines)

    # run student's code and our code, unless no code was provided
    if len(code.strip())==0:	# no code was provided
        s += "<font color='blue'>No code provided, checking skipped!</font>"
        check_ok = False
    elif (code.strip().replace('\r','')==initial_code.strip()):
        s += "<font color='blue'>Code unchanged from initial stub, checking skipped!</font>"
        check_ok = False
    else:

        # run each of the test cases
        testnum = 0
        for the_test in testlist:

            testnum += 1
    
            the_test = str(the_test)
            # header
            s += '<br/><hr width="60%%"/><center><font color="blue"><div class="testhdr">Test %d</div></font></center>' % testnum

            # FIXME: why do we need to do this?
            #if m.search('^test',t):
            ## if 'test ' in t:
            #    t = t.replace('test ','')

            # special case: if test = "generate" then replace test with list of random numbers
            if the_test=='generate':
                the_test = string.join(['%d' % random.randint(0,(1<<16)-1) for k in range(5)],' ')

            # split up test into arguments, and save in environment
            argset = the_test.split(' ')
            runenv = {}
            argc = 1
            for k in argset:
                runenv['argv%d' % argc] = k
                argc += 1
            runenv['argv'] = ['pyxserv'] + argset
    
            # s += '<li> t="%s"' % t
    
            # for each test case, generate 10 random integers, which may be used as private
            # information between the testing of the student's code and testing of our code
            rndset = [ random.randint(0,(1<<16)-1) for k in range(10) ]
            rndlist = string.join(['%d' % k for k in rndset],',')
            runenv['rndlist'] = rndlist
            runenv['rndset'] = rndset
                
            (sco,sce,solog) = sandbox_run_code(code_provided,runenv)            # run student's code
            (co,ce,olog) = sandbox_run_code(code_expected,runenv)             # run our code
    
            # generate output if our code had a bug
            if ce:
                s += "<p/>oops, our code produced an error:"
                s += "<blockquote><pre>%s</pre></blockquote>" % ce.replace('<','&lt;')

            #if dosubmit:
            #    s += "<p/>" + co
    
            # fix this to use CSS formatting!
            s += '<blockquote><pre>%s</pre></blockquote>' % (sco)

            # fix this to use CSS formatting!
            s += "<p/>Your code produces:"
            if sce:
                estr = clean_error(sce)
                #error_line_numbers += lnums
                s += '<p/><font color="red">Error! If no error message follows, check for infinite loops.</font>\n'
                estr = estr.replace('<','&lt;')
                s += '<p/><pre>' + estr + '</pre>'
                
            #s += '<blockquote><pre>%s\n%s</blockquote>' % (sco,solog)

            #s += '<blockquote><pre>%s</blockquote>' % (solog)

            # remove control characters from student log output
            solog = re.sub(r"[\x01-\x09\x7f]", "", solog)

            # escape HTML characters in return string
            s += '<blockquote><pre>%s</pre></blockquote>' % (solog.replace('&','&amp;').replace('<','&lt;'))

            #s += '<blockquote><pre>%s</blockquote>' % (solog)
            #s += '<p/>output:\n<blockquote>%s</blockquote>' % olog
            #s += '<p/>stderr:\n<blockquote>%s</blockquote>' % ce
    
            # if student's code execution times out, then don't bother doing the rest of the tests
            if (sce.count('Execution timed out') and sce.count('infinite loop')) or sce.count('BAD CODE'):
                s += '<br/><font color="red">Aborting tests</font>'
                break

            #if sce:
            #    co_student = None
            #else:
            #    co_student = sco

            s += '<p/>The correct result is:\n<blockquote><font color="blue"><pre>%s</pre></font>' % olog
    
            if sce:
                olog_student = None
            else:
                olog_student = solog
    
            # compare student output with expected output
            # this_ok = (co_student == co)
            # this_ok = (olog_student == olog)
            this_ok = do_output_check(penv,olog_student,olog)

            if this_ok==True:
                s += tut_icon('checkmark')
            else:
                s += tut_icon('wrong')
                if type(this_ok)==str:
                    s += "<font color='red'><div clas='progerr'>%s</div></font>" % this_ok
            s += '\n</blockquote>\n'
    
            if this_ok==True:
                #np = context['npoints']	# award points (perhaps this should be in tut.py?)
                #np[0] += 1
                ntests_passed += 1
    
            check_ok = check_ok and (this_ok==True)

    # debugging
    # s += '<li>ntests_passed = %d' % ntests_passed

    return (check_ok, s, ntests_passed, error_line_numbers)

