from collections import deque
import re
import csv

from modules.instruction import Instruction
from modules.rob import ROB
from modules.rs import RS_Unit, RS_Table, rs_fp_add_op, rs_fp_sub_op, rs_fp_mul_op, rs_int_add_op, rs_int_sub_op, rs_int_addi_op, rs_branch_bne, rs_branch_beq, rs_sd_op,rs_ld_op

from modules.arf import ARF
from modules.rat import RAT
from modules.memory import memory
from modules.helper import arf_from_csv, is_arf, rat_from_csv, init_ARF_RAT
from pathlib import Path
from default_generator.rat_arf_gen import print_file_arf, print_file_rat
from modules.btb import BTB

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
        self.PC = 0x0
        # Monotonic sequence id for dynamic instructions (used for squash)
        self.next_seq = 0

        self.previous_ROB = None
        #parsing code to set the number of functional units and reservation stations will go here

        #memory must be initiialized before all the RS tables
        #Can add way to parse a config for default memory addresses and values
        self.MEM = memory()
        self.MEM.write(4,3)
        self.MEM.write(8,2)
        self.MEM.write(12,1)
        self.MEM.write(24,6)
        self.MEM.write(28,5)
        self.MEM.write(32,4)

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
        self.fs_LS = RS_Table(type="fs_fp_ls", num_rs_units=self.load_store_rs_num, num_FU_units=self.load_store_FU, cycles_per_instruction=self.load_store_mem_cycles,load_store_address_calc = self.load_store_cycles, memory = self.MEM)
        self.fs_LS.add_op(("ld",rs_ld_op))
        self.fs_LS.add_op(("sd",rs_sd_op))

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
        self.fs_branch = RS_Table(type="fs_branch", num_rs_units=1, num_FU_units=1, cycles_per_instruction=1)
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

        # Track how many times each PC has been fetched so we can
        # append cloned instructions to the end on branch re-fetches
        self.pc_fetch_count = {pc: 0 for pc, _ in self.instr_addresses}

        # initialize RAT and ARF
        # include ways to update ARF based on parameters
        # registers 0-31 and R and 32-64 are F
        self.ARF = ARF()
        self.RAT = RAT()

        # Pull from the ARF and RAT .csv
        self.ARF = arf_from_csv("arf.csv")
        self.RAT = rat_from_csv("rat.csv")

        # initial same number of rows as instructions in queue for now
        # ROB should be a queue
        self.ROB = ROB()

        # Queue for the CDB
        self.CDB = deque()

        #temp SD value holder
        self.temp_SD_val = None
        self.commit_clock = self.clock
        self.had_SD = None
        self.store_load_forward = None
        self.CDB_busy = None
        self.temp_LS = deque()
        #self.last_SD_instruction  = None
        # Halt no longer used
        self.BTB = BTB()

        # Create all the savepoint datastructures here
        self.branch_CDB = None
        self.branch_ROB = None
        self.branch_ARF = None
        self.branch_RAT = None
        self.branch_all_rs_tables = None
        # Track ownership of the single load/store memory port so that
        # ld/sd cannot overlap in the memory stage.
        self.ls_mem_owner = None
        self.store_mem_release_cycle = None

    def _resolve_ready_rs_sources(self, rs_unit):
        # Helper to resolve a single tag/value pair from ROB.
        def _resolve(tag_name):
            entry = self.ROB.read(tag_name)
            if entry:
                _, value, done, _ = entry
                # For operand readiness we only care that a value exists;
                # the ROB 'done' bit is for commit ordering, not for use
                # by dependent instructions.
                if value is not None:
                    return value
            return None

        # tag1/value1
        if getattr(rs_unit, "tag1", None) and isinstance(rs_unit.tag1, str) and rs_unit.tag1.startswith("ROB"):
            ready_val = _resolve(rs_unit.tag1)
            if ready_val is not None:
                rs_unit.value1 = ready_val
                rs_unit.tag1 = None

        # tag2/value2
        if getattr(rs_unit, "tag2", None) and isinstance(rs_unit.tag2, str) and rs_unit.tag2.startswith("ROB"):
            ready_val = _resolve(rs_unit.tag2)
            if ready_val is not None:
                rs_unit.value2 = ready_val
                rs_unit.tag2 = None

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

            # Branch remap Beq/Bnz dest=None, src1=op0, src2=op1, offset=op2, immediate=None
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
            return None  # don't fetch out of bounds

        pc = self.PC
        template = self.pc_to_instr.get(pc)
        if template is None:
            return None

        count = self.pc_fetch_count.get(pc, 0)
        if count == 0:
            # First time this PC is fetched, use the existing Instruction
            instr = template
        else:
            # Subsequent fetch of same PC, clone and append
            # so timing table reflects execution instance
            instr = Instruction(template.opcode, list(template.operands))

            # branch is special
            op_code = (template.opcode or "").lower()
            if op_code in ("beq", "bne"):
                operands = list(template.operands)
                if len(operands) == 3:
                    instr.dest = None
                    instr.src1 = operands[0]
                    instr.src2 = operands[1]
                    instr.offset = operands[2]
                    instr.immediate = None

            # Append cloned instance so it prints at the end
            self.instructions_in_flight.append(instr)

        # Assign a unique dynamic sequence id for squash ordering
        try:
            instr.seq_id = self.next_seq
        except Exception:
            pass
        self.next_seq += 1
        # Record the PC on the fetched instance for squash logic
        try:
            instr.pc = pc
        except Exception:
            pass

        # Record the prediction used for this branch (for printing and recovery)
        try:
            op_code = (instr.opcode or "").lower()
            if op_code in ("beq", "bne"):
                pred_bit = self.BTB.find_prediction(pc)
                # Default to "not taken" if no BTB entry exists yet
                if pred_bit is None:
                    instr.branch_pred = False
                else:
                    instr.branch_pred = bool(pred_bit)
        except Exception:
            try:
                instr.branch_pred = False
            except Exception:
                pass

        self.pc_fetch_count[pc] = count + 1

        # Drive control flow using the prediction (if any)
        next_pc = pc + 0x4
        try:
            op_code = (template.opcode or "").lower()
            if op_code in ("beq", "bne"):
                pred_bit = self.BTB.find_prediction(pc)
                target = self.BTB.get_target(pc)
                if pred_bit is not None and pred_bit == 1 and target is not None:
                    # Ensure BTB target is an integer PC
                    if isinstance(target, str):
                        target_pc = int(target, 16) if target.lower().startswith("0x") else int(target)
                    else:
                        target_pc = int(target)
                    next_pc = target_pc
        except Exception:
            pass

        self.PC = next_pc
        return instr

    def has_next(self):
        return int(self.PC <= self.max_pc)

    def issue(self):
        self._update_ls_memory_state()
        #add instructions into the RS if not full
        #think about how we are going to stall
        #ask prof if we need to have official states like fetch and decode since our instruction class already handles fetch+decode
        current_instruction = None
        if not self.has_next():
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
        if current_instruction is not None:
            current_instruction = self.fetch()
            # DEBUG PRINTS
            #print(f"[ISSUE] int_adder_rs_num: {self.int_adder_rs_num}, fs_int_adder.table size: {self.fs_fp_add.length()}")
            for rs_table in self.all_rs_tables:
                rs_table.print_rs_without_intermediates()
            print(f"[ISSUE] Issuing instruction: {current_instruction.opcode}")

            # Grab the opcode
            check = current_instruction.opcode
            current_ROB = None
            
            current_instruction.issue_cycle = self.clock
            #add to ROB and RAT regardless if we must wait for RS space
            #TODO  the register rename doesn't seem to account for the size of the ROB, absolutely needs to be fixed!
            #TODO  we write to the ROB(X) and the search to see if the value exists. this is poor implementation
            
            #if current_instruction.opcode == "sd":
                #pass
            #else:
            current_ROB = "ROB" + str(self.ROB.getEntries()+1)
            current_instruction.rob_tag = current_ROB

            #check for space in RS
            #have to add tables for mult, and ld/store
            print(f"[ISSUE] Check: {check}")
            if (check == "Add.d" or check == "Sub.d") and self.fs_fp_add.length() < self.FP_adder_rs_num:
                rs = RS_Unit(
                    current_ROB,
                    current_instruction.opcode,
                    current_instruction.src1,
                    current_instruction.src2,
                    self.RAT,
                    self.ARF,
                    self.clock,
                )
                rs.add_instr_ref(current_instruction)
                self._resolve_ready_rs_sources(rs)
                self.fs_fp_add.table.append(rs)

            elif (check == "Add" or check == "Sub" or check == "Addi") and self.fs_int_adder.length() < self.int_adder_rs_num:
                print("[ISSUE] ------")
                if check == "Addi":
                    rs = RS_Unit(
                        current_ROB,
                        current_instruction.opcode,
                        current_instruction.src1,
                        current_instruction.immediate,
                        self.RAT,
                        self.ARF,
                        self.clock,
                    )
                    # immediate value goes to value2 without tag needed
                    rs.value2 = int(current_instruction.immediate)
                    rs.add_instr_ref(current_instruction)
                    self._resolve_ready_rs_sources(rs)
                    self.fs_int_adder.table.append(rs)
                else:
                    rs = RS_Unit(
                        current_ROB,
                        current_instruction.opcode,
                        current_instruction.src1,
                        current_instruction.src2,
                        self.RAT,
                        self.ARF,
                        self.clock,
                    )
                    rs.add_instr_ref(current_instruction)
                    self._resolve_ready_rs_sources(rs)
                    self.fs_int_adder.table.append(rs)

            elif (check == "Mult.d") and self.fs_mult.length() < self.multiplier_rs_num:
                rs = RS_Unit(
                    current_ROB,
                    current_instruction.opcode,
                    current_instruction.src1,
                    current_instruction.src2,
                    self.RAT,
                    self.ARF,
                    self.clock,
                )
                rs.add_instr_ref(current_instruction)
                self._resolve_ready_rs_sources(rs)
                self.fs_mult.table.append(rs)

            elif (check == "sd" or check == "ld") and self.fs_LS.length() < self.load_store_rs_num:
                print("[ISSUE] Added ld or sd")
                #this already works for load
                if check == "sd":
                    rs = RS_Unit(
                        current_ROB,
                        current_instruction.opcode,
                        current_instruction.offset,
                        current_instruction.src1,
                        self.RAT,
                        self.ARF,
                        self.clock,
                        current_instruction.dest,
                    )
                else:
                    rs = RS_Unit(
                        current_ROB,
                        current_instruction.opcode,
                        current_instruction.offset,
                        current_instruction.src1,
                        self.RAT,
                        self.ARF,
                        self.clock,
                    )
                rs.add_instr_ref(current_instruction)
                self._resolve_ready_rs_sources(rs)
                self.fs_LS.table.append(rs)

            elif (check == "Beq" or check == "Bne"):
                # Branch predication will be here (no halting)
                branch_rs = RS_Unit(
                    current_ROB,
                    current_instruction.opcode,
                    current_instruction.src1,
                    current_instruction.src2,
                    self.RAT,
                    self.ARF,
                    self.clock,
                )
                branch_rs.add_instr_ref(current_instruction)
                self._resolve_ready_rs_sources(branch_rs)
                self.fs_branch.table.append(branch_rs)
                # set offset for the newly added branch entry
                self.fs_branch.set_branch_offset(len(self.fs_branch.table) - 1, current_instruction.offset)
                print(f"[DEBUG] Testing if branch gets to here {self.fs_branch}")

                # Add BTB entry only if this PC has not been seen before so that
                # dynamic prediction bits trained by change_prediction are preserved.
                try:
                    branch_pc = self.PC - 0x4
                    if self.BTB.get_target(branch_pc) is None:
                        # Convert the encoded offset/target into an integer PC for bookkeeping.
                        off = current_instruction.offset
                        if isinstance(off, str):
                            target_pc = int(off, 16) if off.lower().startswith("0x") else int(off)
                        else:
                            target_pc = int(off)
                        self.BTB.add_branch(branch_pc, target_pc)
                except Exception:
                    pass
                print(f"PC : {self.PC}")
                print("[BRANCH] Printing BTB ")
                print(self.BTB)

                # save all the main data structures to allow for a system save point
                print(f"[DEBUG] Saving all the data here!")
                self.branch_CDB = self.CDB
                self.branch_ROB = self.ROB
                self.branch_ARF = self.ARF
                self.branch_RAT = self.RAT
                self.branch_all_rs_tables = self.all_rs_tables

            else:
                #stall due to full RS
                #if no conditions are satisified, it must mean the targeted RS is full
                pass
            
            #if current_instruction.opcode != "sd":
            # We will also be read naming but we shouldn't read until we read from the right registers
            if (check == "Beq" or check == "Bne"):
                # Change the ROB write (store instr_ref for timing/printing)
                self.ROB.write(current_ROB, "Branch", None, False, current_instruction)
            else:
                self.ROB.write(current_ROB, current_instruction.dest, None, False, current_instruction)

            #sd does not actually need a ROB entry, but we will use it to commit on time
            if current_instruction.opcode == "sd":
                pass
            else:
                self.RAT.write(current_instruction.dest, current_ROB)

            self.instruction_pointer += 1

    # EXECUTE --------------------------------------------------------------
    # Checks the reservation stations for ready instructions, if they are ready, executes them
    # Will simulate cycles needed for each functional unit

    # Execute helper functions
    def parse_rs_table(self, rs_table: RS_Table):
        # print(f"[EXECUTE] Parsing RS Table: {rs_table.type}")
        for index,rs_unit in enumerate(rs_table.table):
            # Skip empty slots (if your RS uses opcode)
            print(f"[EXECUTE] RS Table {rs_table.type}")
            #print(f"[EXECUTE] RS Unit {rs_unit}")

            # print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")
            # if getattr(rs_unit, "opcode", None) is None:
            #     continue
            # General execution logic for RS units
            # if rs_table.check_rs_full() is False:
            # Start execution if operands ready, not already executing, and FU available
            print(
                f"LOOT: value1 = {rs_unit.value1}, value2 = {rs_unit.value2}, "
                f"cycles_left = {rs_unit.cycles_left}, busy units = {rs_table.busy_FU_units}, "
                f"num units = {rs_table.num_FU_units}"
            )
            # Prefer the Instruction reference stored on the RS unit itself.
            # Fall back to a lookup by ROB tag for any older entries that may not have it.
            instr_ref = getattr(rs_unit, "instr_ref", None)
            if instr_ref is None:
                instr_ref = next(
                    (instr for instr in self.instructions_in_flight if instr.rob_tag == rs_unit.DST_tag),
                    None,
                )

            if (
                rs_unit.value1 is not None and 
                rs_unit.value2 is not None and 
                rs_unit.cycles_left is None and 
                rs_table.busy_FU_units <= rs_table.num_FU_units and (rs_unit.opcode != "sd" or rs_unit.SD_value is not None) #SD_value here is the value needed for address calculation
            ):

                print(f"[EXECUTE] Starting execution of {rs_unit.opcode} for "f"destination {rs_unit.DST_tag} with values {rs_unit.value1} and {rs_unit.value2} for {rs_table.cycles_per_instruction} cycles.")
                
                if rs_unit.opcode == "ld":
                    rs_unit.cycles_left = rs_table.cycles_in_ex_b4_mem + rs_table.cycles_per_instruction
                elif rs_unit.opcode == "sd":
                    rs_unit.cycles_left = rs_table.cycles_in_ex_b4_mem

                    #we can just write to mem in this state not correct for the algorithm, but it is for si

                else:
                    rs_unit.cycles_left = rs_table.cycles_per_instruction
                
                #roshan
    
                if instr_ref and instr_ref.execute_start_cycle is None:
                    if instr_ref is not None:
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
                if rs_unit.opcode == "ld":

                    if rs_unit.cycles_left == rs_table.cycles_per_instruction:
                        if instr_ref and instr_ref.mem_cycle_start is None:
                            if rs_table.memory_occupied == False:
                                instr_ref.mem_cycle_start = self.clock + 1
                                rs_table.use_memory()
                                self.ls_mem_owner = "ld"
                            else:
                                rs_unit.cycles_left = rs_unit.cycles_left + 1
                    
                        if instr_ref and instr_ref.execute_end_cycle is None:
                            instr_ref.execute_end_cycle = self.clock


                print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")

            elif rs_unit.cycles_left == 1:
                rs_unit.cycles_left -= 1
                print(f"[EXECUTE] Completed execution of {rs_unit.opcode} for destination {rs_unit.DST_tag} with result {rs_table.compute(rs_unit)}")
                #roshan
                if rs_unit.opcode == "ld":
                    print(f"HERE")
                    if instr_ref and instr_ref.mem_cycle_end is None:
                        
                        instr_ref.mem_cycle_end = self.clock
                        # If a load finally exits memory but its start cycle was
                        # never recorded (e.g., it waited for a busy LSU port),
                        # backfill it from the known memory latency.
                        if instr_ref.mem_cycle_start is None:
                            mem_latency = getattr(rs_table, "cycles_per_instruction", 0) or 0
                            if mem_latency > 0:
                                instr_ref.mem_cycle_start = instr_ref.mem_cycle_end - mem_latency + 1
                            else:
                                instr_ref.mem_cycle_start = instr_ref.mem_cycle_end
                        if instr_ref.execute_end_cycle is None:
                            if instr_ref.mem_cycle_start is not None:
                                instr_ref.execute_end_cycle = instr_ref.mem_cycle_start - 1
                            else:
                                instr_ref.execute_end_cycle = instr_ref.mem_cycle_end
                        if rs_table.memory_occupied == True:
                            rs_table.release_memory()
                            if self.ls_mem_owner == "ld":
                                self.ls_mem_owner = None

                else:
                    if instr_ref and instr_ref.execute_end_cycle is None:
                        instr_ref.execute_end_cycle = self.clock 


            # complete execution if cycles left is 0
            elif rs_unit.cycles_left == 0:

                print()
                rs_unit.DST_value = rs_table.compute(rs_unit)
                print(f"[EXECUTE] RS Unit {rs_unit} has moved to WB with execution with result {rs_unit.DST_value}.")
                
                #load/store forwarding
                #rs_table.table contains all RS entries in a specific RS(int add, fp add, ..etc)
                #rs_unit is a specific index in that table
                if rs_unit.opcode == "ld":
                    if len(self.temp_LS) > 0:
                        for i in self.temp_LS:
                            temp_res, memory_addy = i
                            #a older RS queue entry's target address matches the ld's target address
                            if memory_addy == rs_unit.DST_value and rs_unit.opcode == "sd":
                                #self.ARF.write(rs_unit.DST_tag,self.ARF.read(rs_table.table[i].DST_tag))

                                #print(f"DEBUG: {rs_unit.DST_tag}")
                                #print(f"DEBUG: {self.ARF.read(rs_table.table[i].DST_tag)}")
                                instr_ref.mem_cycle_end = instr_ref.mem_cycle_start      
                                rs_unit.LD_SD_Forward = temp_res
                                instr_ref.write_back_cycle = instr_ref.mem_cycle_end + 1
                                instr_ref.LD_SD_forward = temp_res
                                break
                            

                if rs_unit.opcode == "sd":

                    #SD_res = self.ARF.read(rs_unit.SD_dest)
                    #print(f"CURR DEBUG {rs_unit.SD_dest}")
                    #self.MEM.write(rs_unit.DST_value,SD_res)
                    #print(f"CURR DEBUG {rs_unit.DST_value}")
                    #print(f"CURR DEBUG {SD_res}")

                    instr_ref.instr_dest = rs_unit.DST_value
                    instr_ref.instr_value = rs_unit.SD_dest
                    #self.temp_LS.append((SD_res,rs_unit.DST_value))
                    
                    # Mark the store as completed in the ROB so it
                    # can commit without going through the CDB path.
                    try:
                        self.ROB.update_done(rs_unit.DST_tag, True)
                    except Exception:
                        pass
                    #rs_unit.add_instr_ref(instr_ref)
                else:
                    if instr_ref and str(instr_ref.opcode).lower() not in ("beq", "bne"):

                        #if str(instr_ref.opcode).lower() == "ld" and instr_ref.LD_SD_forward == True:
                         #   instr_ref.write_back_cycle = instr_ref.mem_cycle_end + 1
                            #current issue ishat multiple instructions can possibily finish on the same cycle sp they have the same WB
                        rs_unit.timing_ref = instr_ref
                        

                # Handle branches here

                # could be buffered but we are just leaving this for write back stage to handle
                # Handle branches here
                if rs_table.type == "fs_branch":
                    # Prefer the computed value (offset if taken, else 0)
                    off = rs_unit.branch_offset
                    print(f"[BRANCH] Dst {rs_unit.DST_value}")
                    # Update ROB with branch outcome (no CDB write-back for branches)
                    self.ROB.update(rs_unit.DST_tag, rs_unit.DST_value)

                    # Record branch outcome on the instruction reference for printing
                    branch_instr = instr_ref
                    if branch_instr is not None:
                        try:
                            branch_instr.branch_taken = bool(rs_unit.DST_value)
                            # If we had a prediction, record if it was correct (for printing).
                            if branch_instr.branch_pred is not None:
                                branch_instr.branch_pred_correct = (
                                    branch_instr.branch_pred == branch_instr.branch_taken
                                )
                        except Exception:
                            branch_instr.branch_taken = None

                    # Determine prediction vs actual outcome
                    predicted_taken = False
                    if branch_instr is not None and branch_instr.branch_pred is not None:
                        predicted_taken = bool(branch_instr.branch_pred)
                    actual_taken = bool(rs_unit.DST_value)

                    # Train BTB with the actual outcome
                    try:
                        if branch_instr is not None and getattr(branch_instr, "pc", None) is not None:
                            self.BTB.change_prediction(branch_instr.pc, actual_taken)
                    except Exception:
                        pass

                    mispredicted = (predicted_taken != actual_taken)

                    if mispredicted and branch_instr is not None and getattr(branch_instr, "seq_id", None) is not None:
                        branch_seq = branch_instr.seq_id

                        # Target PC from encoded offset
                        if isinstance(off, str):
                            target_pc = int(off, 16) if off.lower().startswith("0x") else int(off)
                        else:
                            target_pc = int(off)

                        # Branch PC and fall-through PC
                        try:
                            branch_pc = getattr(branch_instr, "pc", None)
                        except Exception:
                            branch_pc = None
                        fallthrough_pc = (branch_pc + 0x4) if branch_pc is not None else None

                        if actual_taken and not predicted_taken:
                            # Predicted Not Taken, actually Taken: squash fall-through, jump to target
                            oldPC = self.PC
                            self.PC = target_pc
                            print(f"[BRANCH] MISPREDICT NT->T: target={target_pc}, old PC={oldPC}, branch PC={branch_pc}")
                        elif (not actual_taken) and predicted_taken:
                            # Predicted Taken, actually Not Taken: squash taken path, jump to fall-through
                            if fallthrough_pc is not None:
                                oldPC = self.PC
                                self.PC = fallthrough_pc
                                print(f"[BRANCH] MISPREDICT T->NT: fallthrough={fallthrough_pc}, old PC={oldPC}, branch PC={branch_pc}")
                        # Squash all younger dynamic instructions regardless of path
                        self._squash_younger_than_seq(branch_seq)

                    # Remove the branch RS entry (taken or not taken) since it is resolved
                    try:
                        rs_table.table.remove(rs_unit)
                    except ValueError:
                        pass
                    # Only handle one per table per cycle (consistent with write_back)
                    break

                # could be buffered but we are just leaving this for write back stage to handle
                # rs_unit.value1 = None
                # rs_unit.value2 = None
                # print(f"[EXECUTE] Completed execution of {rs_unit.opcode} for destination {rs_unit.DST_tag} with result {rs_unit.DST_value}")

        # Release all FU units at the end of execution phase since they are pipelined and get freed up for next cycle
        rs_table.release_all_fu_units()

    def execute(self):
        self._update_ls_memory_state()
        # Execute logic for Floating Point Adder/Subtracter RS
        for rs_table in self.all_rs_tables:
            print(f"SIZE OF ALL RS TABLES: {len(rs_table.table)}")
            self.parse_rs_table(rs_table)

    # Helper: compute default ARF alias for a register name (e.g., F5 -> ARF37)
    def _default_arf_alias(self, reg_name: str) -> str:
        try:
            if reg_name and reg_name.startswith('F'):
                return "ARF" + str(int(reg_name[1:]) + 32)
            if reg_name and reg_name.startswith('R'):
                return "ARF" + str(int(reg_name[1:]))
        except Exception:
            pass
        return None

    # Squash all in-flight instructions younger than a given dynamic sequence id
    def _squash_younger_than_seq(self, branch_seq: int):
        # Identify instructions to squash: those fetched after this branch
        to_squash = [
            instr for instr in list(self.instructions_in_flight)
            if getattr(instr, "seq_id", -1) > branch_seq
        ]

        # Build a set for squashable ROB tags
        tags = set(instr.rob_tag for instr in to_squash if instr.rob_tag is not None)

        # Remove matching RS entries across all tables
        for rs_table in self.all_rs_tables:
            new_table = []
            for rs_unit in rs_table.table:
                if getattr(rs_unit, "DST_tag", None) in tags:
                    continue
                new_table.append(rs_unit)
            rs_table.table = new_table

        # Remove any pending CDB updates for squashed tags
        if len(self.CDB) > 0:
            try:
                from collections import deque as _dq
                self.CDB = _dq([t for t in self.CDB if t and t[0] not in tags])
            except Exception:
                pass

        # Remove from ROB and fix RAT for squashed destinations
        for instr in to_squash:
            if instr.rob_tag:
                self.ROB.clear(instr.rob_tag)
            if instr.dest:
                # If RAT still points at this squashed ROB, restore to ARF mapping
                if self.RAT.read(instr.dest) == instr.rob_tag:
                    alias = self._default_arf_alias(instr.dest)
                    if alias:
                        self.RAT.write(instr.dest, alias)

        # Remove squashed instructions from printing list
        self.instructions_in_flight = [
            instr for instr in self.instructions_in_flight if instr not in to_squash
        ]

    def _update_ls_memory_state(self):
        # Release the shared LS memory port when a queued store's
        # memory window has elapsed.
        if self.ls_mem_owner == "sd" and self.store_mem_release_cycle is not None:
            if self.clock >= self.store_mem_release_cycle:
                if self.fs_LS.memory_occupied:
                    self.fs_LS.release_memory()
                self.ls_mem_owner = None
                self.store_mem_release_cycle = None

    def memory(self):
        # this stage is only for ld
        # integrate this into execute
        pass
    
    # WRITE BACK --------------------------------------------------------------
    # Helper function for write back
    def write_back(self):
        print("[WRITE BACK] Checking RS Units for write back...")
        # First handle the outputs from the reservation stations
        for rs_table in self.all_rs_tables:

            for rs_unit in rs_table.table:
                # branches and stores do not write back via CDB; they
                # are either handled in execute (sd) or via branch logic
                # for timing/printing only.
                try:
                    op_lower = str(rs_unit.opcode).lower()
                except Exception:
                    op_lower = ""
                if op_lower in ("beq", "bne", "sd") or rs_table.type == "fs_branch":
                    continue
                #if rs_unit.opcode == "sd":
                    #continue
                print(f"[WRITE BACK] RS Unit: {rs_unit}")
                # Check if execution is complete and result is ready
                if (rs_unit.cycles_left == 0 and rs_unit.DST_value is not None):
                    # Write back result to ARF and update ROB

                    if rs_unit.opcode == "ld":
                        result = self.MEM.read(rs_unit.DST_value)

                    else:
                        result = rs_unit.DST_value
                    # result in SD should hold the mem address
                    # this needs to point to F1,F2,F3...etc
                    arf_reg = rs_unit.ARF_tag
                    CDB_res_reg = rs_unit.DST_tag

                    # Temporary print statement for debugging
                    print(f"[WRITE BACK] Writing back result {result} to {arf_reg}, getting ready to update ROB entry for {CDB_res_reg}")
                    #
                    # TODO : Implement CDB arbitration logic
                        
                    self.CDB.append((CDB_res_reg, arf_reg, result, rs_unit.timing_ref))

                    # Remove RS entry


                    rs_table.table.remove(rs_unit)
                    print(f"[WRITE BACK] Removed RS Unit {rs_unit} after write back.")
                        
                    
                    break # Only handle one per requirements

        # Next, handle the Common Data Bus (CDB) updates
        if len(self.CDB) > 0:
            CDB_res_reg, arf_reg, result, instr_ref = self.CDB.pop()
        
                        
            print(f"[WRITE BACK] CDB updating ARF:{arf_reg} and CDB_res:{CDB_res_reg} with value {result}")
            # writing to the ARF is done by the commit stage
            #if it is a ld, we need the value from memory since result is only the offset.
            #if rs_unit.opcode == "ld":
                #result = self.MEM.read(result)
            #else:
                #result = temp
            # check a  ll the tables

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
                    if rs_unit.opcode == "sd" and rs_unit.SD_tag == CDB_res_reg:
                        rs_unit.SD_value = result
                        #self.temp_SD_val = rs_unit.SD_value

                    # Should be able to remove this
                    if rs_unit.value1 is not None and rs_unit.value2 is not None:
                        print(f"[WRITE BACK] RS Unit {rs_unit} now has both operands ready: value1={rs_unit.value1}, value2={rs_unit.value2}")
                        rs_unit.written_back = True
            # Update ROB entry
            if instr_ref is not None and str(instr_ref.opcode).lower() == "ld" and instr_ref.LD_SD_forward is not None:
                instr_ref.write_back_cycle = instr_ref.mem_cycle_end + 1
            else:
                if instr_ref is not None:
                    if instr_ref.LD_SD_forward is not None:
                        pass
                    else:   
                        instr_ref.write_back_cycle = self.clock
            print(f"[WRITE BACK] Completed write back for {arf_reg} with value {result}.")
            self.ROB.update(CDB_res_reg, result)
            print(f"[WRITE BACK] Updated ROB entry for {CDB_res_reg} with value {result}.")

        print(f"[WRITE BACK] Current ROB state: {self.ROB}")
    
    # COMMIT --------------------------------------------------------------
    def commit(self):
        self._update_ls_memory_state()
        if self.ROB.getEntries() > 0:
            #Peak the front
            addr, (alias, value, done, instr_ref) = self.ROB.peek()
            print(f"[COMMIT] Checking ROB entry {addr} and clearing from ROB: alias={alias}, value={value}, done={done}")
            if done == True:
                # Be defensive: instr_ref can be None if an entry was written without it
                self.previous_ROB = (instr_ref.opcode if instr_ref is not None else alias)
                #print(f"PLSWORK: {instr_ref.opcode}")
                addr = self.ROB.find_by_alias(alias)
                print(f"[COMMIT] Committing {value} to {alias} from {addr}")

                
                if instr_ref is not None and instr_ref.opcode == "sd":
                    # Enforce exclusive access to the memory port shared with loads.
                    if self.fs_LS.memory_occupied and self.ls_mem_owner != "sd":
                        print("[COMMIT] Store waiting for memory port to become free.")
                        return
                    if (
                        self.ls_mem_owner == "sd"
                        and self.store_mem_release_cycle is not None
                        and self.clock < self.store_mem_release_cycle
                    ):
                        print("[COMMIT] Store memory stage still busy, delaying commit.")
                        return
                    if self.fs_LS.memory_occupied is False:
                        self.fs_LS.use_memory()
                    self.ls_mem_owner = "sd"
                    self.store_mem_release_cycle = self.clock + self.fs_LS.cycles_per_instruction
                    # Stores do not write a value to ARF but we still
                    # want to record when their commit stage happens
                    self.had_SD = True
                    if instr_ref and instr_ref.commit_cycle is None:
                        instr_ref.commit_cycle = self.clock
                        # For printing, model the SD "commit window"
                        instr_ref.commit_cycle_SD = (
                            instr_ref.commit_cycle + self.fs_LS.cycles_per_instruction - 1
                        )

                        self.clock = instr_ref.commit_cycle_SD - 1

                    SD_res = self.ARF.read(instr_ref.instr_value)
                    self.MEM.write(instr_ref.instr_dest,SD_res)


                elif instr_ref is not None and (instr_ref.opcode == "Beq" or instr_ref.opcode == "Bne"):
                    # Branch commits do not update ARF/RAT; just record commit timing
                    if instr_ref.commit_cycle is None:
                        instr_ref.commit_cycle = self.clock
                else:
                    if instr_ref and instr_ref.commit_cycle is None:

                        if instr_ref.LD_SD_forward is not None:
                            self.ARF.write(alias,instr_ref.LD_SD_forward)

                        else:
                            self.ARF.write(alias, value)           

                        instr_ref.commit_cycle = self.clock
                        

                # Update RAT to point back to ARF if it still points to this ROB entry
                if instr_ref is not None and instr_ref.opcode == "sd":
                    pass
                else:
                    if instr_ref is not None and (instr_ref.opcode == "Beq" or instr_ref.opcode == "Bne"):
                        # No RAT update for branches
                        pass
                    elif self.RAT.read(alias) == addr:

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
