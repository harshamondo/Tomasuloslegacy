import re

class Instruction:
    def __init__(self, opcode=None, operands=None):
        self.opcode = opcode
        self.operands = operands if operands is not None else []
        self.dest = None
        self.src1 = None
        self.src2 = None
        self.offset = None
        self.immediate = None
        self.label = None

        if opcode is not None and operands is not None:
            op = opcode.lower()
            if op in ["ld", "sd"] and len(operands) == 2:
                self.dest = operands[0]
                match = re.match(r"(-?\d+)\((\w+)\)", operands[1])
                if match:
                    self.offset = int(match.group(1))
                    self.src1 = match.group(2)
            elif op in ["add", "sub", "addi", "beq", "bne"] and len(operands) >= 3:
                self.dest = operands[0]
                self.src1 = operands[1]
                self.src2 = operands[2]
                if op == "addi" and len(operands) == 3:
                    self.immediate = operands[2]
            elif op in ["add.d", "sub.d", "mult.d"] and len(operands) == 3:
                self.dest = operands[0]
                self.src1 = operands[1]
                self.src2 = operands[2]
            elif op == "nop":
                pass

    def __str__(self):
        return f"{self.opcode} {', '.join(self.operands)}"

    def get_opcode(self):
        return self.opcode
    def set_opcode(self, opcode):
        self.opcode = opcode
    def get_operands(self):
        return self.operands
    def set_operands(self, operands):
        self.operands = operands
    def get_dest(self):
        return self.dest
    def set_dest(self, dest):
        self.dest = dest
    def get_src1(self):
        return self.src1
    def set_src1(self, src1):
        self.src1 = src1
    def get_src2(self):
        return self.src2
    def set_src2(self, src2):
        self.src2 = src2
    def get_offset(self):
        return self.offset
    def set_offset(self, offset):
        self.offset = offset
    def get_immediate(self):
        return self.immediate
    def set_immediate(self, immediate):
        self.immediate = immediate