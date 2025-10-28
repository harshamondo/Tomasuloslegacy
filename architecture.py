from collections import deque
import re
import csv

from modules.instruction import Instruction
from modules.rob import ROB
from modules.rs import RS_Unit, RS_Table
from modules.arf import ARF
from modules.rat import RAT
from modules.helper import is_arf

# Overall class that determines the architecture of the CPU
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

        self.int_adder_rs_num = 2
        self.FP_adder_rs_num = 3
        self.multiplier_rs_num = 2
        self.load_store_rs_num = 3

        self.clock = 0

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
        self.fs_fp_add.__str__()

        #Initialize instruction register
        self.instruction_queue = deque()
        self.init_instr()

        #initialize RAT and ARF
        #include ways to update ARF based on parameters
        #registers 0-31 and R and 32-64 are F
        self.ARF = ARF()
        self.RAT = RAT()
        self.init_ARF_RAT()

        self.ARF.write("F2",10)  
        self.ARF.write("F3",10)  

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
            if check == "Add.d":
                print(self.ROB.getEntries())
                #add to ROB and RAT regardless if we must wait for RS space
                current_ROB = "ROB" + str(self.ROB.getEntries()+1)
                self.ROB.write(current_ROB, current_instruction.dest, None, False)
                self.RAT.write(current_instruction.dest,current_ROB)

                #check for space in RS
                if len(self.fs_fp_add.table) < self.FP_adder_rs_num:
                    print(f"[ISSUE] Issuing instruction {current_instruction} to FS/FP ADD RS.")

                    rsu = RS_Unit()

                    rsu.RAT = self.RAT
                    rsu.ARF = self.ARF

                    rsu.add_entry(
                        status =False,
                        DST_tag=current_instruction.dest,
                        type   ="fs_fp_add",
                        opcode =current_instruction.opcode,
                        tag1   =current_instruction.get_src1(),
                        tag2   =current_instruction.get_src2(),
                        cycles_issued=self.clock
                    )

                    print(f"[ISSUE] Created RS Unit: {rsu}")
                    self.fs_fp_add.table.append(rsu)
                    print(f"[ISSUE] FS/FP ADD RS after issuing: {[str(unit) for unit in self.fs_fp_add.table]}")
                else:
                    print(f"[ISSUE] Stalling: No space in FS/FP ADD RS for instruction {current_instruction}.")          
            else:
                print("[ISSUE] Unsupported instruction for issue:", check)

        else:
            print("[ISSUE] No instruction to issue this cycle.")

        print("[ISSUE] #######################")
        # Go through the RS table and check for if the values are in the ARF or waiting on tags
        for rs_unit in self.fs_fp_add.table:
            alias1 = self.RAT.read(rs_unit.tag1)
            alias2 = self.RAT.read(rs_unit.tag2)
            print(f"[ISSUE] Checking RS Unit {rs_unit}: tag1={rs_unit.tag1} (value1: {rs_unit.value1}), tag2={rs_unit.tag2} (value2: {rs_unit.value2})")
            if is_arf(alias1) and rs_unit.value1 is None:
                rs_unit.value1 = self.ARF.read(rs_unit.tag1)
                print(f"[ISSUE] RS Unit {rs_unit} is ready with values {rs_unit.value1}.")     
            
            if is_arf(alias2) and rs_unit.value2 is None:
                rs_unit.value2 = self.ARF.read(rs_unit.tag2)
                print(f"[ISSUE] RS Unit {rs_unit} is ready with value2 {rs_unit.value2}.")

            if rs_unit.value1 is not None and rs_unit.value2 is not None:
                rs_unit.status = True
                print(f"[ISSUE] RS Unit {rs_unit} is now ready for execution.")
                

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
    def execute(self):
        for rs_unit in self.fs_fp_add.table:
            # Floating Point Adder Execution
            if self.fs_fp_add.check_rs_full() == False:
                #execute instruction
                # first check if operands are ready
                # then check if FU is available
                # then execute instruction for required cycles
                if rs_unit.value1 is not None and rs_unit.value2 is not None and rs_unit.cycles_left is None and self.fs_fp_add.busy_FU_units < self.fs_fp_add.num_FU_units:
                    print(f"[EXECUTE] Starting execution of {rs_unit.opcode} for destination {rs_unit.DST_tag} with values {rs_unit.value1} and {rs_unit.value2}")
                    rs_unit.cycles_left = self.fs_fp_add.cycles_per_instruction
                    print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")
                    self.fs_fp_add.use_fu_unit()

                # decrement cycles left if already executing
                elif rs_unit.cycles_left is not None and rs_unit.cycles_left > 0:
                    rs_unit.cycles_left -= 1
                    print(f"[EXECUTE] RS Unit {rs_unit} has {rs_unit.cycles_left} cycles left.")

                # complete execution if cycles left is 0
                elif rs_unit.cycles_left == 0:
                    rs_unit.DST_value = rs_unit.value1 + rs_unit.value2
                    rs_unit.value1 = None
                    rs_unit.value2 = None
                    print(f"[EXECUTE] Completed execution of {rs_unit.opcode} for destination {rs_unit.DST_tag} with result {rs_unit.DST_value}")
                    self.fs_fp_add.release_fu_unit()
            
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
                dest_reg = rs_unit.DST_tag

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
                if rs_unit.tag1 == dest_reg:
                    rs_unit.value1 = result
                    print(f"[WRITE BACK] Updated RS Unit {rs_unit} value1 with {result}")
                if rs_unit.tag2 == dest_reg:
                    rs_unit.value2 = result
                    print(f"[WRITE BACK] Updated RS Unit {rs_unit} value2 with {result}")

            # Update ROB entry
            rob_entry = self.RAT.read(dest_reg)
            if rob_entry and rob_entry.startswith("ROB"):
                self.ROB.update(rob_entry, result)
    
    # COMMIT --------------------------------------------------------------
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
                            self.RAT.write(alias, "ARF" + alias[1:])  
                        # Clear the ROB entry
                        self.ROB.clear(rob_entry_key)
                        # Only commit one instruction per cycle
                        break  

    def FP_adder(self, reg1, reg2):
        pass

    def INT_adder(self, reg1, reg2):
        pass

    def multiplier(self, reg1, reg2):
        pass

    def CDB(self):
        pass