# logger.py
import logging, sys, io

def setup_logging(log_path="run.log"):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s",
                            datefmt="%H:%M:%S")

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)

    root.handlers.clear()
    root.addHandler(sh)
    root.addHandler(fh)
    return root

class StreamToLogger(io.TextIOBase):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self._buf = ""

    def write(self, s):
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line:
                self.logger.log(self.level, line)

    def flush(self):
        if self._buf:
            self.logger.log(self.level, self._buf)
            self._buf = ""
