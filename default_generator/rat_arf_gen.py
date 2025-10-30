import csv

# ====== Configurable lengths and overrides ======
NUM_R = 32          # how many R registers 
NUM_F = 32          # how many F registers 

R_DEFAULT = 0       # default value for all registers
F_DEFAULT = 0       

F_OVERRIDES = {}
R_OVERRIDES = {}
# ===============================================

def generate_rows_arf(num_r, num_f, r_default, f_default, r_overrides, f_overrides):
    rows = []
    for i in range(1, num_r + 1):
        rows.append((f"R{i}", r_overrides.get(i, r_default)))
    for i in range(1, num_f + 1):
        rows.append((f"F{i}", f_overrides.get(i, f_default)))
    return rows

def generate_rows_rat(num_r, num_f):
    rows = []
    index = 1
    for i in range(1, num_r + 1):
        rows.append((f"R{i}", f"ARF{index}"))
        index += 1
    for i in range(1, num_f + 1):
        rows.append((f"F{i}", f"ARF{index}"))
        index += 1
    return rows

def print_file_arf():
    rows = generate_rows_arf(NUM_R, NUM_F, R_DEFAULT, F_DEFAULT, R_OVERRIDES, F_OVERRIDES)
    with open("arf.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Register", "Value"])
        writer.writerows(rows)
    print("Wrote arf.csv")

def print_file_rat():
    rows = generate_rows_rat(NUM_R, NUM_F)
    with open("rat.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Register", "Value"])
        writer.writerows(rows)
    print("Wrote rat.csv")