from helper import Connection
import sys, time

TARGET_DIR = "src/"

debug = bool(int(sys.argv[1]))
com = sys.argv[2]
files = sys.argv[3:]

conn = Connection(com, debug=debug)
for source_file in files:
    assert source_file.startswith(TARGET_DIR)
    source_file = source_file.replace(TARGET_DIR, "./")
    path = source_file.split("/")
    assert path[0] == "."
    for directory in path[1:-1]:
        conn.mkdir(directory)
    dest_file = bytes(source_file, "utf-8")
    conn.write_file(TARGET_DIR + source_file, dest_file)

conn.soft_restart()
print("Done! Have a nice day.")