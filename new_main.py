# new_main.py
# Final version of CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
# Authors: Harsh Selokar, Victor Chiang, Roshin Maharana

from collections import deque
import re
import csv

class Instruction:
	# Define class for Instruction
	def __init__(self, opcode=None, operands=None):
		self.opcode = opcode										# Operation code of the instruction
		# Operands typically go destination, source1, source2
		self.operands = operands if operands is not None else []	# List of operands for the instruction
		# Named fields for common instruction types
		self.dest = None
		self.src1 = None
		self.src2 = None
		self.offset = None
		self.immediate = None

		# Parse operands for specific opcodes
		if opcode is not None and operands is not None:
			op = opcode.lower()
			# Load/Store: Ld Fa, offset(Ra) or Sd Fa, offset(Ra)
			if op in ["ld", "sd"] and len(operands) == 2:
				self.dest = operands[0]
				# Parse offset(Ra)
				match = re.match(r"(-?\d+)\((\w+)\)", operands[1])
				if match:
					self.offset = int(match.group(1))
					self.src1 = match.group(2)
			# Integer/FP ALU: Add Rd, Rs, Rt or Add.d Fd, Fs, Ft
			elif op in ["add", "sub", "addi", "beq", "bne"] and len(operands) >= 3:
				self.dest = operands[0]
				self.src1 = operands[1]
				self.src2 = operands[2]
				if op == "addi" and len(operands) == 3:
					self.immediate = operands[2]
			elif op in ["add.d", "sub.d", "mult.d"] and len(operands) == 3:
				self.dest = operands[0]
				self.src1 = operands[1]
				self.src2 = operands[2]
			# NOP
			elif op == "nop":
				pass

	# String representation of the Instruction
	def __str__(self):
		return (f"Instruction(opcode={self.opcode}, operands={self.operands}, "
				f"dest={self.dest}, src1={self.src1}, src2={self.src2}, "
				f"offset={self.offset}, immediate={self.immediate})")

	# Destructor for Instruction class
	def __del__(self):
		# Add any cleanup code here if needed
		pass

class ROB_entry:
      def __init__(self,src_reg = None):
            self.src_reg = ""
            self.value = 0
            self.done = False

# Reservation Station Unit - used to represent each entry in a reservation station
# [status][DST_tag][opcode][tag1][tag2][value1][value2]
# will slowly count clock cycles to simulate execution time
# status means the value is ready for execute
class RS_Unit:
      def __init__(self,status = None, DST_tag = None, type = None, opcode = None, tag1 = None, tag2 = None, value1 = None, value2 = None):
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

class RAT:
      def __init__(self,current_alias = None):
            #ARF_reg = R1, R2 ...etc
            self.ARF_reg = ""
            #current_alias is a integer representing ROB reg number starting from 1
            self.current_alias = None

class ARF:
      def __init__(self,type = None):
            self.type = ""
            self.reg = ""
            self.value = ""
            
