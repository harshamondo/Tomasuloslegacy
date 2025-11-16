class RAT:

    #addressing ROB1..ROB2..etc
    #value is another register or alias
    def __init__(self):
        self.data = {}
      
    def read(self, address):
        return self.data.get(address, None)

    def write(self, address,alias):
       
        self.data[address] = alias

    def clear(self,address):
        self.data.pop(address, None)
        self.entries -= 1

    def __str__(self):
        return f"RAT(Rdata={self.R_type})", f"RAT(Rdata={self.F_type})"
    
    def snapshot(self):
        return dict(self.data)

    def restore(self, snap):
        # Restore a previously-saved snapshot from snapshot().
        if snap is None:
            return
        self.data.clear()
        self.data.update(snap)

    def rat_restore_after_squash(self, removed_addrs):
        if not removed_addrs:
            return

        removed = set(removed_addrs)

        for reg, alias in list(self.data.items()):
            if alias not in removed:
                continue  # still valid

            # Need to restore this reg's alias to ARF
            if reg.startswith("R"):
                # R1 -> ARF1, R2 -> ARF2, ...
                num = int(reg[1:])
                default_alias = f"ARF{num}"
            elif reg.startswith("F"):
                # F1 -> ARF33, F2 -> ARF34, ... (32 integer regs)
                num = int(reg[1:])
                default_alias = f"ARF{32 + num}"
            else:
                # Unknown naming convention; safest is to just drop it
                # or leave as-is. We'll drop it here.
                default_alias = None

            if default_alias is not None:
                self.data[reg] = default_alias
            else:
                # if we couldn't determine a default, just clear mapping
                self.data.pop(reg, None)