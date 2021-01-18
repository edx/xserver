i = 1
for x in range(10**7):
    i += x

# correct output, but takes too long
print("hello world")

# Debugging
import sys
sys.stdout = sys.__stdout__

print("#" * 80)
print("Still running!  Should have been killed.")
print("#" * 80)
