from collections import deque
class RS_Unit:
    def __init__(self,DST_tag = None, opcode = None, reg1 = None, reg2 = None, RAT_object = None, ARF_object = None, cycles_issued = None, inst_id=None, offset=None):
        self.opcode = opcode
        self.tag1 = None
        self.tag2 = None
        self.value1 = None
        self.value2 = None
        self.cycles_left = None
        self.cycle_issued = cycles_issued
        self.DST_value = None
        self.reg1 = reg1
        self.reg2 = reg2
        self.ARF_tag = DST_tag
        self.inst_id = inst_id
        self.offset = offset

        self.RAT = RAT_object
        self.ARF = ARF_object

        self.DST_ROB_tag = RAT_object.read(DST_tag)

        # Source 1 resolution
        if self.reg1:
            alias1 = self.RAT.read(self.reg1)
            if alias1 and alias1.startswith("ROB"):
                self.tag1 = alias1
            elif alias1 and alias1.startswith("ARF"):
                self.value1 = self.ARF.read(self.reg1)
            elif isinstance(self.reg1, (int, float)):
                self.value1 = self.reg1
            # Handle Addi/LD/SD immediate/offset if passed as reg1
            elif isinstance(self.reg1, str) and self.reg1.isdigit():
                 self.value1 = int(self.reg1)

        # Source 2 resolution
        if self.reg2:
            alias2 = self.RAT.read(self.reg2)
            if alias2 and alias2.startswith("ROB"):
                self.tag2 = alias2
            elif alias2 and alias2.startswith("ARF"):
                self.value2 = self.ARF.read(self.reg2)
            elif isinstance(self.reg2, (int, float)):
                self.value2 = self.reg2
            elif isinstance(self.reg2, str) and self.reg2.isdigit():
                 self.value2 = int(self.reg2)

    def print_RS(self):
        print("Now printing RS entry:")
        print("[",self.opcode,"]","[",self.DST_ROB_tag,"]","[",self.tag1,"]","[",self.tag2,"]","[",self.value1,"]","[",self.value2,"]")
    
    def __str__(self):
        return (f"DST_reg={self.ARF_tag}, DST_ROB={self.DST_ROB_tag}, opcode={self.opcode}, "
                f"tag1={self.tag1}, tag2={self.tag2}, value1={self.value1}, value2={self.value2})")

class RS_Table:
    def __init__(self, type = None, num_rs_units = 0, num_FU_units = 0, cycles_per_instruction = 0, ex_cycles=0, mem_cycles=0):
        self.table = []
        self.type = type
        self.num_units = num_rs_units
        self.num_FU_units = num_FU_units
        self.cycles_per_instruction = cycles_per_instruction
        self.ex_cycles = ex_cycles
        self.mem_cycles = mem_cycles
        self.busy_FU_units = 0

        if self.type == "fs_fp_ls":
            self.table = deque()
    
    def add_unit(self, rs_unit):
        self.table.append(rs_unit)

    def __str__(self):
        output = [f"RS Table Type: {self.type} (Busy FUs: {self.busy_FU_units}/{self.num_FU_units})"]
        if not self.table:
            output.append("[Empty]")
        else:
            for i, unit in enumerate(self.table):
                output.append(f"  [{i}] {unit}")
        return "\n".join(output)

    def check_rs_full(self):
        return len(self.table) >= self.num_units
    
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