from collections import deque
import re
import csv

from modules.instruction import Instruction
from modules.rob import ROB
from modules.rs import RS_Unit, RS_Table, rs_fp_add_op, rs_fp_sub_op, rs_fp_mul_op, rs_int_add_op, rs_int_sub_op, rs_int_addi_op, rs_branch_bne, rs_branch_beq

from modules.arf import ARF
from modules.rat import RAT
from modules.helper import arf_from_csv, is_arf, rat_from_csv, init_ARF_RAT, _to_int_addr
from pathlib import Path
from default_generator.rat_arf_gen import print_file_arf, print_file_rat
from modules.btb import BTB

# Overall class that determines the architecture of the CPU
class Architecture:
    # Stupid helper functions to force PC into an int, python let me declare my variables you menace!
    @property
    def PC(self) -> int:
        return self._pc

    @PC.setter
    def PC(self, value):
        self._pc = _to_int_addr(value)  # coercion & guarantee

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
        self.act_PC = 0x0
        self.PC = 0x0

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
        self.fs_LS.add_op(("Add",rs_int_add_op))
        
        #there are two cycles, one for calculating address (adder), and ld's time spent in memory
        print(f"Multiplier RS Num: {self.multiplier_rs_num}, Multiplier FU: {self.multiplier_FU}, Cycles: {self.multiplier_cycles}, Mem Cycles: {self.multiplier_mem_cycles}")
        self.fs_mult = RS_Table(type="fs_fp_mult", num_rs_units=self.multiplier_rs_num, num_FU_units=self.multiplier_FU, cycles_per_instruction=self.multiplier_cycles)
        self.fs_mult.add_op( ("Mult.d", rs_fp_mul_op) )  # Placeholder, replace with actual multiplication function!!!

        print(f"Integer Adder RS Num: {self.int_adder_rs_num}, Integer Adder FU: {self.int_adder_FU}, Cycles: {self.int_adder_cycles}, Mem Cycles: {self.int_adder_mem_cycles}")
        self.fs_int_adder = RS_Table(type="fs_int_adder", num_rs_units=self.int_adder_rs_num, num_FU_units=self.int_adder_FU, cycles_per_instruction=self.int_adder_cycles)
        self.fs_int_adder.add_op( ("Add", rs_int_add_op) )
        self.fs_int_adder.add_op( ("Sub", rs_int_sub_op) )
        self.fs_int_adder.add_op( ("Addi", rs_int_addi_op) )
        
        # Execution step is only 1 step, there should not be extra rs_units and there isn't really functional units for this branch
        self.fs_branch = RS_Table(type="fs_branch", num_rs_units=1, num_FU_units=1, cycles_per_instruction=0)
        self.fs_branch.add_op( ("Bne", rs_branch_bne))
        self.fs_branch.add_op( ("Beq", rs_branch_beq))

        self.all_rs_tables = [
            self.fs_fp_add,
            self.fs_int_adder,
            self.fs_mult,
            self.fs_LS,
            self.fs_branch
        ]

        self.instruction_pointer = 0
        self.instructions_in_flight = []
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

        self.pc_to_instr = dict(self.instr_addresses)
        self.max_pc = (len(self.instr_addresses) - 1) * 0x4 if self.instr_addresses else -1

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
        self.halt = False # just for branch solo
        self.BTB = BTB()

        # Pause for reset
        self.pause_for_reset = False

        # Create all the savepoint datastructures here
        self.branch_CDB = None
        self.branch_ROB = None
        self.branch_ARF = None
        self.branch_RAT = None
        self.branch_all_rs_tables = None

        # self.branch_fs_fp_add = None


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
            if opcode.lower() in ("beq", "bne"):
                if len(operands) != 3:
                    raise ValueError(f"{opcode} expects 3 operands, got {len(operands)}: {operands}")
                instr.dest = None
                instr.src1 = operands[0]
                instr.src2 = operands[1]
                instr.offset = operands[2]
                instr.immediate = None

            self.instruction_queue.append(instr)
            self.instructions_in_flight.append(instr)

    # ISSUE --------------------------------------------------------------
    def fetch(self):
        if not self.has_next():
            return None # don't fetch out of bounds
        instr = self.pc_to_instr.get(self.PC)
        if instr is None:
            return None
        self.PC += 0x4
        self.act_PC = self.PC-0x4 # this is the actual PC during the code execution
        return instr

    def has_next(self):
        return int(self.PC <= self.max_pc)

    def issue(self):
        #add instructions into the RS if not full
        #think about how we are going to stall
        #ask prof if we need to have official states like fetch and decode since our instruction class already handles fetch+decode
        current_instruction = None
        if self.halt or not self.has_next():
            return
        
        current_instruction = self.pc_to_instr.get(self.PC)
        if current_instruction is None:
            # PC past end nothing to issue
            return

        # peak the current instruction
        #current_instruction = self.instruction_queue[0]
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

            # Grab the opcode
            check = current_instruction.opcode
            current_ROB = None
            
            current_instruction.issue_cycle = self.clock
            #add to ROB and RAT regardless if we must wait for RS space
            #TODO  the register rename doesn't seem to account for the size of the ROB, absolutely needs to be fixed!
            #TODO  we write to the ROB(X) and the search to see if the value exists. this is poor implementation
            current_ROB = "ROB" + str(self.ROB.getEntries()+1)
            current_instruction.rob_tag = current_ROB
            #check for space in RS
            #have to add tables for mult, and ld/store
            print(f"[ISSUE] Check: {check}")
            if (check == "Add.d" or check == "Sub.d") and self.fs_fp_add.length() < self.FP_adder_rs_num:
                self.fs_fp_add.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.src2, self.RAT, self.ARF,self.clock))

            elif (check == "Add" or check == "Sub" or check == "Addi") and self.fs_int_adder.length() < self.int_adder_rs_num:
                print("[ISSUE] ------")
                if check == "Addi":
                    rs = RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.immediate, self.RAT, self.ARF,self.clock)
                    # immediate value goes to value2 without tag needed
                    rs.value2 = int(current_instruction.immediate)
                    # print("[ISSUE] Added Addi RS Unit with immediate value:", rs.value2)
                    # print("[ISSUE] RS Unit details:", rs)
                    self.fs_int_adder.table.append(rs)
                else:
                    self.fs_int_adder.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.src2, self.RAT, self.ARF,self.clock))

            elif (check == "Mult.d") and self.fs_mult.length() < self.multiplier_rs_num:
                self.fs_mult.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.src1, current_instruction.src2, self.RAT, self.ARF,self.clock))

            elif (check == "Sd" or check == "Ld") and self.fs_LS.length() < self.load_store_rs_num:
                print("[ISSUE] Added ld or sd")
                self.fs_LS.table.append(RS_Unit(current_ROB, current_instruction.opcode, current_instruction.offset, current_instruction.src1, self.RAT, self.ARF,self.clock))

            elif (check == "Beq" or check == "Bne"):
                 # Take a RAT snapshot so we can roll back if this branch is mispredicted
                current_instruction.rat_snapshot = self.RAT.snapshot()

                # Issue the branch into the branch RS
                branch_unit = RS_Unit(
                    current_ROB,
                    current_instruction.opcode,
                    current_instruction.src1,
                    current_instruction.src2,
                    self.RAT,
                    self.ARF,
                    self.clock,
                )
                # Remember where this branch lives
                branch_unit.branch_pc = self.act_PC
                branch_unit.branch_offset = current_instruction.offset
                self.fs_branch.table.append(branch_unit)
                # Also keep the offset through the existing helper (optional but harmless)
                self.fs_branch.set_branch_offset(0, current_instruction.offset)

                print(f"[DEBUG] Testing if branch gets to here {self.fs_branch}")

                # Branch prediction / BTB handling
                if self.BTB.find_prediction(self.act_PC) is None:
                    print(f"[BRANCH] New Entry")
                    # Store the target (offset/PC) in the BTB
                    self.BTB.add_branch(self.act_PC, current_instruction.offset)

                current_predication = self.BTB.find_prediction(self.act_PC)

                print(f"[BRANCH] PC : {self.act_PC}")
                print("[BRANCH] Printing BTB ")
                print(self.BTB)

                # If we predict taken, speculatively move PC to the BTB target
                if current_predication:
                    self.PC = self.BTB.get_target(self.act_PC)

                print(
                    f"[BRANCH] Info dump target - target={self.BTB.get_target(self.act_PC)} "
                    f"| current prediction | predicted_taken={bool(current_predication)}"
                )

            else:
                #stall due to full RS
                #if no conditions are satisified, it must mean the targeted RS is full
                #this is not necessary, legacy
                pass

            # We will also be read naming but we shouldn't read until we read from the right registers
            if (check == "Beq" or check == "Bne"):
                # Branch writes a ROB entry but does not rename a destination register
                self.ROB.write(current_ROB, "Branch", None, False, current_instruction)
            else:
                self.ROB.write(current_ROB, current_instruction.dest, None, False, current_instruction)
                # Only real register-writing instructions update the RAT
                self.RAT.write(current_instruction.dest, current_ROB)

            self.instruction_pointer += 1



    # EXECUTE --------------------------------------------------------------
    # Checks the reservation stations for ready instructions, if they are ready, executes them
    # Will simulate cycles needed for each functional unit

    # Execute helper functions
    def parse_rs_table(self, rs_table: RS_Table):
        # print(f"[EXECUTE] Parsing RS Table: {rs_table.type}")
        for rs_unit in rs_table.table:
            # Skip empty slots (if your RS uses opcode)
            print(f"[EXECUTE] RS Table {rs_table.type}")
            #print(f"[EXECUTE] RS Unit {rs_unit}")

            # print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")
            # if getattr(rs_unit, "opcode", None) is None:
            #     continue
            # General execution logic for RS units
            # if rs_table.check_rs_full() is False:
            # Start execution if operands ready, not already executing, and FU available
            print(f"LOOT: value1 = {rs_unit.value1}, value2 = {rs_unit.value2}, cycles_left = {rs_unit.cycles_left}, busy units = {rs_table.busy_FU_units}, num units = {rs_table.num_FU_units}")
            instr_ref = next((instr for instr in self.instructions_in_flight if instr.rob_tag == rs_unit.DST_tag), None)

            # Branch starts here
                        # ---------------- Branch handling ----------------
            if (
                rs_unit.value1 is not None
                and rs_unit.value2 is not None
                and rs_table.type == "fs_branch"
                and rs_unit.cycles_left is None   # only handle once
            ):
                # Compute the branch condition once
                rs_unit.DST_value = rs_table.compute(rs_unit)
                print(f"[EXECUTE] RS Unit {rs_unit} has moved to WB with execution with result {rs_unit.DST_value}.")

                # Branch is effectively 0-cycle in EX, but we still mark it as 'executed'
                rs_unit.cycles_left = rs_table.cycles_per_instruction
                print(
                    f"[EXECUTE] Starting execution of {rs_unit.opcode} for destination {rs_unit.DST_tag} "
                    f"with values {rs_unit.value1}, {rs_unit.value2} for {rs_table.cycles_per_instruction} cycles."
                )

                taken = bool(rs_unit.DST_value)
                branch_pc = getattr(rs_unit, "branch_pc", self.act_PC)
                print(f"[BRANCH] Result={taken} for branch at PC=0x{branch_pc:04X}")

                # What did we predict?
                current_predication = self.BTB.find_prediction(branch_pc)
                print(f"[BRANCH] Predicted_taken={bool(current_predication)} , Actual_taken={taken}")

                if current_predication != taken:
                    print(f"[BRANCH] MISPREDICT: fixing state and updating prediction to {taken}")

                    # Restore RAT to what it was when the branch was issued
                    if instr_ref is not None and getattr(instr_ref, "rat_snapshot", None) is not None:
                        self.RAT.restore(instr_ref.rat_snapshot)

                    # Throw away all young ROB entries
                    removed_addrs = self.ROB.squash_after_address(rs_unit.DST_tag)
                    self.RAT.rat_restore_after_squash(removed_addrs)

                    removed_set = set(removed_addrs)
                    print(f"[BRANCH] Squashed ROB entries: {removed_addrs}")

                    # 3) Flush any RS entries that belonged to squashed ROB entries
                    if removed_addrs:
                        for t in self.all_rs_tables:
                            t.table = [u for u in t.table if u.DST_tag not in removed_set]

                        # 4) Drop any pending CDB updates for squashed entries
                        if len(self.CDB) > 0:
                            from collections import deque  # already imported at top, but harmless
                            new_cdb = deque()
                            for dest_tag, arf_reg, result in self.CDB:
                                if dest_tag not in removed_set:
                                    new_cdb.append((dest_tag, arf_reg, result))
                            self.CDB = new_cdb

                    # Update the predictor with the correct direction
                    self.BTB.change_prediction(branch_pc, taken)

                    # Set the PC to the correct path
                    if taken:
                        target = self.BTB.get_target(branch_pc)
                        if target is None:
                            # Use the saved offset if BTB target is missing
                            target = rs_unit.branch_offset
                        self.PC = _to_int_addr(target) # protect
                    else:
                        # Not taken: fall-through is just branch_pc + 4
                        self.PC = branch_pc + 0x4

                    print(f"[BRANCH] New PC after recovery: 0x{self.PC:04X}")

                # if rs_unit.DST_value:
                #     if isinstance(off, str):
                #         off = int(off, 16) if off.lower().startswith("0x") else int(off)

                #     oldPC = self.PC
                #     # New PC
                #     self.PC = off

                #     self.halt = False  # unfreeze issue/fetch if you halted on branch issue
                #     # remove the branch RS entry now that it’s resolved
                #     # rs_table.table.remove(rs_unit)
                #     print(f"[BRANCH] Resolved: offset={off}, new PC={self.PC}, old PC={oldPC}")
            elif (
                rs_unit.value1 is not None
                and rs_unit.value2 is not None
                and rs_unit.cycles_left is None
                # TODO : Test Pipelined CPU - check for available FU units
                and rs_table.busy_FU_units <= rs_table.num_FU_units 
            ):
                print(f"[EXECUTE] Starting execution of {rs_unit.opcode} for "f"destination {rs_unit.DST_tag} with values {rs_unit.value1} and {rs_unit.value2} for {rs_table.cycles_per_instruction} cycles.")
                
                rs_unit.cycles_left = rs_table.cycles_per_instruction
                
                #roshan
                # print(f"CLOCK CYCLE CHECKER: {instr_ref.issue_cycle}")
                # print(f"CLOCK CYCLE CHECKER: {self.clock}")
    
                if instr_ref and instr_ref.execute_start_cycle is None:
                    if instr_ref.issue_cycle  - self.clock == 0:
                        instr_ref.execute_start_cycle = rs_unit.cycle_issued + 1
                    else:
                        instr_ref.execute_start_cycle = self.clock

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
                #roshan
                if instr_ref and instr_ref.execute_end_cycle is None:
                    instr_ref.execute_end_cycle = self.clock 
            # complete execution if cycles left is 0
            elif rs_unit.cycles_left == 0:
                rs_unit.DST_value = rs_table.compute(rs_unit)
                print(f"[EXECUTE] RS Unit {rs_unit} has moved to WB with execution with result {rs_unit.DST_value}.")
                
                #roshan
                instr_ref = next((instr for instr in self.instructions_in_flight if instr.rob_tag == rs_unit.DST_tag), None)
                if instr_ref:
                    instr_ref.write_back_cycle = self.clock

        # Release all FU units at the end of execution phase since they are pipelined and get freed up for next cycle
        rs_table.release_all_fu_units()

    def execute(self):
        # Execute logic for Floating Point Adder/Subtracter RS
        for rs_table in self.all_rs_tables:
            self.parse_rs_table(rs_table)

    # WRITE BACK --------------------------------------------------------------
    # Helper function for write back
    def write_back(self):
        # if self.pause_for_reset is True:
        #     print("[WRITE BACK] Skipping...")
        #     return

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
        if self.pause_for_reset is True:
            addr, (alias, value, done, instr_ref) = self.ROB.peek()

            print("[COMMIT] Skipping... well kinda?")
            # Set to true if it has a value for all of them
            for i in range(1, self.ROB.max_entries + 1):
                rob_entry_key = "ROB" + str(i)
                rob_entry = self.ROB.read(rob_entry_key)
                # make sure the key is clean
                if rob_entry is not None:
                    # pull values
                    alias, value, done, instr_ref = rob_entry
                    print(f"[COMMIT] Checking ROB entry {rob_entry_key}: alias={alias}, value={value}, done={done}")
                    if value is not None and done is not True:
                        print(f"[COMMIT] Waiting 1 cycle to commit {value} to {alias} from {rob_entry_key}")
                        self.ROB.update_done(rob_entry_key, True)

            print(f"[COMMIT] Checking ROB entry {addr} and clearing from ROB: alias={alias}, value={value}, done={done}")
            if done == True:
                addr = self.ROB.find_by_alias(alias)
                print(f"[COMMIT] Committing {value} to {alias} from {addr}")
                self.ARF.write(alias, value)
                if instr_ref and instr_ref.commit_cycle is None:
                    instr_ref.commit_cycle = self.clock

                # Update RAT to point back to ARF if it still points to this ROB entry
                if self.RAT.read(alias) == addr:
                    self.RAT.write(alias, "ARF" + str(int(alias[1:]) + 32))  
                # Clear the ROB entry
                self.ROB.clear(addr)
                # Only commit one instruction per cycle

            # No more pausing for this cycle. Should issue correctly starting the next cycle
            self.pause_for_reset = False
            return

        if self.ROB.getEntries() > 0:
            # Peak the front

            addr, (alias, value, done, instr_ref) = self.ROB.peek()
            if addr is None:
                return

            print(f"[COMMIT] Checking ROB entry {addr} and clearing from ROB: alias={alias}, value={value}, done={done}")
            if done == True:
                addr = self.ROB.find_by_alias(alias)
                print(f"[COMMIT] Committing {value} to {alias} from {addr}")
                self.ARF.write(alias, value)
                if instr_ref and instr_ref.commit_cycle is None:
                    instr_ref.commit_cycle = self.clock

                # Update RAT to point back to ARF if it still points to this ROB entry
                if self.RAT.read(alias) == addr:
                    self.RAT.write(alias, "ARF" + str(int(alias[1:]) + 32))  
                # Clear the ROB entry
                self.ROB.clear(addr)
                # Only commit one instruction per cycle

            # Set to true if it has a value for all of them
            for i in range(1, self.ROB.max_entries + 1):
                rob_entry_key = "ROB" + str(i)
                rob_entry = self.ROB.read(rob_entry_key)
                # make sure the key is clean
                if rob_entry is not None:
                    # pull values
                    alias, value, done, instr_ref = rob_entry
                    print(f"[COMMIT] Checking ROB entry {rob_entry_key}: alias={alias}, value={value}, done={done}")
                    if value is not None and done is not True:
                        print(f"[COMMIT] Waiting 1 cycle to commit {value} to {alias} from {rob_entry_key}")
                        self.ROB.update_done(rob_entry_key, True)