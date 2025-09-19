class Memory:
	def __init__(self):
		self.data = {}

	def read(self, address):
		return self.data.get(address, None)

	def write(self, address, value):
		self.data[address] = value

	def __str__(self):
		return f"Memory(data={self.data})"
#####################################################################
# main.py
# A CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
#
# The goal is to create a program that simulate's Tomasulo's algorithm with branch prediction and CDR.
#
# Author: Harsh Selokar
#####################################################################

# Define class for Functional Unit
class FU:
	def __init__(self, name="", num_rs=0, cycles_ex=0, cycles_mem=0, instruction=None):
		self.name = name                # Name of the functional unit
		self.num_rs = num_rs            # Number of reservation stations
		self.cycles_ex = cycles_ex      # Execution cycles
		self.cycles_mem = cycles_mem    # Memory access cycles
		self.instruction = instruction  # A single unit can only process one instruction at a time

	def __str__(self):
		return (f"FU(num_rs={self.num_rs}, cycles_ex={self.cycles_ex}, cycles_mem={self.cycles_mem}, "
				f"instruction={self.instruction})")
	
class Instruction:
	def __init__(self, opcode=None, operands=None):
		self.opcode = opcode
		self.operands = operands if operands is not None else []

	def __str__(self):
		return f"Instruction(opcode={self.opcode}, operands={self.operands})"

class Memory:
	def __init__(self):
		self.data = {}

	def read(self, address):
		return self.data.get(address, None)

	def write(self, address, value):
		self.data[address] = value

	def __str__(self):
		return f"Memory(data={self.data})"

def main():
	init()
	# Demonstrate Memory usage
	mem = Memory()
	mem.write(100, 42)
	mem.write(200, 99)
	print(f"Value at address 100: {mem.read(100)}")
	print(f"Value at address 200: {mem.read(200)}")
	print(f"Value at address 300 (unset): {mem.read(300)}")
	print(f"Full memory contents: {mem}")

	# Simulate a clock cycle loop
	clock_cycle = 0
	# Loop until user decides to quit
	while True:
		user_input = input("Press Enter to continue looping, or 'q' to quit: ")
		if user_input.lower() == 'q':
			print("Exiting loop.")
			break
		print(f"Clock cycle: {clock_cycle}")
		clock_cycle += 1

def init():
	print("Initialization complete.")


if __name__ == "__main__":
	main()
