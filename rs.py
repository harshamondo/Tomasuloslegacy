# Reservation Station Unit - used to represent each entry in a reservation station
# [status][DST_tag][opcode][tag1][tag2][value1][value2]
# will slowly count clock cycles to simulate execution time
# status means the value is ready for execute
class RS_Unit:
      def __init__(self, status = None, DST_tag = None, type = None, opcode = None, tag1 = None, tag2 = None, value1 = None, value2 = None):
            self.status = False
            self.DST_tag = ""
            self.type = ""
            self.opcode = ""
            self.tag1 = ""
            self.tag2 = ""
            self.value1 = None
            self.value2 = None

      def del_entry(self):
            self.__init__()

      def add_entry(self,status = None, DST_tag = None, opcode = None, reg1 = None, reg2 = None):
            #this function will recieve src operands and check if the registers point to ARF or a ROB entry and update accordingly
            self.status = status
            self.DST_tag = DST_tag
            self.opcode = opcode
            
            #if the rat points to ARF then find the ARF value, if not write the ROB entry to the RS
            if self.RAT[int(reg1[1:])].current_alias[:3] == "ARF":
                  self.value1 = self.ARF[self.RAT[int(reg1[1:])]].value
            else:
                  self.tag1 = self.RAT[int(reg1[1:])].current_alias

            if self.RAT[int(reg2[1:])].current_alias[:3] == "ARF":
                  self.value1 = self.ARF[self.RAT[int(reg2[1:])]].value
            else:
                  self.tag1 = self.RAT[int(reg2[1:])].current_alias
            
    

# Reservation Station Table - holds multiple RS_Unit objects
# Type indicates the type of functional unit it is associated with (e.g., Integer Adder, FP Adder, Multiplier, Load/Store)
# number of units indicates how many RS_Unit entries it can hold at maximum
class RS_Table:
    def __init__(self, type = None, num_rs_units = 0, num_FU_units = 0):
        self.table = []
        self.type = type
        self.num_units = num_rs_units
        self.num_FU_units = num_FU_units
        self.busy_FU_units = 0
    
    def add_unit(self, rs_unit):
        self.table.append(rs_unit)

    def __str__(self):
        print(f"Reservation Station Table Type: {self.type}")
        print(f"Number of Units: {self.num_units}")
        print(f"Number of Functional Units: {self.num_FU_units}")
        print(f"Busy Functional Units: {self.busy_FU_units}")
        for unit in self.table:
            print(unit.__dict__)

    def check_full(self):
        return len(self.table) >= self.num_units