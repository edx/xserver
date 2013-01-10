XQueue worker interface
-----------------------

XQueue will push student submissions to your server using an HTTP JSON 
protocol.  

The request will have a JSON object as a body, with these keys:

    "xqueue_body": A string, a JSON-encoded object with these keys:

        "student_response": A string, the student's response.
            The main task of the grader is to determine the correctness
            of this response.
        
        "grader_payload": A string, can be anything, you can interpret it
            any way you like.  It will be taken from the content of the 
            <grader_payload> XML tag in the problem.  We use JSON data here
            as an easy way to pass extensible data to the grader.  This 
            payload is where you can specify the details of the grading
            process to the grader.

    "xqueue_files": Ignore this.

An example request could look like this:

    {
    "xqueue_body": 
        "{\"student_response\": \"def double(x):\\n    return 2*x\\n\", \"grader_payload\": \"anything_you_like\"}"
    }

Note that student_response in xqueue_body (and potentially grader_payload as
well, depending on what you choose to do with it, is a JSON-encoded string,
which is then used as a string in a JSON object.

Your response must have a JSON object as a body, with these keys:

    "correct": true or false
    "score": A numeric value to assign to the answer, we often use 0 or 1.
    "msg": An HTML string, will be shown to user.


A sample response could look like this:

    {
    "correct": true,
    "score": 1,
    "msg": "<p>Great! You got the right answer!</p>"
    }

