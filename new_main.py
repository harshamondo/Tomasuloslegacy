# new_main.py
# Final version of CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
# Authors: Harsh Selokar, Victor Chiang, Roshin Maharana

# Importing necessary classes from other modules -- these are modules you can work on.
from architecture import Architecture

def check_init():
    loot = Architecture("instruction_sets/instructions.txt")
    # for i in range(1,32):
    #     print(loot.ARF.read("R"+ str(i)))
    #     print(loot.RAT.read("R"+ str(i)))

    # for i in range(33,65):
    #     print(loot.ARF.read("R"+ str(i)))
    #     print(loot.RAT.read("R"+ str(i)))

# Don't use this, use the correct __name__ guard below
def main():
    print("CPU Simulator Main Module")

    loot = Architecture("instruction_sets/instructions.txt")
    
    # Test ARF,ROB,RAT, and RS are intialized properly
    print("Now printing RAT Contents")
    for i in range(0,len(loot.RAT)):
          curr = loot.RAT[i]
          print(curr.ARF_reg,loot.RAT.current_alias)

    # # print("Instructions in queue:")
    # # for instr in loot.instruction_queue:
    # #     print(instr)

if __name__ == "__main__":
	check_init()
