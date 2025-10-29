# Reservation Station Unit - used to represent each entry in a reservation station
# [status][DST_tag][opcode][tag1][tag2][value1][value2]
# will slowly count clock cycles to simulate execution time
# status means the value is ready for execute
from collections import deque
class RS_Unit:
      def __init__(self,DST_tag = None, opcode = None, reg1 = None, reg2 = None, RAT_object = None, ARF_object = None, cycles_issued = None):
            self.opcode = opcode
            self.tag1 = None
            self.tag2 = None
            self.value1 = None
            self.value2 = None
            self.cycles_left = None
            self.cycle_issued = cycles_issued
            self.DST_value = None
            self.reg1 = reg1
            self.reg2 = reg2
            self.ARF_tag = DST_tag

            self.RAT = RAT_object
            self.ARF = ARF_object

            self.DST_tag = RAT_object.read(DST_tag)


            if self.RAT.read(self.reg1) != None and self.RAT.read(self.reg1)[:3] == "ROB":
                self.tag1 = self.RAT.read(self.reg1)
            elif self.RAT.read(self.reg1) != None and self.RAT.read(self.reg1)[:3] == "ARF":
                self.value1 = self.ARF.read(self.reg1)

            
            if self.RAT.read(self.reg2) != None and self.RAT.read(self.reg2)[:3] == "ROB":
                self.tag2 = self.RAT.read(self.reg2)
            elif self.RAT.read(self.reg2) != None and self.RAT.read(self.reg2)[:3] == "ARF":
                self.value2 = self.ARF.read(self.reg2)
        
      def print_RS(self):
           print("Now printing RS entry:")
           print("[",self.opcode,"]","[",self.DST_tag,"]","[",self.tag1,"]","[",self.tag2,"]","[",self.value1,"]","[",self.value2,"]")
      
      def __str__(self):
            return (f"DST_tag={self.DST_tag}, DST_value={self.DST_value}, opcode={self.opcode}, "
                  f"tag1={self.tag1}, tag2={self.tag2}, value1={self.value1}, value2={self.value2})")

# Reservation Station Table - holds multiple RS_Unit objects
# Type indicates the type of functional unit it is associated with (e.g., Integer Adder, FP Adder, Multiplier, Load/Store)
# number of units indicates how many RS_Unit entries it can hold at maximum
class RS_Table:
    def __init__(self, type = None, num_rs_units = 0, num_FU_units = 0, cycles_per_instruction = 0):
        self.table = []
        self.type = type
        self.num_units = num_rs_units
        self.num_FU_units = num_FU_units
        self.cycles_per_instruction = cycles_per_instruction
        self.busy_FU_units = 0

       #store/load RS are queues
        if self.type == "fs_fp_ls":
            self.table = deque()
    
    def add_unit(self, rs_unit):

        self.table.append(rs_unit)

    def __str__(self):
        # Build a string instead of printing directly
            output = []
            output.append(f"Reservation Station Table Type: {self.type}")
            output.append(f"Number of Units: {self.num_units}")
            output.append(f"Number of Functional Units: {self.num_FU_units}")
            output.append(f"Busy Functional Units: {self.busy_FU_units}")
            output.append("Current Entries:")

            if not self.table:
                  output.append("[Empty]")
            else:
                  for i, unit in enumerate(self.table):
                        output.append(f"  [{i}] {unit}")

            # Join everything into a single string and return it
            return "\n".join(output)

    def check_rs_full(self):
        return len(self.table) >= self.num_units
    
    def use_fu_unit(self):
      if self.busy_FU_units < self.num_FU_units:
            self.busy_FU_units += 1
            return True
      return False

    def release_fu_unit(self):
        if self.busy_FU_units > 0:
            self.busy_FU_units -= 1
            return True
        return False
