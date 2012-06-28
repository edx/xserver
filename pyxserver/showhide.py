#!/usr/bin/python
#
# File:   tutor/tutor2/showhide.py
# Date:   22-Jul-11
# Author: I. Chuang <ichuang@mit.edu>
#
# python functions for providing HTML code for javascript show/hide div
#
# change this to use configuration variables, or read from template

def start(sid):
    return '<div id="DivPartHeader"><div id="DivPart%sTitle">' % str(sid)

def link(sid,display=False):
    if display:
        ls = '<img src="/tutorexport/images/minus.png"/>Hide'
    else:
        ls = '<img src="/tutorexport/images/plus.png"/>Show'
    return '<a id="DivLink%s" href="javascript:showhide(\'DivPartContent%s\',\'DivLink%s\');">%s</A></div></div>' % (str(sid),str(sid),str(sid),ls)

def content(sid,display=False):
    if display:
        ls  = 'block'
    else:
        ls = 'none'
    return '<div id="DivPartContent%s" style="display: %s;">' % (str(sid),ls)

def end(sid):
    return '</div>';
