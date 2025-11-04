from cProfile import label
import re 
from modules.helper import is_arf
from typing import Callable, Any

# Reservation Station Unit - used to represent each entry in a reservation station
# [status][DST_tag][opcode][tag1][tag2][value1][value2]
# will slowly count clock cycles to simulate execution time
# status means the value is ready for execute
from collections import deque
class RS_Unit:
      def __init__(self, DST_tag = None, opcode = None, reg1 = None, reg2 = None, RAT_object = None, ARF_object = None, cycles_issued = None):
            self.opcode = opcode
            self.tag1 = None
            self.tag2 = None
            self.value1 = None
            self.value2 = None

            # Branch offset
            self.branch_offset = None
            # self.immediate = immediate
            self.cycles_left = None
            self.cycle_issued = cycles_issued
            self.DST_value = None
            self.reg1 = reg1
            self.reg2 = reg2
            self.ARF_tag = DST_tag

            self.written_back = False

            self.RAT = RAT_object
            self.ARF = ARF_object

            # We should just assign the value? No need to read
            #self.DST_tag = RAT_object.read(DST_tag)
            self.DST_tag = DST_tag

            if self.RAT.read(self.reg1) != None and self.RAT.read(self.reg1)[:3] == "ROB":
                self.tag1 = self.RAT.read(self.reg1)
            elif self.RAT.read(self.reg1) != None and self.RAT.read(self.reg1)[:3] == "ARF":
                self.value1 = self.ARF.read(self.reg1)

            if self.RAT.read(self.reg2) != None and self.RAT.read(self.reg2)[:3] == "ROB":
                self.tag2 = self.RAT.read(self.reg2)
            elif self.RAT.read(self.reg2) != None and self.RAT.read(self.reg2)[:3] == "ARF":
                self.value2 = self.ARF.read(self.reg2)
      
      def set_branch_offset(self, branch_offset):
            self.branch_offset = branch_offset

      def print_RS(self):
           print("Now printing RS entry:")
           print("[",self.opcode,"]","[",self.DST_tag,"]","[",self.tag1,"]","[",self.tag2,"]","[",self.value1,"]","[",self.value2,"]")
      
      def __str__(self):
            return (f"DST_tag={self.DST_tag}, DST_value={self.DST_value}, opcode={self.opcode}, "
                  f"tag1={self.tag1}, tag2={self.tag2}, value1={self.value1}, value2={self.value2}),"
                  f"cycles_left={self.cycles_left}, cycle_issued={self.cycle_issued}, written_back={self.written_back}"
                  f", branch_offset={self.branch_offset}")

# Reservation Station Table - holds multiple RS_Unit objects
# Type indicates the type of functional unit it is associated with (e.g., Integer Adder, FP Adder, Multiplier, Load/Store)
# number of units indicates how many RS_Unit entries it can hold at maximum
OpFunc = Callable[[Any, 'RS_Unit'], Any]
# OpPair tuple: (operation name, operation function)
OpPair = tuple[str, OpFunc]

# TODO : Neeed to add op tables that has a tuple set of operation name and function to compute
class RS_Table:
      def __init__(self, type = None, num_rs_units = 0, num_FU_units = 0, cycles_per_instruction = 0, op = None):
            self.op = []
            self.table = []
            self.type = type
            self.num_units = num_rs_units
            self.num_FU_units = num_FU_units
            self.cycles_per_instruction = cycles_per_instruction
            self.busy_FU_units = 0
            #store/load RS are queues
            if self.type == "fs_fp_ls":
                  self.table = deque()

      def set_branch_offset(self, index = 0, offset = 0):
            self.table[index].set_branch_offset(offset)

      def check_rs_full(self):
            return len(self.table) >= self.num_units

      def add_op(self, op_pair: OpPair):
            self.op.append(op_pair)

      def add_unit(self, rs_unit):
            self.table.append(rs_unit)

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
      
      def release_all_fu_units(self):
            self.busy_FU_units = 0

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

      # Compute method to execute operation based on opcode saved within the RS_Unit
      def compute(self, rs_unit: RS_Unit) -> Any:
            op_name = rs_unit.opcode
            if op_name is None:
                  raise ValueError("RS_Unit.opcode is None")

            # Linear search over registered OpPairs
            for name, func in self.op:
                  if name == op_name:
                        return func(self, rs_unit) # Call the operation function, passing self and rs_unit to for computation

            available = ", ".join(n for n, _ in self.op) or "<none>"
            raise KeyError(f"Unknown opcode '{op_name}'. Registered ops: [{available}]")

      def length(self):
            count = 0
            for rs_unit in self.table:
                  if rs_unit.cycles_left is None:
                        count += 1
                  elif rs_unit.cycles_left is not None and rs_unit.cycles_left > 0:
                        count += 1
            return count
      
      def print_rs_without_intermediates(self):
            print(f"RS Table Type: {self.type}, Number of Units: {self.num_units}, Busy FU Units: {self.busy_FU_units}")
            for i, rs_unit in enumerate(self.table):
                  if rs_unit.cycles_left is None:
                        print(f"[{i}] Opcode: {rs_unit.opcode}, DST_tag: {rs_unit.DST_tag}, tag1: {rs_unit.tag1}, tag2: {rs_unit.tag2}, value1: {rs_unit.value1}, value2: {rs_unit.value2}, cycles_left: {rs_unit.cycles_left}")
                  elif rs_unit.cycles_left is not None and rs_unit.cycles_left > 0:
                        print(f"[{i}] Opcode: {rs_unit.opcode}, DST_tag: {rs_unit.DST_tag}, tag1: {rs_unit.tag1}, tag2: {rs_unit.tag2}, value1: {rs_unit.value1}, value2: {rs_unit.value2}, cycles_left: {rs_unit.cycles_left}")

# OPERATIONS used by the RS_Table compute method go here. They can use anything in the RS_Unit
# Example operation: Floating Point Addition
# parameters: rs_unit - the RS_Unit containing the operands, immediates, etc.
def rs_fp_add_op(self, rs_unit: RS_Unit):
      return rs_unit.value1 + rs_unit.value2

def rs_fp_sub_op(self, rs_unit: RS_Unit):
      return rs_unit.value1 - rs_unit.value2

def rs_fp_mul_op(self, rs_unit: RS_Unit):
      return rs_unit.value1 * rs_unit.value2

def rs_int_add_op(self, rs_unit: RS_Unit):
      return rs_unit.value1 + rs_unit.value2

def rs_int_sub_op(self, rs_unit: RS_Unit):
      return rs_unit.value1 - rs_unit.value2

def rs_int_addi_op(self, rs_unit: RS_Unit):
      return rs_unit.value1 + rs_unit.value2

def rs_branch(self, rs_unit: RS_Unit):
      return rs_unit.branch_offset
