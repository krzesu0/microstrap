from helper import Connection
from hashlib import sha1
import sys, time

TARGET_DIR = "src/"

debug = bool(int(sys.argv[1]))
com = sys.argv[2]
files_to_flash = sys.argv[3:]

conn = Connection(com, debug=debug)

if files_to_flash:
    files, directories, file_hashes = conn.get_files()

for source_file in files_to_flash:
    assert source_file.startswith(TARGET_DIR)
    # create hash for comparison later
    with open(source_file, "rb") as file:
        hash_ = sha1()
        hash_.update(file.read())
        file_hash = hash_.digest() 
    
    source_file = source_file.replace(TARGET_DIR, "./")
    path = source_file.split("/")

    if "/".join(path[:-1]) not in directories:
        # if the directory doesnt exist create it
        for i, _ in enumerate(path[1:-1]):
            dir_structure = "/".join(path[1:i+2])
            # create directory step by step
            # if the structure looks like foo/bar/asd/dsa/.../
            # create foo/, create foo/bar/, create foo/bar/asd/
            # ...
            if "./" + dir_structure not in directories:
                # skip existing directories
                conn.mkdir(dir_structure)
                # add newly created directories to list to prevent
                # creating the same directory multiple times
                directories.append("./"+dir_structure)

    dest_file = bytes(source_file, "utf-8")
    
    if source_file in files:
        if file_hash not in file_hashes:
            conn.write_file(TARGET_DIR + source_file, dest_file, True)
        else:
            print(f"Current version of {source_file} is present. Skiping...")
    else:
            dest_file = bytes(source_file, "utf-8")
            conn.write_file(TARGET_DIR + source_file, dest_file, False)

conn.soft_restart()
print("Done! Have a nice day.")