# new_main.py
# Final version of CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
# Authors: Harsh Selokar, Victor Chiang, Roshin Maharana

# Importing necessary classes from other modules -- these are modules you can work on.
from architecture import Architecture
from pathlib import Path
from logger import setup_logging, StreamToLogger
import logging, sys

# Helper : Function to print ARF and RAT contents
def print_ARF_RAT(arch):
    print("Architectural Register File (ARF) Contents:")
    for i in range(1, 33):
        print(f"R{i}: {arch.ARF.read('R'+ str(i))}")
    for i in range(1, 33):
        print(f"F{i}: {arch.ARF.read('F'+ str(i))}")

    print("\nRegister Alias Table (RAT) Contents:")
    for i in range(1, 33):
        print(f"R{i}: {arch.RAT.read('R'+ str(i))}")
    for i in range(1, 33):
        print(f"F{i}: {arch.RAT.read('F'+ str(i))}")

def print_ROB(arch):
    print("\nReorder Buffer (ROB) Contents:")
    print(arch.ROB)

# Helper : Function to run a test simulation
def check_init():
    try:
        Path("run.log").unlink()
    except FileNotFoundError:
        pass

    # initialize handlers (console + run.log)
    setup_logging("run.log")

    # existing print() calls to also go into logging
    sys.stdout = StreamToLogger(logging.getLogger("stdout"), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger("stderr"), logging.ERROR)

    print("logger initialized")  

    #loot = Architecture("instruction_sets/branch_test.txt")
    loot = Architecture("instruction_sets/straight_line_dependencies_no_load.txt")
    #loot = Architecture("instruction_sets/straight_line_case_no_load.txt")
    #loot = Architecture("instruction_sets/instructions.txt")
    
    print("Initial ARF and RAT contents:")
    # print_ARF_RAT(loot)
    total_cycles = 30

    for i in range(1,total_cycles):
        print("----------------Issuing cycle number:", loot.clock)
        loot.issue()
        loot.execute()
        loot.write_back()
        loot.commit()
        loot.clock += 1
        print("--------------------------------------------------")

    print(f"Final ARF and RAT contents after {total_cycles} issue/execute cycles:")
    print_ARF_RAT(loot)
    print_ROB(loot)

# Don't use this, use the correct __name__ guard below
def main():
    print("CPU Simulator Main Module")

    loot = Architecture("instruction_sets/instructions.txt")
    
    # Test ARF,ROB,RAT, and RS are intialized properly
    print("Now printing RAT Contents")
    for i in range(0,len(loot.RAT)):
          curr = loot.RAT[i]
          print(curr.ARF_reg,loot.RAT.current_alias)

if __name__ == "__main__":
	check_init()