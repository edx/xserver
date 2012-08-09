"""
Various common utility functions for Tutor2 system code

 - B{debug_http}: for debugging request.POST returns

"""

import math

def getkey2(dict,key,default):
    """utilify function: get dict[key] if key exists, or return default"""
    if dict.has_key(key):
        return dict[key]
    return default

def incr_key(dict,key,delta):
    "utility function: add delta to dict[key] if key exists, else set dict[key]=delta"
    if dict.has_key(key):
        dict[key] += delta
    else:
        dict[key] = delta

def tut_icon(name):
    'Return HTML code for various tutor icons'
    if name=='checkmark':
        return '&nbsp;<img src="http://sicp-s3.mit.edu/tutorexport/images/checkmrk-small.jpg" align="top" alt="WELL DONE"/>\n'
    if name=='wrong':
        return '&nbsp;<img src="http://sicp-s3.mit.edu/tutorexport/images/xncircle-small.jpg" align="top" alt="WRONG"/>'
    if name=='question':
        return '&nbsp;<img src="http://sicp-s3.mit.edu/tutorexport/images/qmrk-small.gif" align="top" alt="NO ANSWER"/>\n'
    return ''

def c_str(s,color):
    'Return HTML code for text in specified color'
    return '<font color="%s">%s</font>' % (color,str(s))

def debug_http(request):
    """
    Provides: debugging page, listing all key,val from request.POST
    """
    s = ''
    for k in request.POST:
        s += '<li> %s: %s' % (k,request.POST[k])
    return s

def traverse_nodes(nodelist,nodetype,fn):
    """
    Walks through nodelist tree from parsing template and performs specified
    function on specified node type.
    """
    for n in nodelist:
        if type(n)==nodetype:
            fn(n)
        if hasattr(n,'nodelist'):
            traverse_nodes(n.nodelist,nodetype,fn)

def stripquotes(s):
    quotes = list('"\'')
    if s[0] in quotes and s[-1] in quotes:
        return s[1:-1]
    return s

# statistics class
class StatVar(object):
    """
    Simple statistics on floating point numbers: avg, sdv, var, min, max
    """
    def __init__(self,unit=1):
        self.sum = 0
        self.sum2 = 0
        self.cnt = 0
        self.unit = unit
        self.min = None
        self.max = None
    def add(self,x):
        if x==None:
            return
        if not self.min:
            self.min = x
        else:
            if x<self.min:
                self.min = x
        if not self.max:
            self.max = x
        else:
            if x>self.max:
                self.max = x
        self.sum += x
        self.sum2 += x**2
        self.cnt += 1
    def avg(self):
        if not self.cnt:
            return 0
        return self.sum / 1.0 / self.cnt / self.unit
    def var(self):
        if not self.cnt:
            return 0
        return (self.sum2 / 1.0 / self.cnt / (self.unit**2)) - (self.avg()**2)
    def sdv(self):
        v = self.var()
        if v>0:
            return math.sqrt(v)
        else:
            return 0
    def __str__(self):
        return 'cnt=%d, avg=%f, sdv=%f' % (self.cnt,self.avg(),self.sdv())
    def __add__(self,x):
        self.add(x)
        return self

