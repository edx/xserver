#!/usr/bin/python
import json
import requests

#------------------------------------------------------------
# Simple demo of the (asynchronous) external grading interface.
# Xqueue API consists of:
#	1) get_queuelen:   Get length of specific queue
#	2) get_submission: Get single submission from a specific queue
#	3) put_result:	   Return the results of a submission
#------------------------------------------------------------
def main():
	xqueue_url = 'http://107.20.215.194/'
	queue_name = 'mitx-600x'

	# 1. Get length of queue
	#------------------------------------------------------------
	r = requests.get(xqueue_url+'xqueue/get_queuelen/',
					 params={'queue_name':queue_name})
	xreply = json.loads(r.text)
	if xreply['return_code']: # Non-zero return code indicates error 
		print xreply['content']
		return
	queuelen = xreply['content']
	print "Queue '%s' has %d awaiting jobs" % (queue_name, queuelen)
	if queuelen < 1:
		return

	# 2. Contact xqueue and get a student submission
	#------------------------------------------------------------
	r = requests.get(xqueue_url+'xqueue/get_submission/',
					 params={'queue_name':queue_name})
	xreply = json.loads(r.text)
	if xreply['return_code']:
		print xreply['content']	
		return

	# Extract the package, which consists of header and body, 
	#	from the reply
	#------------------------------------------------------------
	xpackage = json.loads(xreply['content'])

	xheader = xpackage['xqueue_header'] # Xqueue callback and secret key	
	xbody   = xpackage['xqueue_body']   # Grader-specific serial data

	# The current 'pull_once' routine is a wrapper for the
	#	synchronous 6.00x grader (pyxserver)
	# So, pyxserver should be running in the background
	#------------------------------------------------------------
	r = requests.post('http://127.0.0.1:3031',data=xbody)
	grader_reply = r.text # Serialized text

	# 3. Return graded result to xqueue
	#------------------------------------------------------------
	xpackage = {'xqueue_header': xheader,
	            'xqueue_body'  : grader_reply,}
	r = requests.post(xqueue_url+'xqueue/put_result/',
					 data=xpackage)
	xreply = json.loads(r.text)
	if xreply['return_code']:
		print xreply['content']

if __name__ == "__main__":
	main()
