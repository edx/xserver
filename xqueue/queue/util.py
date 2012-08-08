import hashlib

def make_hashkey(seed):
    '''
    Generate a hashkey (string)
    '''
    h = hashlib.md5()
    h.update(str(seed))
    return h.hexdigest()

def get_request_ip(request):
    '''
    Retrieve the IP origin of a Django request
    '''
    ip = request.META.get('HTTP_X_REAL_IP','') # nginx reverse proxy
    print 'HTTP_X_REAL_IP: %s' % ip
    if not ip:
        ip = request.META.get('REMOTE_ADDR','None')
        print 'REMOTE_ADDR: %s' % ip
    return ip
