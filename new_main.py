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
        self.instruction_queue = deque()
        self.init_instr()
    
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

    def issue():
        pass
    def fetch():
        pass
    def decode():
        pass
    def execute():
        pass
    def write_back():
        pass


def main():
	print("CPU Simulator Main Module")

	loot = Architecture("instructions.txt")
	print("Instructions in queue:")
	for instr in loot.instruction_queue:
		print(instr)

if __name__ == "__main__":
	main()
