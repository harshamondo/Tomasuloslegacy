import re 

# Reservation Station Unit - used to represent each entry in a reservation station
# [status][DST_tag][opcode][tag1][tag2][value1][value2]
# will slowly count clock cycles to simulate execution time
# status means the value is ready for execute
class RS_Unit:
      def __init__(self, status = None, DST_tag = None, type = None, opcode = None, tag1 = None, tag2 = None, value1 = None, value2 = None):
            self.status = False
            self.DST_tag = ""
            self.DST_value = None
            self.type = ""
            self.opcode = ""
            self.tag1 = ""
            self.tag2 = ""
            self.value1 = None
            self.value2 = None
            self.cycles_left = None

      def del_entry(self):
            self.__init__()

      def add_entry(self,status = None, DST_tag = None, type = None, opcode = None, reg1 = None, reg2 = None):
            #this function will recieve src operands and check if the registers point to ARF or a ROB entry and update accordingly
            self.status = status
            self.DST_tag = DST_tag
            self.opcode = opcode
            self.type = type
            
            #if the rat points to ARF then find the ARF value, if not write the ROB entry to the RS
            if self.RAT[int(reg1[1:])].current_alias[:3] == "ARF":
                  self.value1 = self.ARF[self.RAT[int(reg1[1:])]].value
            else:
                  self.tag1 = self.RAT[int(reg1[1:])].current_alias

            if self.RAT[int(reg2[1:])].current_alias[:3] == "ARF":
                  self.value1 = self.ARF[self.RAT[int(reg2[1:])]].value
            else:
                  self.tag1 = self.RAT[int(reg2[1:])].current_alias
      
      def print_RS(self):
            print(f"RS Unit - Status: {self.status}, DST_tag: {self.DST_tag}, Opcode: {self.opcode}, Tag1: {self.tag1}, Tag2: {self.tag2}, Value1: {self.value1}, Value2: {self.value2}")

      def __str__(self):
            return (f"RS_Unit(status={self.status}, DST_tag={self.DST_tag}, opcode={self.opcode}, "
                    f"tag1={self.tag1}, tag2={self.tag2}, value1={self.value1}, value2={self.value2})")
      
      def set_cycles(self, cycles):
            self.cycles_left = cycles

      def get_cycles(self):
            return self.cycles_left

      def decrement_cycles(self):
            if self.cycles_left is not None and self.cycles_left > 0:
                  self.cycles_left -= 1
            return self.cycles_left

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
