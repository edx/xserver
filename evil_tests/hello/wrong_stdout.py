# take back stdout
import sys
sys.stdout = sys.__stdout__

print("O hai")
