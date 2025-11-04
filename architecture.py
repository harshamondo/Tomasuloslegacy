from collections import deque
import re
import csv

from modules.instruction import Instruction
from modules.rob import ROB
from modules.rs import RS_Unit, RS_Table, rs_fp_add_op, rs_fp_sub_op, rs_fp_mul_op, rs_int_add_op, rs_int_sub_op, rs_int_addi_op, rs_branch

from modules.arf import ARF
from modules.rat import RAT
from modules.helper import arf_from_csv, is_arf, rat_from_csv, init_ARF_RAT
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

                if re.search("Integer adder", type_name, re.IGNORECASE):
                    self.int_adder_rs_num = int(rs_field) if rs_field.isdigit() else self.int_adder_rs_num
                    self.int_adder_cycles = int(ex_field) if ex_field.isdigit() else self.int_adder_cycles
                    self.int_adder_mem_cycles = int(mem_field) if mem_field.isdigit() else self.int_adder_mem_cycles
                    self.int_adder_FU = int(fu_field) if fu_field.isdigit() else self.int_adder_FU
            
                if re.search("FP multiplier", type_name, re.IGNORECASE):
                    self.multiplier_rs_num = int(rs_field) if rs_field.isdigit() else self.multiplier_rs_num
                    self.multiplier_cycles = int(ex_field) if ex_field.isdigit() else self.multiplier_cycles
                    self.multiplier_mem_cycles = int(mem_field) if mem_field.isdigit() else self.multiplier_mem_cycles
                    self.multiplier_FU = int(fu_field) if fu_field.isdigit() else self.multiplier_FU

                if re.search("Load/store unit", type_name, re.IGNORECASE):
                    self.load_store_rs_num = int(rs_field) if rs_field.isdigit() else self.load_store_rs_num
                    self.load_store_cycles = int(ex_field) if ex_field.isdigit() else self.load_store_cycles
                    self.load_store_mem_cycles = int(mem_field) if mem_field.isdigit() else self.load_store_mem_cycles
                    self.load_store_FU = int(fu_field) if fu_field.isdigit() else self.load_store_FU

        print(f"FP Adder RS Num: {self.FP_adder_rs_num}, FP Adder FU: {self.FP_adder_FU}, Cycles: {self.FP_adder_cycles}, Mem Cycles: {self.FP_adder_mem_cycles}")
        self.fs_fp_add = RS_Table(type="fs_fp_add", num_rs_units=self.FP_adder_rs_num, num_FU_units=self.FP_adder_FU, cycles_per_instruction=self.FP_adder_cycles)
        self.fs_fp_add.add_op( ("Add.d", rs_fp_add_op) )
        self.fs_fp_add.add_op( ("Sub.d", rs_fp_sub_op) )

        # TODO : Initialize other RS_Tables for multiplier, integer adder, load/store with respective functions
        print(f"Load/Store RS Num: {self.load_store_rs_num}, Load/Store FU: {self.load_store_FU}, Cycles: {self.load_store_cycles}, Mem Cycles: {self.load_store_mem_cycles}")
        self.fs_LS = RS_Table(type="fs_fp_ls", num_rs_units=self.load_store_rs_num, num_FU_units=self.load_store_FU, cycles_per_instruction=self.load_store_cycles)

        print(f"Multiplier RS Num: {self.multiplier_rs_num}, Multiplier FU: {self.multiplier_FU}, Cycles: {self.multiplier_cycles}, Mem Cycles: {self.multiplier_mem_cycles}")
        self.fs_mult = RS_Table(type="fs_fp_mult", num_rs_units=self.multiplier_rs_num, num_FU_units=self.multiplier_FU, cycles_per_instruction=self.multiplier_cycles)
        self.fs_mult.add_op( ("Mult.d", rs_fp_mul_op) )  # Placeholder, replace with actual multiplication function!!!

        print(f"Integer Adder RS Num: {self.int_adder_rs_num}, Integer Adder FU: {self.int_adder_FU}, Cycles: {self.int_adder_cycles}, Mem Cycles: {self.int_adder_mem_cycles}")
        self.fs_int_adder = RS_Table(type="fs_int_adder", num_rs_units=self.int_adder_rs_num, num_FU_units=self.int_adder_FU, cycles_per_instruction=self.int_adder_cycles)
        self.fs_int_adder.add_op( ("Add", rs_int_add_op) )
        self.fs_int_adder.add_op( ("Sub", rs_int_sub_op) )
        self.fs_int_adder.add_op( ("Addi", rs_int_addi_op) )
        
        # Execution step is only 1 step, there should not be extra rs_units and there isn't really functional units for this branch
        self.fs_branch = RS_Table(type="fs_branch", num_rs_units=1, num_FU_units=1, cycles_per_instruction=1)
        self.fs_branch.add_op( ("Bne", rs_branch))
        self.fs_branch.add_op( ("Beq", rs_branch))

        self.all_rs_tables = [
            self.fs_fp_add,
            self.fs_int_adder,
            self.fs_mult,
            self.fs_LS,
            self.fs_branch
        ]

        #Initialize instruction register
        self.instruction_queue = deque()
        self.init_instr()

        #Setup PC + branch instruction map
        # Go through the instruction q 
        self.instr_addresses = []
        for index, instruction in enumerate(self.instruction_queue):
        # We are starting the PC at 0x0 to begin. Each address is 0x4 off of the base
            pc = 0x0 + index * 0x4
            self.instr_addresses.append((pc, instruction))

        for pc, instruction in self.instr_addresses:
            print(f"[INIT] PC=0x{pc:04X} Instruction={instruction}")

        #initialize RAT and ARF
        #include ways to update ARF based on parameters
        #registers 0-31 and R and 32-64 are F
        self.ARF = ARF()
        self.RAT = RAT()

        # Pull from the ARF and RAT .csv
        self.ARF = arf_from_csv("arf.csv")
        self.RAT = rat_from_csv("rat.csv")

        #initial same number of rows as instructions in queue for now
        #ROB should be a queue
        self.ROB = ROB()

        # Queue for the CDB
        self.CDB = deque()

        # Halt
        self.halt = False

    # Helper functions to initialize the architecture

    # Helper functions to get the functions from the txt file and get them read for issue
    def init_instr(self):
            instructions_list = self.parse()
            self.gen_instructions(instructions_list)

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
            # Fetches instructions, decodes to Instruction objects, and enqueues them.
        while instruction_list:
            instr = instruction_list.pop(0)

            if isinstance(instr, tuple):
                opcode, operands = instr
            elif isinstance(instr, str):
                parts = instr.replace(',', '').split()
                if not parts:
                    continue
                opcode, operands = parts[0], parts[1:]
            else:
                continue

            # Build the Instruction first
            instr = Instruction(opcode, operands)

            # Branch remap: Beq/Bnz dest=None, src1=op0, src2=op1, offset=op2, immediate=None
            if opcode.lower() in ("beq", "bnz"):
                if len(operands) != 3:
                    raise ValueError(f"{opcode} expects 3 operands, got {len(operands)}: {operands}")
                instr.dest = None
                instr.src1 = operands[0]
                instr.src2 = operands[1]
                instr.offset = operands[2]
                instr.immediate = None

            self.instruction_queue.append(instr)

    # ISSUE --------------------------------------------------------------
    def fetch(self):
        if len(self.instruction_queue) == 0:
            return None
        current_instruction = self.instruction_queue.popleft()
        return current_instruction

    def issue(self):
        #add instructions into the RS if not full
        #think about how we are going to stall
        #ask prof if we need to have official states like fetch and decode since our instruction class already handles fetch+decode
        current_instruction = None
        if len(self.instruction_queue) != 0:
            # peak the current instruction
            current_instruction = self.instruction_queue[0]
            type_of_instr = current_instruction.opcode
            # printing size of the all RS tables before checking for space
            print(f"[ISSUE] RS Table Sizes before issue:")
            print(f"[ISSUE] FP Adder RS Size: {self.fs_fp_add.length()}")
            print(f"[ISSUE] Int Adder RS Size: {self.fs_int_adder.length()}")
            print(f"[ISSUE] Multiplier RS Size: {self.fs_mult.length()}")
            print(f"[ISSUE] Load/Store RS Size: {self.fs_LS.length()}")
            # print what's in the RS tables
            for rs_table in self.all_rs_tables:
                print(f"[ISSUE] RS Table {rs_table.type} contents before issue:")
                for rs_unit in rs_table.table:
                    print(f"    {rs_unit}")

            # Checks if the reservations stations after full! No instruction 
            if (type_of_instr == "Add.d" or type_of_instr == "Sub.d"):
                if self.fs_fp_add.length() >= self.FP_adder_rs_num:
                    current_instruction = None
            elif (type_of_instr == "Add" or type_of_instr == "Sub" or type_of_instr == "Addi"):
                if self.fs_int_adder.length() >= self.int_adder_rs_num:
                    current_instruction = None
            elif (type_of_instr == "Mult.d"):
                if self.fs_mult.length() >= self.multiplier_rs_num:
                    current_instruction = None
            elif (type_of_instr == "SD" or type_of_instr == "LD"):
                if self.fs_LS.length() >= self.load_store_rs_num:
                    current_instruction = None
            elif (type_of_instr == "NOP"):
                self.fetch()
                current_instruction = None

        # NOP is untested
        if current_instruction is not None and self.halt is not True:
            current_instruction = self.fetch()
            # DEBUG PRINTS
            #print(f"[ISSUE] int_adder_rs_num: {self.int_adder_rs_num}, fs_int_adder.table size: {self.fs_fp_add.length()}")
            for rs_table in self.all_rs_tables:
                rs_table.print_rs_without_intermediates()
            print(f"[ISSUE] Issuing instruction: {current_instruction}")

            check = current_instruction.opcode
            # issued = False
            current_ROB = None
                
            #add to ROB and RAT regardless if we must wait for RS space
            #TODO  the register rename doesn't seem to account for the size of the ROB, absolutely needs to be fixed!
            #TODO  we write to the ROB(X) and the search to see if the value exists. this is poor implementation
            current_ROB = "ROB" + str(self.ROB.getEntries()+1)

            #check for space in RS
            #have to add tables for mult, and ld/store
            print(f"[ISSUE] Check: {check}")
            if (check == "Add.d" or check == "Sub.d") and self.fs_fp_add.length() < self.FP_adder_rs_num:
                self.fs_fp_add.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.src2, self.RAT, self.ARF))

            elif (check == "Add" or check == "Sub" or check == "Addi") and self.fs_int_adder.length() < self.int_adder_rs_num:
                print("[ISSUE] ------")
                if check == "Addi":
                    rs = RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.immediate, self.RAT, self.ARF)
                    # immediate value goes to value2 without tag needed
                    rs.value2 = int(current_instruction.immediate)
                    # print("[ISSUE] Added Addi RS Unit with immediate value:", rs.value2)
                    # print("[ISSUE] RS Unit details:", rs)
                    self.fs_int_adder.table.append(rs)
                else:
                    self.fs_int_adder.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.src2, self.RAT, self.ARF))

            elif (check == "Mult.d") and self.fs_mult.length() < self.multiplier_rs_num:
                self.fs_mult.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.src2, self.RAT, self.ARF))

            elif (check == "Sd" or check == "Ld") and self.fs_LS.length() < self.load_store_rs_num:
                print("[ISSUE] Added ld or sd")
                self.fs_LS.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.offset, current_instruction.src1, self.RAT, self.ARF))
            elif (check == "Beq" or check == "Bne"):
                # Ignore the next fetch until the Bne is done
                halt = True

                # Branch predication will be here
                self.fs_branch.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.src2, self.RAT, self.ARF))
                self.fs_branch.set_branch_offset(0, current_instruction.offset)

                # branch does not stack at the moment!!
                print(f"[DEBUG] Testing if branch gets to here {self.fs_branch}")
            else:
                #stall due to full RS
                #if no conditions are satisified, it must mean the targeted RS is full
                pass

            # We will also be read naming but we shouldn't read until we read from the right registers
            self.ROB.write(current_ROB,current_instruction.dest, None, False)
            self.RAT.write(current_instruction.dest, current_ROB)

    # EXECUTE --------------------------------------------------------------
    # Checks the reservation stations for ready instructions, if they are ready, executes them
    # Will simulate cycles needed for each functional unit

    # Execute helper functions
    def parse_rs_table(self, rs_table: RS_Table):
        print(f"[EXECUTE] Parsing RS Table: {rs_table.type}")
        for rs_unit in rs_table.table:
            # Skip empty slots (if your RS uses opcode)
            print(f"[EXECUTE] RS Table {rs_table.type}")
            print(f"[EXECUTE] RS Unit {rs_unit}")

            # print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")
            # if getattr(rs_unit, "opcode", None) is None:
            #     continue
            # General execution logic for RS units
            # if rs_table.check_rs_full() is False:
            # Start execution if operands ready, not already executing, and FU available
            if (
                rs_unit.value1 is not None
                and rs_unit.value2 is not None
                and rs_unit.cycles_left is None
                # TODO : Test Pipelined CPU - check for available FU units
                and rs_table.busy_FU_units <= rs_table.num_FU_units 
            ):
                print(f"[EXECUTE] Starting execution of {rs_unit.opcode} for "f"destination {rs_unit.DST_tag} with values {rs_unit.value1} and {rs_unit.value2} for {rs_table.cycles_per_instruction} cycles.")
                rs_unit.cycles_left = rs_table.cycles_per_instruction

                if rs_unit.written_back == True:
                    rs_unit.written_back = False
                    rs_unit.cycles_left -= 1

                print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")
                rs_table.use_fu_unit()

            # Decrement remaining cycles if currently executing
            elif rs_unit.cycles_left is not None and rs_unit.cycles_left > 1:
                rs_unit.cycles_left -= 1
                print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")
            elif rs_unit.cycles_left == 1:
                rs_unit.cycles_left -= 1
                print(f"[EXECUTE] Completed execution of {rs_unit.opcode} for destination {rs_unit.DST_tag} with result {rs_table.compute(rs_unit)}")
            # complete execution if cycles left is 0
            elif rs_unit.cycles_left == 0:
                rs_unit.DST_value = rs_table.compute(rs_unit)
                print(f"[EXECUTE] RS Unit {rs_unit} has moved to WB with execution with result {rs_unit.DST_value}.")
                # could be buffered but we are just leaving this for write back stage to handle
                # rs_unit.value1 = None
                # rs_unit.value2 = None
                # print(f"[EXECUTE] Completed execution of {rs_unit.opcode} for destination {rs_unit.DST_tag} with result {rs_unit.DST_value}")

        # Release all FU units at the end of execution phase since they are pipelined and get freed up for next cycle
        rs_table.release_all_fu_units()

    def execute(self):
        # Execute logic for Floating Point Adder/Subtracter RS
        for rs_table in self.all_rs_tables:
            self.parse_rs_table(rs_table)

    # WRITE BACK --------------------------------------------------------------
    # Helper function for write back
    def write_back(self):
        print("[WRITE BACK] Checking RS Units for write back...")

        # First handle the outputs from the reservation stations
        for rs_table in self.all_rs_tables:
            print(f"[WRITE BACK] Processing RS Table: {rs_table.type}")
            for rs_unit in rs_table.table:
                print(f"[WRITE BACK] RS Unit: {rs_unit}")
                # Check if execution is complete and result is ready
                if rs_unit.cycles_left == 0 and rs_unit.DST_value is not None:
                    # Write back result to ARF and update ROB
                    result = rs_unit.DST_value
                    #this needs to point to F1,F2,F3...etc
                    arf_reg = rs_unit.ARF_tag
                    CDB_res_reg = rs_unit.DST_tag

                    # Temporary print statement for debugging
                    print(f"[WRITE BACK] Writing back result {result} to {arf_reg}, getting ready to update ROB entry for {CDB_res_reg}")
                    #
                    # TODO : Implement CDB arbitration logic
                    #
                    self.CDB.append((CDB_res_reg, arf_reg, result))

                    # Remove RS entry
                    rs_table.table.remove(rs_unit)
                    print(f"[WRITE BACK] Removed RS Unit {rs_unit} after write back.")
                    break # Only handle one per requirements
                break

        # Next, handle the Common Data Bus (CDB) updates
        if len(self.CDB) > 0:
            CDB_res_reg, arf_reg, result = self.CDB.pop()
            print(f"[WRITE BACK] CDB updating ARF:{arf_reg} and CDB_res:{CDB_res_reg} with value {result}")
            # writing to the ARF is done by the commit stage
            # check all the tables
            for rs_table in self.all_rs_tables:
                for rs_unit in rs_table.table:
                    if rs_unit.tag1 == CDB_res_reg:
                        print(f"[WRITE BACK] Found one in {rs_table.type}")
                        rs_unit.value1 = result
                        print(f"[WRITE BACK] Updated RS Unit {rs_unit} value1 with {result}")
                    if rs_unit.tag2 == CDB_res_reg:
                        print(f"[WRITE BACK] Found one in {rs_table.type}")
                        rs_unit.value2 = result
                        print(f"[WRITE BACK] Updated RS Unit {rs_unit} value2 with {result}")

                    # Should be able to remove this
                    if rs_unit.value1 is not None and rs_unit.value2 is not None:
                        print(f"[WRITE BACK] RS Unit {rs_unit} now has both operands ready: value1={rs_unit.value1}, value2={rs_unit.value2}")
                        rs_unit.written_back = True

            # Update ROB entry
            print(f"[WRITE BACK] Completed write back for {arf_reg} with value {result}.")
            self.ROB.update(CDB_res_reg, result)
            print(f"[WRITE BACK] Updated ROB entry for {CDB_res_reg} with value {result}.")

        print(f"[WRITE BACK] Current ROB state: {self.ROB}")
    
    # COMMIT --------------------------------------------------------------
    # TODO : Implement commit logic to use head and tail logic as per ROB design in class
    def commit(self):
        if self.ROB.getEntries() > 0:
            for i in range(1, self.ROB.max_entries + 1):
                rob_entry_key = "ROB" + str(i)
                rob_entry = self.ROB.read(rob_entry_key)

                if rob_entry is not None:
                    alias, value, done = rob_entry
                    print(f"[COMMIT] Checking ROB entry {rob_entry_key}: alias={alias}, value={value}, done={done}")

                    # Extra cycle wait if instruction not done
                    if done == False and value is not None:
                        print(f"[COMMIT] Waiting 1 cycle to commit {value} to {alias} from {rob_entry_key}")
                        self.ROB.update_done(rob_entry_key, True)
                        
                    if done == True:
                        print(f"[COMMIT] Committing {value} to {alias} from {rob_entry_key}")
                        self.ARF.write(alias, value)

                        # Update RAT to point back to ARF if it still points to this ROB entry
                        if self.RAT.read(alias) == rob_entry_key:
                            self.RAT.write(alias, "ARF" + str(int(alias[1:]) + 32))  
                        # Clear the ROB entry
                        self.ROB.clear(rob_entry_key)
                        # Only commit one instruction per cycle
                        break  