from collections import deque
import re
import csv
import io

from modules.instruction import Instruction
from modules.rob import ROB
from modules.rs import RS_Unit, RS_Table
from modules.arf import ARF
from modules.rat import RAT
# from modules.helper import is_arf

# Overall class that determines the architecture of the CPU
class Architecture:
    def __init__(self, filename=None, config_content=None):
        self.filename = filename
        self.config = "config.csv"
        
        self.int_adder_FU = 1
        self.FP_adder_FU = 1
        self.multiplier_FU = 1
        self.load_store_FU = 1

        self.int_adder_rs_num = 2
        self.FP_adder_rs_num = 3
        self.multiplier_rs_num = 2
        self.load_store_rs_num = 3

        self.integer_adder_cycles = 1
        self.FP_adder_cycles = 3
        self.multiplier_cycles = 20
        self.load_store_ex_cycles = 1
        self.load_store_mem_cycles = 4
        self.FP_adder_mem_cycles = 0 

        self.clock = 1
        self.instruction_id_counter = 0 
        self.inst_timing = {}

        if config_content:
            self._parse_config_content(config_content)
        
        self.fs_fp_add = RS_Table(type="fs_fp_add", num_rs_units=self.FP_adder_rs_num, num_FU_units=self.FP_adder_FU, cycles_per_instruction=self.FP_adder_cycles, ex_cycles=self.FP_adder_cycles, mem_cycles=self.FP_adder_mem_cycles)
        self.fs_LS = RS_Table(type="fs_fp_ls", num_rs_units=self.load_store_rs_num, num_FU_units=self.load_store_FU, cycles_per_instruction=self.load_store_ex_cycles + self.load_store_mem_cycles, ex_cycles=self.load_store_ex_cycles, mem_cycles=self.load_store_mem_cycles)
        self.fs_mult = RS_Table(type="fs_fp_mult", num_rs_units=self.multiplier_rs_num, num_FU_units=self.multiplier_FU, cycles_per_instruction=self.multiplier_cycles, ex_cycles=self.multiplier_cycles, mem_cycles=0)
        self.fs_int_adder = RS_Table(type="fs_int_adder", num_rs_units=self.int_adder_rs_num, num_FU_units=self.int_adder_FU, cycles_per_instruction=self.integer_adder_cycles, ex_cycles=self.integer_adder_cycles, mem_cycles=0)

        self.instruction_queue = deque()
        self.init_instr()

        self.ARF = ARF()
        self.RAT = RAT()
        self.init_ARF_RAT()

        self.ROB = ROB()
        self.CDB = deque()

        # Custom initial ARF writes from main.py equivalent
        self.ARF.write("F2", 10.0)
        self.ARF.write("F3", 10.0)
        self.ARF.write("F4", 20.0)
    
    def _parse_config_content(self, content):
        config_file = io.StringIO(content)
        reader = csv.DictReader(config_file)
        for row in reader:
            self._process_config_row(row)

    def _process_config_row(self, row):
        type_name = row.get("Type", "").strip().lower()
        rs_field = row.get("# of rs")
        ex_field = row.get("Cycles in EX")
        mem_field = row.get("Cycles in Mem")
        fu_field = row.get("# of FUs")

        if re.search("integer adder", type_name, re.IGNORECASE):
            self.int_adder_rs_num = int(rs_field) if rs_field and rs_field.isdigit() else self.int_adder_rs_num
            self.integer_adder_cycles = int(ex_field) if ex_field and ex_field.isdigit() else self.integer_adder_cycles
            self.int_adder_FU = int(fu_field) if fu_field and fu_field.isdigit() else self.int_adder_FU
        elif re.search("fp adder", type_name, re.IGNORECASE):
            self.FP_adder_rs_num = int(rs_field) if rs_field and rs_field.isdigit() else self.FP_adder_rs_num
            self.FP_adder_cycles = int(ex_field) if ex_field and ex_field.isdigit() else self.FP_adder_cycles
            self.FP_adder_mem_cycles = int(mem_field) if mem_field and mem_field.isdigit() else self.FP_adder_mem_cycles
            self.FP_adder_FU = int(fu_field) if fu_field and fu_field.isdigit() else self.FP_adder_FU
        elif re.search("fp multiplier", type_name, re.IGNORECASE):
            self.multiplier_rs_num = int(rs_field) if rs_field and rs_field.isdigit() else self.multiplier_rs_num
            self.multiplier_cycles = int(ex_field) if ex_field and ex_field.isdigit() else self.multiplier_cycles
            self.multiplier_FU = int(fu_field) if fu_field and fu_field.isdigit() else self.multiplier_FU
        elif re.search("load/store unit", type_name, re.IGNORECASE):
            self.load_store_rs_num = int(rs_field) if rs_field and rs_field.isdigit() else self.load_store_rs_num
            self.load_store_ex_cycles = int(ex_field) if ex_field and ex_field.isdigit() else self.load_store_ex_cycles
            self.load_store_mem_cycles = int(mem_field) if mem_field and mem_field.isdigit() else self.load_store_mem_cycles
            self.load_store_FU = int(fu_field) if fu_field and fu_field.isdigit() else self.load_store_FU

    def _get_rs_table(self, opcode):
        op = opcode.upper().replace('.', '')
        if op in ["ADDD", "SUBD"]: return self.fs_fp_add
        elif op == "MULTD": return self.fs_mult
        elif op in ["LD", "SD", "L.D", "S.D"]: return self.fs_LS
        elif op in ["ADD", "SUB", "ADDI", "BNE", "BEQ"]: return self.fs_int_adder
        return None

    def parse(self):
        instructions = []
        try:
            with open(self.filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    parts = line.split(':')
                    instruction_str = parts[-1].strip()
                    
                    parts = instruction_str.replace(',', '').split()
                    if len(parts) > 0:
                        opcode = parts[0]
                        operands = parts[1:]
                        instructions.append((opcode, operands))
        except FileNotFoundError:
            # Fallback for instruction set content if file isn't created yet
            content = "Add.d F1, F2, F3\nAdd.d F3, F1, F4"
            for line in content.strip().split('\n'):
                parts = line.replace(',', '').split()
                if len(parts) > 0:
                    instructions.append((parts[0], parts[1:]))
        return instructions

    def gen_instructions(self, instruction_list):
        while instruction_list:
            instr = instruction_list.pop(0)
            if isinstance(instr, tuple):
                opcode, operands = instr
                self.instruction_queue.append(Instruction(opcode, operands))
    
    def init_instr(self):
        instructions_list = self.parse()
        self.gen_instructions(instructions_list)

    def init_ARF_RAT(self):
        for i in range(1, 33):
            self.ARF.write("R" + str(i), 0)
            self.RAT.write("R" + str(i), "ARF" + str(i))
            self.ARF.write("F" + str(i), 0.0)
            self.RAT.write("F" + str(i), "ARF" + str(i + 32))

    def fetch(self):
        if len(self.instruction_queue) == 0:
            return None
        current_instruction = self.instruction_queue.popleft()
        return current_instruction

    def _record_timing(self, inst_id, stage, cycle):
        if inst_id not in self.inst_timing:
            self.inst_timing[inst_id] = {
                'inst_obj': None, 'Is': None, 'Ex_S': None, 'Ex_E': None, 
                'Mem_S': None, 'Mem_E': None, 'WB': None, 'Com': None
            }
        self.inst_timing[inst_id][stage] = cycle

    def issue(self):
        current_instruction = self.fetch()
        
        if current_instruction is not None:
            rs_table = self._get_rs_table(current_instruction.opcode)
            
            if rs_table and not rs_table.check_rs_full() and self.ROB.getEntries() < self.ROB.max_entries:
                inst_id = self.instruction_id_counter
                
                self._record_timing(inst_id, 'Is', self.clock)
                self.inst_timing[inst_id]['inst_obj'] = current_instruction

                rob_tag = "ROB" + str(self.ROB.tail)
                if current_instruction.dest:
                    self.ROB.write(rob_tag, current_instruction.dest, None, False)
                    self.RAT.write(current_instruction.dest, rob_tag)
                
                rs_unit = RS_Unit(
                    DST_tag=current_instruction.dest, 
                    opcode=current_instruction.opcode, 
                    reg1=current_instruction.src1, 
                    reg2=current_instruction.src2, 
                    RAT_object=self.RAT, 
                    ARF_object=self.ARF, 
                    cycles_issued=self.clock, 
                    inst_id=inst_id,
                    offset=current_instruction.offset
                )
                rs_table.add_unit(rs_unit)

                self.instruction_id_counter += 1
                return True
            else:
                self.instruction_queue.appendleft(current_instruction)
                return False
        return False
        
    def execute(self):
        rs_tables = [self.fs_fp_add, self.fs_mult, self.fs_LS, self.fs_int_adder]

        for rs_table in rs_tables:
            units_to_remove = []
            for rs_unit in rs_table.table:
                
                # Check if ready to start EX and FU is available
                if rs_unit.value1 is not None and rs_unit.value2 is not None and rs_unit.cycles_left is None and rs_table.busy_FU_units < rs_table.num_FU_units:
                    # Start EX
                    rs_unit.cycles_left = rs_table.ex_cycles + rs_table.mem_cycles
                    
                    if rs_unit.cycles_left > 0:
                        self._record_timing(rs_unit.inst_id, 'Ex_S', self.clock)
                        rs_unit.cycles_left -= 1
                        rs_table.use_fu_unit()
                        
                        # Handle 0-cycle EX and immediate MEM start
                        if rs_table.ex_cycles == 0 and rs_table.mem_cycles > 0:
                            self._record_timing(rs_unit.inst_id, 'Mem_S', self.clock)

                # Continue EX/MEM
                elif rs_unit.cycles_left is not None and rs_unit.cycles_left > 0:
                    rs_unit.cycles_left -= 1

                    total_cycles = rs_table.ex_cycles + rs_table.mem_cycles
                    cycles_done = total_cycles - (rs_unit.cycles_left + 1)
                    
                    # Check for EX end and MEM start
                    if cycles_done == rs_table.ex_cycles and rs_table.ex_cycles > 0:
                         self._record_timing(rs_unit.inst_id, 'Ex_E', self.clock)
                         if rs_table.mem_cycles > 0:
                            self._record_timing(rs_unit.inst_id, 'Mem_S', self.clock + 1) # MEM starts next cycle
                    
                # Complete EX/MEM and write result to CDB
                if rs_unit.cycles_left == 0:
                    # Calculate result (simplification)
                    result = 0.0
                    op = rs_unit.opcode.lower()
                    v1 = rs_unit.value1
                    v2 = rs_unit.value2
                    
                    if op in ["add.d", "add"]:
                        result = v1 + v2
                    elif op in ["sub.d", "sub"]:
                        result = v1 - v2
                    elif op in ["mult.d", "mult"]:
                        result = v1 * v2
                    
                    rs_unit.DST_value = result
                    
                    # Record the final cycle for EX/MEM
                    if rs_table.ex_cycles > 0 and rs_table.mem_cycles == 0:
                        self._record_timing(rs_unit.inst_id, 'Ex_E', self.clock)
                    elif rs_table.mem_cycles > 0:
                         self._record_timing(rs_unit.inst_id, 'Mem_E', self.clock)
                    
                    self.CDB.append(({'result': rs_unit.DST_value, 'rob_tag': rs_unit.DST_ROB_tag, 'inst_id': rs_unit.inst_id}, rs_table))
                    
                    units_to_remove.append(rs_unit) 
                    rs_unit.cycles_left = -1 # Mark as done execution

    def write_back(self):
        if len(self.CDB) > 0:
            cdb_item, rs_table_used = self.CDB.popleft()
            result = cdb_item['result']
            rob_tag = cdb_item['rob_tag']
            inst_id = cdb_item['inst_id']

            self._record_timing(inst_id, 'WB', self.clock)

            if rob_tag and rob_tag.startswith("ROB"):
                self.ROB.update(rob_tag, result)
            
            rs_tables = [self.fs_fp_add, self.fs_mult, self.fs_LS, self.fs_int_adder]
            for rs_table in rs_tables:
                for rs_unit in list(rs_table.table): # Iterate over a copy for safe removal
                    if rs_unit.tag1 == rob_tag:
                        rs_unit.value1 = result
                        rs_unit.tag1 = None
                    if rs_unit.tag2 == rob_tag:
                        rs_unit.value2 = result
                        rs_unit.tag2 = None
                    
                    # Remove RS entry that wrote back (marked with cycles_left = -1 in execute)
                    if rs_unit.cycles_left == -1 and rs_unit.DST_ROB_tag == rob_tag:
                        rs_table.table.remove(rs_unit)
                        rs_table_used.release_fu_unit()

    def commit(self):
        head_key = "ROB" + str(self.ROB.head)
        rob_entry = self.ROB.read(head_key)

        if rob_entry and rob_entry['done'] == True:
            
            inst_id_to_record = None
            for inst_id, entry in self.inst_timing.items():
                if entry['inst_obj'].dest == rob_entry['alias'] and entry['Com'] is None:
                    inst_id_to_record = inst_id
                    break
            
            if inst_id_to_record is not None:
                self._record_timing(inst_id_to_record, 'Com', self.clock)
            
            # Write result to ARF
            dest_reg = rob_entry['alias']
            result = rob_entry['value']
            self.ARF.write(dest_reg, result)

            # Update RAT
            reg_type = dest_reg[0]
            reg_num = int(dest_reg[1:])
            arf_tag_num = reg_num + (32 if reg_type == 'F' else 0)
            
            if self.RAT.read(dest_reg) == head_key:
                self.RAT.write(dest_reg, "ARF" + str(arf_tag_num))

            # Clear ROB entry and advance head
            self.ROB.clear(head_key)
            return True
        return False
    
    def display_timing_table(self):
        header = ["Inst", "ISSUE", "EX", "MEM", "WB", "COM"]
        
        max_inst_len = max(len(str(entry.get('inst_obj', ''))) for entry in self.inst_timing.values()) if self.inst_timing else 10
        inst_format = f"{{:<{max_inst_len + 2}}}"
        
        separator_line = [
            "-" * (max_inst_len + 2), 
            "-------", 
            "------", 
            "-------", 
            "----", 
            "----"
        ]
        
        header_row = f"{inst_format.format(header[0])} | {header[1]:<7} | {header[2]:<6} | {header[3]:<7} | {header[4]:<4} | {header[5]:<4}"
        separator_str = f"{separator_line[0]} | {separator_line[1]} | {separator_line[2]} | {separator_line[3]} | {separator_line[4]} | {separator_line[5]}"
        
        print("\n" + "=" * len(header_row))
        print("Tomasulo Algorithm Timing Table")
        print("=" * len(header_row))
        print(header_row)
        print(separator_str)
        
        for inst_id in sorted(self.inst_timing.keys()):
            entry = self.inst_timing[inst_id]
            inst_obj = entry.get('inst_obj')
            if not inst_obj: continue

            full_inst_str = str(inst_obj)
            
            issue_time = str(entry.get('Is', ''))
            
            ex_start = entry.get('Ex_S', '')
            ex_end = entry.get('Ex_E', '')
            ex_str = ""
            if ex_start and ex_end:
                ex_str = f"{ex_start}" if ex_start == ex_end else f"{ex_start}-{ex_end}"
            elif ex_end or ex_start:
                ex_str = str(ex_end or ex_start)

            mem_start = entry.get('Mem_S', '')
            mem_end = entry.get('Mem_E', '')
            mem_str = ""
            if mem_start and mem_end:
                mem_str = f"{mem_start}" if mem_start == mem_end else f"{mem_start}-{mem_end}"
            elif mem_end or mem_start:
                 mem_str = str(mem_end or mem_start)
            
            if not mem_str and not (self.fs_LS.mem_cycles > 0 and 'LD' in full_inst_str.upper()):
                 mem_str = '-'

            wb_time = str(entry.get('WB', ''))
            com_time = str(entry.get('Com', ''))

            print(f"{inst_format.format(full_inst_str)} | {issue_time:<7} | {ex_str:<6} | {mem_str:<7} | {wb_time:<4} | {com_time:<4}")

        print("=" * len(header_row) + "\n")