class Architecture:
    def __init__(self,filename = None):
        self.filename = filename
        self.config = "config.csv"
        
        #parse through config.txt and update
        #default values for testing, will update through parsing later
        self.int_adder_FU = 1
        self.FP_adder_FU = 1
        self.multiplier_FU = 1
        self.load_store_FU = 1

        self.int_adder_num = 2
        self.FP_adder_num = 3
        self.multiplier_num = 2
        self.load_store_num = 3

        self.clock = 0

        #parsing code to set the number of functional units and reservation stations will go here
        
        with open(self.config, newline='') as f:
            reader = csv.DictReader(f)

            header = next(reader)  # Skip header row
            print(f"Header : {header}")  # For debugging purposes

            # operations to read configuration
            for line in f:
                line = line.strip()
                type_name = row.get("Type", "").strip().lower()
                rs_field = row.get("# of rs")
                ex_field = row.get("Cycles in EX")
                mem_field = row.get("Cycles in Mem")
                fu_field = row.get("# of FUs")

                if type_name == "integer adder":

        #Initialize instruction register
        self.instruction_queue = deque()
        self.init_instr()

        #initialize RAT and ARF
        #include ways to update ARF based on parameters
        #registers 0-31 and R and 32-64 are F
        self.ARF = [64]
        self.init_ARF()
        self.RAT = [64]
        self.init_RAT()

        #initial same number of rows as instructions in queue for now
        #ROB should be a queue
        self.ROB = deque()

        #assume individual RS
		#[OP][Dst-Tag][Tag1][Tag1][Val1][Val2]
        #RS_tables will contain an array of RS_unit objects
        #self.RS_tables = []
        self.int_adder_RS = []
        self.FP_adder_RS = []
        self.multiplier_RS = []
        self.load_store_RS = []
        self.init_config()


    """
Helper functions for ISSUE
"""
    # Fetch instructions from a file
    def parse(self):
            """
            Reads instructions from a file and returns them as a list of (opcode, operands) tuples.
            """
            instructions = []
            with open(self.filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.replace(',', '').split()
                    if len(parts) > 0:
                        opcode = parts[0]
                        operands = parts[1:]
                        instructions.append((opcode, operands))
            return instructions


    def gen_instructions(self,instruction_list):
        """
        Fetches instructions from instruction_list, decodes them into Instruction objects, and puts them into the global instruction_queue.
        """
        while instruction_list:
            instr = instruction_list.pop(0)
            # If already tuple (opcode, operands), just use it
            if isinstance(instr, tuple):
                opcode, operands = instr
                self.instruction_queue.append(Instruction(opcode, operands))
            elif isinstance(instr, str):
                # Fallback: decode string
                parts = instr.replace(',', '').split()
                if len(parts) > 0:
                    opcode = parts[0]
                    operands = parts[1:]
                    self.instruction_queue.append(Instruction(opcode, operands))


    """
    ISSUE --------------------------------------------------------------
    """
    def init_instr(self):
        instructions_list = self.parse()
        self.gen_instructions(instructions_list)
    
    def init_config(self):
          #parse config.txt
          #include code to parse config.txt and update # of RS for each unit accordingly, for now it is hardcoded to initialize the RS tables
          for i in range(1,self.FP_adder_num):
                self.FP_adder_RS.append(RS_Unit())
          for i in range(1,self.int_adder_num):
                self.int_adder_RS.append(RS_Unit())
          for i in range(1,self.multiplier_num):
                self.multiplier_RS.append(RS_Unit())
          for i in range(1,self.load_store_num):
                self.load_store_RS.append(RS_Unit())

          #debug
          #print(len(self.FP_adder_RS))
    def init_ARF(self):
        #can add logic here to insert default values into the ARF
        for i in range (0,31):
              self.ARF.append(ARF("R"))
        for i in range (32,63):
              self.ARF.append(ARF("F"))

    def init_RAT(self):
        #this function will initialize an array of RAT class objects and assign them to the value of ARF
        for i in range(len(self.ARF)):
              self.RAT.append(RAT("ARF" + str(i + 1)))

    def issue(self):
        #add instructions into the RS if not full
        #think about how we are going to stall
        #ask prof if we need to have official states like fetch and decode since our instruction class already handles fetch+decode
        current_instruction = self.fetch()
        check = current_instruction.opcode
        issued = False
        if check == "Add.d":
            #check FP add RS
            for i in self.FP_adder_RS:
                  if i == None and i.status == False:
                        #add to ROB table
                        #update RAT
                        self.ROB.append(ROB_entry(current_instruction.dest))
                        self.RAT[current_instruction.dest[-1]].current_alias = "ROB" + str(len(self.ROB)+1)
                        
                        #add to reservation stations
                        #[status][DST_tag][opcode][tag1][tag2][value1][value2]
                        self.FP_adder_RS[i].add_entry(True,self.RAT[current_instruction.dest[-1]].current_alias,check,current_instruction.src1, current_instruction.src2)
                        issued = True
                        
            if issued == False:
                  #add stall state?
                  pass
                  
                        
        #add logic for other instructions                
    

    def fetch(self):
        current_instruction = self.instruction_queue.popleft()
        return current_instruction
    def decode(self):
        pass
        
    # EXECUTE --------------------------------------------------------------
    # Checks the reservation stations for ready instructions, if they are ready, executes them
    # Will simulate cycles needed for each functional unit
    def execute(self):
        for i in self.FP_adder_RS:
            if i.status == True:
                #check if operands are ready
                if i.tag1 == None and i.tag2 == None:
                    #execute instruction
                    result = self.INT_adder(i.value1, i.value2)        
                    #clear RS entry
                    i.del_entry()

        pass
    def write_back(self):
        pass
    
    def FP_adder(self,reg1,reg2):
        pass

    def INT_adder(self,reg1,reg2):
        pass
    def multiplier(self,reg1,reg2):
        pass
    def CBD(self):
        pass
    

def main():
    print("CPU Simulator Main Module")

    loot = Architecture("instructions.txt")
    

    print("Instructions in queue:")
    for instr in loot.instruction_queue:
        print(instr)



if __name__ == "__main__":
	main()
