from collections import deque
import re
import csv

from instruction import Instruction
from rob import ROB
from rs import RS_Unit, RS_Table
from arf import ARF
from rat import RAT

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
                    self.FP_adder_FU = int(fu_field) if fu_field.isdigit() else self.FP_adder_FU             

        print(f"FP Adder RS Num: {self.FP_adder_rs_num}, FP Adder FU: {self.FP_adder_FU}")
        self.fs_fp_add = RS_Table(type="fs_fp_add", num_rs_units=self.FP_adder_rs_num, num_FU_units=self.FP_adder_FU)
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

        #assume individual RS
		#[OP][Dst-Tag][Tag1][Tag1][Val1][Val2]
        #RS_tables will contain an array of RS_unit objects
        #self.RS_tables = []
        self.int_adder_RS = []
        self.FP_adder_RS = []
        self.multiplier_RS = []
        self.load_store_RS = []
        self.init_config()


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
    
    def init_config(self):
          #parse config.txt
          #include code to parse config.txt and update # of RS for each unit accordingly, for now it is hardcoded to initialize the RS tables
          for i in range(1,self.FP_adder_rs_num):
                self.FP_adder_RS.append(RS_Unit())
          for i in range(1,self.int_adder_rs_num):
                self.int_adder_RS.append(RS_Unit())
          for i in range(1,self.multiplier_rs_num):
                self.multiplier_RS.append(RS_Unit())
          for i in range(1,self.load_store_rs_num):
                self.load_store_RS.append(RS_Unit())

          #debug
          #print(len(self.FP_adder_RS))
    def init_ARF_RAT(self):
        #add logic here to initialize ARF to values
        for i in range(1,65):
             self.ARF.write("R" + str(i),0)
             self.RAT.write("R" + str(i),"ARF" + str(i))

    def issue(self):
        #add instructions into the RS if not full
        #think about how we are going to stall
        #ask prof if we need to have official states like fetch and decode since our instruction class already handles fetch+decode
        current_instruction = self.fetch()
        check = current_instruction.opcode
        issued = False
        if check == "Add.d":
            #check FP add RS
            for i in self.FP_adder_RS:
                  if i == None and i.status == False:
                        #add to ROB table
                        #update RAT
                        self.ROB.append(ROB_entry(current_instruction.dest))
                        self.RAT[current_instruction.dest[-1]].current_alias = "ROB" + str(len(self.ROB)+1)
                        
                        #add to reservation stations
                        #[status][DST_tag][opcode][tag1][tag2][value1][value2]
                        self.FP_adder_RS[i].add_entry(True,self.RAT[current_instruction.dest[-1]].current_alias,check,current_instruction.src1, current_instruction.src2)
                        issued = True
                        
            if issued == False:
                  #add stall state?
                  pass
                        
        #add logic for other instructions                
    

    def fetch(self):
        current_instruction = self.instruction_queue.popleft()
        return current_instruction
    def decode(self):
        pass
        
    # EXECUTE --------------------------------------------------------------
    # Checks the reservation stations for ready instructions, if they are ready, executes them
    # Will simulate cycles needed for each functional unit
    def execute(self):
        for i in self.FP_adder_RS:
            if i.status == True:
                #check if operands are ready
                if i.tag1 == None and i.tag2 == None:
                    #execute instruction
                    result = self.INT_adder(i.value1, i.value2)  
                    #clear RS entry
                    i.del_entry()
        
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