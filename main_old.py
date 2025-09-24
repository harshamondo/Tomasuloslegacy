import csv

def parse_config(filename):
	"""
	Parses a comma-delimited config file and returns a list of dictionaries.
	"""
	config_data = []
	with open(filename, newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			config_data.append(row)
	print("Parsed config data:")
	for entry in config_data:
		print(entry)
	return config_data
from collections import deque

#####################################################################
# main.py
# A CPU simulator main module
# This program is an assignment for Computer Architecture 1 @ University of Pittsburgh
#
# The goal is to create a program that simulate's Tomasulo's algorithm with branch prediction and CDR.
#
# Author: Harsh Selokar
#####################################################################

# Instruction queue to hold instructions before issuing
instruction_queue = deque()

def issue(instruction, fu):
	"""
	Issues an instruction to a functional unit (FU).
	This is a placeholder function. Add logic as needed.
	"""
	print(f"Issuing {instruction} to {fu}")

# Define class for Functional Unit
class FU:
	def __init__(self, name="", num_rs=0, current_cycle_ex=0, max_cycles_ex=0, current_cycle_mem=0, max_cycles_mem=0, current_instruction=None):
		self.name = name								# Name of the functional unit
		self.num_rs = num_rs							# Number of reservation stations
		self.current_cycle_ex = current_cycle_ex		# Current execution cycles
		self.max_cycles_ex = max_cycles_ex				# Maximum execution cycles
		self.current_cycle_mem = current_cycle_mem		# Current memory access cycles
		self.max_cycles_mem = max_cycles_mem			# Maximum memory access cycles
		self.current_instruction = current_instruction	# A single unit can only process one instruction at a time

	def remove_execution_cycle(self):
		if self.current_cycle_ex > 0:
			self.current_cycle_ex -= 1

	def __str__(self):
		return (f"FU(num_rs={self.num_rs}, current_cycle_ex={self.current_cycle_ex}, max_cycles_ex={self.max_cycles_ex}, current_cycle_mem={self.current_cycle_mem}, "
				f"max_cycles_mem={self.max_cycles_mem}, instruction={self.instruction})")

class Instruction:
	def __init__(self, opcode=None, operands=None):
		self.opcode = opcode
		self.operands = operands if operands is not None else []

	def __str__(self):
		return f"Instruction(opcode={self.opcode}, operands={self.operands})"

# Define class for Memory
# Memory can hold values at different addresses
class Memory:
	def __init__(self):
		self.data = {}

	def read(self, address):
		return self.data.get(address, None)

	def write(self, address, value):
		self.data[address] = value

	def __str__(self):
		return f"Memory(data={self.data})"

# Define class for Register
# Each register can hold a value and a tag (for tracking dependencies)
# Supports floating point values or integers
class RegisterArray:
	def __init__(self):
		self.data = {}

	def read(self, address):
		return self.data.get(address, None)

	def write(self, address, value):
		self.data[address] = value

	def __str__(self):
		return f"Register(data={self.data})"

class CDB:
	def __init__(self):
		self.buffer = []  # Holds extra calculated values from FUs

	def add_value(self, value):
		self.buffer.append(value)

	def get_values(self):
		return self.buffer

	def clear(self):
		self.buffer.clear()

	def __str__(self):
		return f"CDB(buffer={self.buffer})"

def main():
	init()
	
	# Demonstrate Memory usage
	# Create a memory instance and perform some read/write operations
	# Memory reads with no write value are set to '0'
	# mem = Memory()
	# mem.write(100, 42)
	# mem.write(200, 99)
	# print(f"Value at address 100: {mem.read(100)}")
	# print(f"Value at address 200: {mem.read(200)}")
	# print(f"Value at address 300 (unset): {mem.read(300)}")
	# print(f"Full memory contents: {mem}")

	# FU formating : (name, num_rs, current_cycle_ex, max_cycles_ex, current_cycle_mem, max_cycles_mem, instruction)
	Adder = FU(name="Adder", num_rs=3, max_cycles_ex=2)

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
	parse_config("config.txt")
	print("Initialization complete.")


if __name__ == "__main__":
	init()
	# Test config file parsing
	parse_config("config.txt")
	# Demonstrate Memory usage
	mem = Memory()
	mem.write(100, 42)
	mem.write(200, 99)
	print(f"Value at address 100: {mem.read(100)}")
	print(f"Value at address 200: {mem.read(200)}")
	print(f"Value at address 300 (unset): {mem.read(300)}")
	print(f"Full memory contents: {mem}")
