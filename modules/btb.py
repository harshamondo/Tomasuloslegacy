class BTB:
    def __init__(self, rows=8):
        # [Lookup tag (PC & mask)] [Target PC] [Prediction bit: 0 don't take, 1 take]
        self.rows = rows
        self.cols = 3
        self.data = [[None] * self.cols for _ in range(self.rows)]  # no aliasing
        self.entries = 0
        self.max_entries = rows
        self.mask = 0b111  # 3-bit index

    def _index_of(self, tag):
        for idx, slot in enumerate(self.data):
            if slot[0] == tag:
                return idx
        return -1

    def add_branch(self, PC, Target):
        tag = PC & self.mask

        # Update existing
        idx = self._index_of(tag)
        if idx != -1:
            self.data[idx][1] = Target
            self.data[idx][2] = 0  # default: not taken
            return idx

        # Insert into first free slot
        if self.entries < self.max_entries:
            for i, slot in enumerate(self.data):
                if slot[0] is None:
                    self.data[i][0] = tag
                    self.data[i][1] = Target
                    self.data[i][2] = 0  # default: not taken
                    self.entries += 1
                    return i

        # BTB full (no replacement policy specified)
        return None

    def change_prediction(self, PC, taken):
        tag = PC & self.mask
        idx = self._index_of(tag)
        if idx == -1:
            return False
        self.data[idx][2] = 1 if taken else 0
        return True

    def find_prediction(self, PC):
        tag = PC & self.mask
        idx = self._index_of(tag)
        if idx == -1:
            return None
        return self.data[idx][2]

    def get_target(self, PC):
        tag = PC & self.mask
        idx = self._index_of(tag)
        if idx == -1:
            return None
        return self.data[idx][1]

    def __str__(self):
        lines = []
        for count, (tag, tgt, pred) in enumerate(self.data, start=1):
            lines.append(f"Index [{count}] PC_tag:{tag} | Target:{tgt} | Pred:{pred}")
        return "\n".join(lines)
