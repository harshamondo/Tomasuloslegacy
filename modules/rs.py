# Reservation Station Unit - used to represent each entry in a reservation station
# [status][DST_tag][opcode][tag1][tag2][value1][value2]
# will slowly count clock cycles to simulate execution time
# status means the value is ready for execute
class RS_Unit:
      def __init__(self,DST_tag = None, opcode = None, reg1 = None, reg2 = None, RAT_object = None, ARF_object = None):
            self.opcode = opcode
            self.tag1 = None
            self.tag2 = None
            self.value1 = None
            self.value2 = None

            self.reg1 = reg1
            self.reg2 = reg2

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