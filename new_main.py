# new_main.py
# Final version of CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
# Authors: Harsh Selokar, Victor Chiang, Roshin Maharana

# Importing necessary classes from other modules -- these are modules you can work on.
from architecture import Architecture

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

def check_init():
    loot = Architecture("instruction_sets/instructions.txt")
    print_ARF_RAT(loot)

    for i in range(0,20):
        print("Issuing cycle number:", loot.clock)
        loot.issue()
        print(f"[DEBUG] {loot.fs_fp_add}")
        # loot.fs_fp_add.table[0].print_RS()
        # loot.issue()
        # loot.fs_fp_add.table[1].print_RS()
        loot.execute()
        loot.write_back()
        loot.clock += 1
        # print_ARF_RAT(loot)

    print("Final ARF and RAT contents after 5 issue/execute cycles:")
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

    # print("Instructions in queue:")
    # for instr in loot.instruction_queue:
    #     print(instr)

if __name__ == "__main__":
	check_init()