from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt

import json

# Xqueue reply format:
#    JSON-serialized dict:
#    { 'return_code': 0(success)/1(error),
#      'content'    : 'my content', }
#--------------------------------------------------
def _compose_reply(success, content):
    return_code = 0 if success else 1
    return json.dumps({ 'return_code': return_code,
                        'content': content })

# Log in
#--------------------------------------------------
@csrf_exempt
def log_in(request):
    if request.method == 'POST':
        p = request.POST.dict()
        if p.has_key('username') and p.has_key('password'):
            user = authenticate(username=p['username'], password=p['password'])
            if user is not None:
                login(request, user)
                return HttpResponse(_compose_reply(success=True,
                                               content='Logged in'))
            else:
                return HttpResponse(_compose_reply(success=False,
                                               content='Incorrect login credentials'))
        else:
            return HttpResponse(_compose_reply(success=False,
                                               content='Insufficient login info'))
    else:
        return HttpResponse(_compose_reply(success=False,
                                           content='Log in with HTTP POST'))

def log_out(request):
    logout(request)
    return HttpResponse(_compose_reply(success=True,content='Goodbye'))

# Status check
#--------------------------------------------------
def status(request):
    return HttpResponse(_compose_reply(success=True, content='OK'))
