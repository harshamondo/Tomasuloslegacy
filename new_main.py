from collections import deque

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
				import re
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
      
class Architecture:

    def __init__(self,filename = None):
        self.filename = filename
        
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

        #Initialize instruction register
        self.instruction_queue = deque()
        self.init_instr()

        #initialize RAT and ARF
        #include ways to update ARF based on parameters
        #registers 0-31 and R and 32-64 are F
        self.ARF = [64]
        self.init_ARF()
        self.RAT = [64]
        self.RAT = self.ARF.copy()
        

        #initial same number of rows as instructions in queue for now
        self.ROB = [[None for _ in range (4)] for _ in range(len(self.instruction_queue))]

        #assume individual RS
		#[OP][Dst-Tag][Tag1][Tag1][Val1][Val2]
        #[[None for _ in range (cols)] for _ in range(rows)]
        self.init_config()
        self.int_adder_RS = [[None for _ in range (6)] for _ in range(self.int_adder_num)]
        self.FP_adder_RS = [[None for _ in range (6)] for _ in range(self.FP_adder_num)]
        self.multiplier_RS = [[None for _ in range (6)] for _ in range(self.multiplier_num)]
        self.load_store_RS = [[None for _ in range (6)] for _ in range(self.load_store_num)]


    
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
          pass
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
                  if i == None:
                        #[OP][Dst-Tag][Tag1][Tag1][Val1][Val2]
                        #self.ROB[]

                        self.FP_adder_FU[i]
                        issued = True
                        #write to reservation station
            if issued == False:
                  #add stall state?
                  pass
                  
                        
        #add logic for other instructions                
    

    def fetch(self):
        current_instruction = self.instruction_queue.popleft()
        return current_instruction
    def decode(self):
        pass
        
    def execute(self):
        pass
    def write_back(self):
        pass
    
    def init_ARF():
        pass

def main():
    print("CPU Simulator Main Module")

    loot = Architecture("instructions.txt")
    loot.issue()

    #print("Instructions in queue:")
    #for instr in loot.instruction_queue:
        #print(instr)



if __name__ == "__main__":
	main()
