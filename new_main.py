# new_main.py
# Final version of CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
# Authors: Harsh Selokar, Victor Chiang, Roshin Maharana

# Importing necessary classes from other modules -- these are modules you can work on.
from architecture import Architecture
from pathlib import Path
from logger import setup_logging, StreamToLogger
import logging, sys
from modules.print import print_timing_table 

# temporary
from modules.btb import BTB

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

    loot = Architecture("instruction_sets/final.txt")
    #loot = Architecture("instruction_sets/final_demo.txt")
    #loot = Architecture("instruction_sets/branch_test.txt")
    #loot = Architecture("instruction_sets/straight_line_dependencies_no_load.txt")
    #loot = Architecture("instruction_sets/straight_line_case_no_load.txt")
    #loot = Architecture("instruction_sets/instructions.txt")
    #loot = Architecture("instruction_sets/load_store_test.txt")
    #loot = Architecture("instruction_sets/load_store_forwarding.txt")
    #loot = Architecture("instruction_sets/load_store_memory.txt")
    #loot = Architecture("instruction_sets/report.txt")

    
    print("Initial ARF and RAT contents:")
    # print_ARF_RAT(loot)
    total_cycles = 100

    print(f"Current PC: {loot.PC}")
    for i in range(1,total_cycles):
        print("----------------Issuing cycle number:", loot.clock)
        print(f"Current PC: 0x{loot.PC}")
        
        print(f"TRACKING R2: {loot.ARF.read("R2")}")
        loot.issue()
        loot.execute()
        loot.write_back()
        loot.commit()

        # Total number of clock cycles for the overall system. Seperate from the PC
        loot.clock += 1
        print("--------------------------------------------------")

   # print(f"Final ARF and RAT contents after {total_cycles} issue/execute cycles:")
    print_ARF_RAT(loot)
    print_ROB(loot)

    print_timing_table(loot.instructions_in_flight)
    #for store word test
    print(loot.MEM.read(32))


def test_btb():
    hi = BTB()
    hi.add_branch(0xF, 0xA)           # insert (tag = 0xA & 0b111 = 0b010)
    print(hi.find_prediction(0xF))    
    hi.change_prediction(0xF, True)
    print(hi.find_prediction(0xF))    
    print(hi.get_target(0xF))         # 0xF
    print(hi)

if __name__ == "__main__":
	check_init()  