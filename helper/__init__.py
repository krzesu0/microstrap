with open("helper/executables/dir_tree.py", "rb") as file:
    TREE_DIR = file.read()

with open("helper/executables/write_file.py", "rb") as file:
    WRITE_FILE = file.read()


CANCEL = b"\x03"    # Ctrl+C
REBOOT = b"\x04"    # Ctrl+D
RAW_MODE = b"\x05"  # Ctrl+E

from .serial import Connection