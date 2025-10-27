from collections import deque
import re
import csv

from modules.instruction import Instruction
from modules.rob import ROB
from modules.rs import RS_Unit, RS_Table
from modules.arf import ARF
from modules.rat import RAT

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

        #initial same number of rows as instructions in queue for now
        #ROB should be a queue
        self.ROB = ROB()


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
        check = current_instruction.opcode
        issued = False
        current_ROB = None
        if check == "Add.d":
            
            print(self.ROB.getEntries())
            #add to ROB and RAT regardless if we must wait for RS space
            current_ROB = "ROB" + str(self.ROB.getEntries()+1)
            self.ROB.write(current_ROB,current_instruction.dest,None,None)
            self.RAT.write(current_instruction.dest,current_ROB)

            #check for space in RS
            if len(self.fs_fp_add.table) < self.FP_adder_rs_num:
                self.fs_fp_add.table.append(RS_Unit(current_instruction.dest,current_instruction.opcode,current_instruction.src1,current_instruction.src2,self.RAT,self.ARF))
            else:
                #stall
                pass              
    

    def fetch(self):
        current_instruction = self.instruction_queue.popleft()
        return current_instruction
    def decode(self):
        pass
        
    # EXECUTE --------------------------------------------------------------
    # Checks the reservation stations for ready instructions, if they are ready, executes them
    # Will simulate cycles needed for each functional unit
    def execute(self):
        for rs_unit in self.fs_fp_add.table:
            if self.fs_fp_add.check_rs_full() == False:
                #execute instruction
                if rs_unit.value1 is not None & rs_unit.value2 is not None:
                    rs_unit.set_cycles(self.fs_fp_add.cycles_per_instruction)
                    self.fs_fp_add.use_fu_unit()
                    
                if rs_unit.get_cycles() > 0:
                    rs_unit.decrement_cycles()

                if rs_unit.get_cycles() == 0:
                    rs_unit.set_cycles(self.fs_fp_add.cycles_per_instruction)
                    self.fs_fp_add.DST_value = rs_unit.value1 + rs_unit.value2
                    self.fs_fp_add.release_fu_unit()

    def write_back(self):
        pass
    
    def FP_adder(self,reg1,reg2):
        pass

    def INT_adder(self,reg1,reg2):
        pass

    def multiplier(self,reg1,reg2):
        pass
    
    def CBD(self):
        pass