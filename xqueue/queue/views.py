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
def compose_reply(success, content):
    return_code = 0 if success else 1
    return json.dumps({ 'return_code': return_code,
                        'content': content })


# Log in
#--------------------------------------------------
@csrf_exempt
def log_in(request):
    if request.method == 'POST':
        p = request.POST.copy()
        if p.has_key('username') and p.has_key('password'):
            user = authenticate(username=p['username'], password=p['password'])
            if user is not None:
                login(request, user)
                return HttpResponse(compose_reply(True, 'Logged in'))
            else:
                return HttpResponse(compose_reply(False, 'Incorrect login credentials'))
        else:
            return HttpResponse(compose_reply(False, 'Insufficient login info'))
    else:
        return HttpResponse(compose_reply(False,'login_required'))

def log_out(request):
    logout(request)
    return HttpResponse(compose_reply(success=True,content='Goodbye'))

# Status check
#--------------------------------------------------
def status(request):
    return HttpResponse(compose_reply(success=True, content='OK'))
