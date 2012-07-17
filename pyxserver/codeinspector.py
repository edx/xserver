from bdb import Bdb, Breakpoint
import tempfile, sys, os, shutil

class Code_Inspector(Bdb):

    def __init__(self, student_source):
        Bdb.__init__(self)
        self.student_source = student_source
        self.variable_trackers = []
        
    def __enter__(self):
        code_file_name = tempfile.mkstemp(suffix=".py")[1]
        self.code_file = open(code_file_name, 'w+')
        self.code_file.write(self.student_source)
        self.code_file.seek(0)
        sys.path.append(os.path.abspath(os.path.join(self.code_file.name, os.path.pardir)))
        return self
        
    def __exit__(self, type, value, traceback):
        self.code_file.close()
        os.remove(self.code_file.name)

    def user_line(self, frame):
        """This method is called when we stop or break at this line."""
        breakpoints = self.get_breaks(frame.f_code.co_filename, frame.f_lineno)
        if breakpoints:
            for breakpoint in breakpoints:
                breakpoint.inspection_function(frame)
    
    def inspect_line(self, lineno, inspect_frame):
        """
        sets a breakpoint at filename, lineno and a function (which takes a frame) to execute on
        the frame when that breakpoint is hit
        """
        self.set_break(self.code_file.name, lineno).inspection_function = inspect_frame

    def inspect_variable(self, variable, inspect_variable_changes):
        """
        takes a variable of interest and a function describing out to think about
        that variable's changes (it takes a list of values) and registers that function 
        so that it will eventually recieve the appropriate input.
        """
        self.code_file.seek(0)
        tracker = VariableTracker(variable, inspect_variable_changes)
        self.variable_trackers.append(tracker)
        lineno = 0
        for line in self.code_file:
            lineno +=1
            if variable in line:
                self.inspect_line(lineno, tracker.recieve_variable_call) 

    # Largely copy-pasted from the Bdb implementation, but returns a reference to the 
    # breakpoint it just made rather than dropping it.
    def set_break(self, filename, lineno, temporary=0, cond = None,
                  funcname=None):
        filename = self.canonic(filename)
        import linecache # Import as late as possible
        line = linecache.getline(filename, lineno)
        if not line:
            return 'Line %s:%d does not exist' % (filename,
                                   lineno)
        if not filename in self.breaks:
            self.breaks[filename] = []
        list = self.breaks[filename]
        if not lineno in list:
            list.append(lineno)
        return Breakpoint(filename, lineno, temporary, cond, funcname)

    def inspect_dispatch(self, function_call):
        """
        dispatches all of the inspection that has been set up and returns 
        the results of each of those inspections. 
        """
        student_code = __import__(os.path.basename(self.code_file.name[:-3]))
        self.run("student_code."+function_call, locals = locals())
        ans = []
        for tracker in self.variable_trackers:
            ans.append(tracker.determine_value())
        return ans

class VariableTracker:
    """
    Used to track a single variable which might be present on many different lines
    """
    def __init__(self, variable, analyzer):
        self.matrix = {}
        self.analyzer = analyzer
        self.var = variable
    def recieve_variable_call(self, frame):
        """
        used to track a particular line on which a variable is found
        """
        if self.var in frame.f_locals:
            if not frame.f_lineno in self.matrix:
                self.matrix[frame.f_lineno] = []
            self.matrix[frame.f_lineno].append(frame.f_locals[self.var])

    def determine_value(self):
        return max([self.analyzer(values) for values in self.matrix.values()])     

if __name__ == "__main__":
    mock_code = """
def calc_payments(balance, interest):
    lower = balance/12
    upper = (balance * (1+interest/12)**12)/12
    monthly_interest = interest/12
    calced_balance = balance
    while abs(calced_balance) > .2:
        calced_balance = balance
        payment = (upper - lower)/2 + lower
        for i in range(12):
            calced_balance -= payment
            calced_balance *= 1+monthly_interest
        if calced_balance > 0: #too big, need higher payment
            lower = payment
        else:
            upper = payment
    return payment
"""

    def inspect_function(values):
        diff = -1 #all new assignments will keep diff positive
        if (len(values)<3):
            return False
        for i in range(1, len(values)-1):
            old_diff = diff
            diff = abs(values[i]-values[i-1])
            if diff < .001 or (old_diff > 0 and diff > .55*old_diff):
                return False
        return True

    with Code_Inspector(mock_code) as my_ci:
        my_ci.inspect_variable("payment", inspect_function)
        print my_ci.inspect_dispatch("calc_payments(3500000, .01)")

    mock_code = """
def calc_payments(balance, interest):
    payment = 0
    monthly_interest = interest/(12.0)
    calced_balance = balance
    while calced_balance > 0:
        calced_balance = balance
        payment += 10
        for i in range(12):
            calced_balance -= payment
            calced_balance *= 1+monthly_interest
    return payment
        
""" 
    with Code_Inspector(mock_code) as my_ci:
        my_ci.inspect_variable("payment", inspect_function)
        print my_ci.inspect_dispatch("calc_payments(3500, .01)")
