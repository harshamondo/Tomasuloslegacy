from collections import deque
import re
import csv

from modules.instruction import Instruction
from modules.rob import ROB
from modules.rs import RS_Unit, RS_Table, rs_fp_add_op
from modules.arf import ARF
from modules.rat import RAT
from modules.helper import arf_from_csv, is_arf, rat_from_csv
from pathlib import Path
from default_generator.rat_arf_gen import print_file_arf, print_file_rat

# Overall class that determines the architecture of the CPU
class Architecture:
    def __init__(self,filename = None):
        self.filename = filename
        self.config = "config.csv"
        
        # Generate ARF and RAT files if they do not exist
        # Made this to make it easier to reset the ARF and RAT files to different configurations
        if not Path("arf.csv").is_file():
            print_file_arf()

        if not Path("rat.csv").is_file():
            print_file_rat()

        #parse through config.txt and update
        #default values for testing, will update through parsing later
        self.int_adder_FU = 1
        self.FP_adder_FU = 1
        self.multiplier_FU = 1
        self.load_store_FU = 1

        self.int_adder_rs_num = 2
        self.FP_adder_rs_num = 3
        self.multiplier_rs_num = 2
        self.load_store_rs_num = 3

        self.clock = 1

        #parsing code to set the number of functional units and reservation stations will go here
        with open(self.config, newline='') as f:
            reader = csv.DictReader(f)

            # header = next(reader)  # Skip header row
            # print(f"Header : {header}")  # For debugging purposes

            # operations to read configuration
            for row in reader:
                type_name = row.get("Type", "").strip().lower()
                rs_field = row.get("# of rs")
                ex_field = row.get("Cycles in EX")
                mem_field = row.get("Cycles in Mem")
                fu_field = row.get("# of FUs")

                print("Type:", type_name)
                print("# of RS:", rs_field)
                print("Cycles in EX:", ex_field)
                print("Cycles in Mem:", mem_field)
                print("# of FUs:", fu_field)

                if re.search("FP adder", type_name, re.IGNORECASE):
                    self.FP_adder_rs_num = int(rs_field) if rs_field.isdigit() else self.FP_adder_rs_num
                    self.FP_adder_cycles = int(ex_field) if ex_field.isdigit() else self.FP_adder_cycles
                    self.FP_adder_mem_cycles = int(mem_field) if mem_field.isdigit() else self.FP_adder_mem_cycles
                    self.FP_adder_FU = int(fu_field) if fu_field.isdigit() else self.FP_adder_FU             

        print(f"FP Adder RS Num: {self.FP_adder_rs_num}, FP Adder FU: {self.FP_adder_FU}")
        self.fs_fp_add = RS_Table(type="fs_fp_add", num_rs_units=self.FP_adder_rs_num, num_FU_units=self.FP_adder_FU, cycles_per_instruction=self.FP_adder_cycles)
        self.fs_fp_add.add_op( ("Add.d", rs_fp_add_op) )
        self.fs_fp_add.add_op( ("Sub.d", rs_fp_add_op) )  # Placeholder, replace with actual subtraction function!!!

        # TODO : Initialize other RS_Tables for multiplier, integer adder, load/store with respective functions
        self.fs_LS = RS_Table(type="fs_fp_ls", num_rs_units=self.load_store_rs_num, num_FU_units=self.load_store_FU)
        self.fs_mult = RS_Table(type="fs_fp_mult", num_rs_units=self.multiplier_rs_num, num_FU_units=self.multiplier_FU)
        self.fs_int_adder = RS_Table(type="fs_int_adder", num_rs_units=self.int_adder_rs_num, num_FU_units=self.int_adder_FU)

        #Initialize instruction register
        self.instruction_queue = deque()
        self.init_instr()

        #initialize RAT and ARF
        #include ways to update ARF based on parameters
        #registers 0-31 and R and 32-64 are F
        self.ARF = ARF()
        self.RAT = RAT()

        self.ARF = arf_from_csv("arf.csv")
        self.RAT = rat_from_csv("rat.csv")

        #initial same number of rows as instructions in queue for now
        #ROB should be a queue
        self.ROB = ROB()

        self.CDB = deque()

    # Helper functions for ISSUE
    # Fetch instructions from a file
    def parse(self):
            # Reads instructions from a file and returns them as a list of (opcode, operands) tuples.
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
        # Fetches instructions from instruction_list, decodes them into Instruction objects, and puts them into the global instruction_queue.
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


    # ISSUE --------------------------------------------------------------
    def init_instr(self):
        instructions_list = self.parse()
        self.gen_instructions(instructions_list)

          #debug
          #print(len(self.FP_adder_RS))
    def init_ARF_RAT(self):
        #add logic here to initialize ARF to values
        #add logic here to initialize ARF to values
        for i in range(1,33):
             self.ARF.write("R" + str(i),0)
             self.RAT.write("R" + str(i),"ARF" + str(i))
        for i in range(1,33):
             self.ARF.write("F" + str(i),0)
             self.RAT.write("F" + str(i),"ARF" + str(i+32))

    def issue(self):
        #add instructions into the RS if not full
        #think about how we are going to stall
        #ask prof if we need to have official states like fetch and decode since our instruction class already handles fetch+decode
        current_instruction = self.fetch()
        
        if current_instruction is not None:
            print("[ISSUE] No instruction to issue this cycle.")
            check = current_instruction.opcode
            issued = False
            current_ROB = None
    
                
            #add to ROB and RAT regardless if we must wait for RS space
            current_ROB = "ROB" + str(self.ROB.getEntries()+1)
            self.ROB.write(current_ROB,current_instruction.dest,None,False)
            self.RAT.write(current_instruction.dest,current_ROB)

            #check for space in RS
            #have to add tables for mult, and ld/store
            
            if (check == "Add.d" or check == "Sub.d") and len(self.fs_fp_add.table) < self.FP_adder_rs_num:
                self.fs_fp_add.table.append(RS_Unit(current_instruction.dest,current_instruction.opcode,current_instruction.src1,current_instruction.src2,self.RAT,self.ARF,self.clock))
            
            elif (check == "Add" or check == "Sub" or check == "Addi") and len(self.fs_int_adder.table) < self.int_adder_rs_num:
                
                if check == "Addi":
                    self.fs_int_adder.table.append(RS_Unit(current_instruction.dest,current_instruction.opcode,current_instruction.src1,current_instruction.immediate,self.RAT,self.ARF))
                else:
                    self.fs_int_adder.table.append(RS_Unit(current_instruction.dest,current_instruction.opcode,current_instruction.src1,current_instruction.src2,self.RAT,self.ARF))

            elif (check == "Mult.d") and len(self.fs_mult.table) < self.multiplier_rs_num:
                self.fs_mult.table.append(RS_Unit(current_instruction.dest,current_instruction.opcode,current_instruction.src1,current_instruction.src2,self.RAT,self.ARF))
            
            elif (check == "SD" or check == "LD") and len(self.fs_LS.table) < self.load_store_rs_num:
                print("added ld")
                self.fs_LS.table.append(RS_Unit(current_instruction.dest,current_instruction.opcode,current_instruction.offset, current_instruction.src1,self.RAT,self.ARF))
            else:
                #stall due to full RS
                #if no conditions are satisified, it must mean the targeted RS is full
                pass
                

    def fetch(self):
        if len(self.instruction_queue) == 0:
            return None
        current_instruction = self.instruction_queue.popleft()
        return current_instruction
    
    def decode(self):
        pass
        
    # EXECUTE --------------------------------------------------------------
    # Checks the reservation stations for ready instructions, if they are ready, executes them
    # Will simulate cycles needed for each functional unit

    # Execute helper functions
    def parse_rs_table(self, rs_table=None):
        for rs_unit in rs_table.table:
            # Skip empty slots (if your RS uses opcode)
            if getattr(rs_unit, "opcode", None) is None:
                continue

            # General execution logic for RS units
            if rs_table.check_rs_full() is False:
                # Start execution if operands ready, not already executing, and FU available
                if (
                    rs_unit.value1 is not None
                    and rs_unit.value2 is not None
                    and rs_unit.cycles_left is None
                    # TODO : Pipelined CPU - check for available FU units
                    and rs_table.busy_FU_units < rs_table.num_FU_units 
                ):
                    print(f"[EXECUTE] Starting execution of {rs_unit.opcode} for "f"destination {rs_unit.DST_tag} with values {rs_unit.value1} and {rs_unit.value2}")
                    rs_unit.cycles_left = rs_table.cycles_per_instruction
                    print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")
                    rs_table.use_fu_unit()

                # Decrement remaining cycles if currently executing
                elif rs_unit.cycles_left is not None and rs_unit.cycles_left > 0:
                    rs_unit.cycles_left -= 1
                    print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")

                # Finish when execution cycles reach 0
                elif rs_unit.cycles_left == 0:
                    rs_unit.DST_value = rs_table.compute(rs_unit)
                    rs_unit.value1 = None
                    rs_unit.value2 = None
                    print(f"[EXECUTE] Completed execution of {rs_unit.opcode} for "
                        f"destination {rs_unit.DST_tag} with result {rs_unit.DST_value}")
                    rs_table.release_fu_unit()

    def execute(self):
        # Execute logic for Floating Point Adder/Subtracter RS
        self.parse_rs_table(self.fs_fp_add)

        #
        # TODO: Add execution logic for other functional units
        #

    def write_back(self):
        print("[WRITE BACK] Checking RS Units for write back...")

        # First handle the outputs from the reservation stations
        for rs_unit in self.fs_fp_add.table:
            print(f"[WRITE BACK] RS Unit: {rs_unit}")
            # Check if execution is complete and result is ready
            if rs_unit.cycles_left == 0 and rs_unit.DST_value is not None:
                # Write back result to ARF and update ROB
                result = rs_unit.DST_value
                #this needs to point to F1,F2,F3...etc
                dest_reg = rs_unit.ARF_tag
                CDB_res_reg = rs_unit.DST_tag

                # Temporary print statement for debugging
                print(f"[WRITE BACK] Writing back result {result} to {dest_reg}")
                #
                # TODO : Implement CDB arbitration logic
                #
                self.CDB.append((dest_reg, result))

                # Remove RS entry
                self.fs_fp_add.table.remove(rs_unit)
                print(f"[WRITE BACK] Removed RS Unit {rs_unit} after write back.")
                break # Only handle one per requirements

        # Next, handle the Common Data Bus (CDB) updates
        if len(self.CDB) > 0:
            dest_reg, result = self.CDB.pop()
            print(f"[WRITE BACK] CDB updating {dest_reg} with value {result}")
            # writing to the ARF is done by the commit stage
            for rs_unit in self.fs_fp_add.table:
                if rs_unit.tag1 == CDB_res_reg:
                    rs_unit.value1 = result
                    print(f"[WRITE BACK] Updated RS Unit {rs_unit} value1 with {result}")
                if rs_unit.tag2 == CDB_res_reg:
                    rs_unit.value2 = result
                    print(f"[WRITE BACK] Updated RS Unit {rs_unit} value2 with {result}")

            # Update ROB entry
            # not updating
            # dest reg should be F1
            rob_entry = self.RAT.read(dest_reg)
            print("NOW PRINTING RELEVANT VALUES:")
            print(dest_reg)
            print(self.RAT.read(dest_reg))
            if rob_entry and rob_entry.startswith("ROB"):
                self.ROB.update(rob_entry, result)
    
    # COMMIT --------------------------------------------------------------
    # TODO : Implement commit logic to use head and tail logic as per ROB design in class
    def commit(self):
        if self.ROB.getEntries() > 0:
            for i in range(1, self.ROB.max_entries + 1):
                rob_entry_key = "ROB" + str(i)
                rob_entry = self.ROB.read(rob_entry_key)

                if rob_entry is not None:
                    alias, value, done = rob_entry
                    if done == False and value is not None:
                        print(f"[COMMIT] Committing {value} to {alias} from {rob_entry_key}")
                        done = True
                        self.ARF.write(alias, value)
                        if self.RAT.read(alias) == rob_entry_key:
                            self.RAT.write(alias, "ARF" + str(int(alias[1:]) + 32))  
                        # Clear the ROB entry
                        self.ROB.clear(rob_entry_key)
                        # Only commit one instruction per cycle

                        #need to repoint the RAT table to the ARF

                        break  