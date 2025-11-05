# new_main.py
# Final version of CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
# Authors: Harsh Selokar, Victor Chiang, Roshin Maharana

# Importing necessary classes from other modules -- these are modules you can work on.
from architecture import Architecture
from modules.print import print_timing_table 

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
    
    loot = Architecture("instruction_sets/straight_line_dependencies_no_load.txt") 
    # loot = Architecture("instruction_sets/straight_line_case_no_load.txt")
    # loot = Architecture("instruction_sets/instructions.txt")
    
    # Increased total cycles for a safe maximum limit
    total_cycles = 30

    for i in range(1,total_cycles):
        print("----------------Issuing cycle number:", loot.clock)
        
        # Calling the functions in reversed  order: commit --> WB --> Execute --> Issue
        #If you guys can make some changes in each of the functions then then the order can be reversed
        loot.commit()
        loot.write_back() 
        loot.execute()
        loot.issue()
        
        loot.clock += 1
        print("--------------------------------------------------")
        
        # Stop simulation if all instructions have committed
        if (
            all(instr.commit_cycle is not None for instr in loot.instructions_in_flight) 
            and loot.instruction_pointer >= len(loot.instructions_in_flight) 
            and loot.ROB.getEntries() == 0
        ):
            print(f"All instructions committed after {loot.clock - 1} cycles. Stopping simulation.")
            break

    print(f"Final ARF and RAT contents after {loot.clock - 1} cycles:")
    print_ARF_RAT(loot)
    print_ROB(loot)
    
    # Call the print function with the list of Instruction objects
    print_timing_table(loot.instructions_in_flight) 

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