from helper import Connection
import sys, os

TARGET_DIR = "dest/"

debug = bool(int(sys.argv[1]))
com = sys.argv[2]

conn = Connection(com, debug=debug)
files, directories = conn.get_files()
print(directories)
for directory in directories:
    os.makedirs(TARGET_DIR + directory.decode("utf-8"), exist_ok=True)

for file in files:
    conn.download_file(file, TARGET_DIR + file.decode("utf-8"))