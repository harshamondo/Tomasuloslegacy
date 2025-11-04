import csv, re
from modules.rat import RAT
from modules.arf import ARF
from modules.instruction import Instruction

def _get_alias_str(alias_obj):
    if isinstance(alias_obj, str):
        return alias_obj
    return getattr(alias_obj, "current_alias", None)

def is_arf(alias_obj) -> bool:
    alias = _get_alias_str(alias_obj)
    return isinstance(alias, str) and alias.startswith("ARF")

# Poor implementation of reading RAT from CSV
# Assumes well-formed CSV with "Register,Value" header
# Also no check for failure
def rat_from_csv(path: str) -> RAT:
    reg_re = re.compile(r"^[RF]\d+$")
    alias_re = re.compile(r"^ARF\d+$")

    rat = RAT()

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and {"Register", "Value"} <= {h.strip() for h in reader.fieldnames}:
            for row in reader:
                reg = (row.get("Register") or "").strip()
                alias = (row.get("Value") or "").strip()
                if not reg or not alias:
                    continue
                if not reg_re.match(reg):
                    raise ValueError(f"Bad register name '{reg}'. Expected 'R#' or 'F#'.")
                if not alias_re.match(alias):
                    raise ValueError(f"Bad alias '{alias}'. Expected 'ARF#'.")
                rat.write(reg, alias)
    return rat

def arf_from_csv(path: str) -> ARF:
    reg_re = re.compile(r"^[RF]\d+$")
    alias_re = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$')

    arf = ARF()

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and {"Register", "Value"} <= {h.strip() for h in reader.fieldnames}:
            for row in reader:
                reg = (row.get("Register") or "").strip()
                value_str = (row.get("Value") or "").strip()
                if not reg or not value_str:
                    continue
                if not reg_re.match(reg):
                    raise ValueError(f"Bad register name '{reg}'. Expected 'R#' or 'F#'.")
                try:
                    value = int(value_str)
                except ValueError:
                    raise ValueError(f"Bad value '{value_str}'. Expected an integer.")
                arf.write(reg, value)
    return arf

# Helper functions for ISSUE
def init_ARF_RAT(self):
        #add logic here to initialize ARF to values
        #add logic here to initialize ARF to values
        for i in range(1,33):
             self.ARF.write("R" + str(i),0)
             self.RAT.write("R" + str(i),"ARF" + str(i))
        for i in range(1,33):
             self.ARF.write("F" + str(i),0)
             self.RAT.write("F" + str(i),"ARF" + str(i+32))