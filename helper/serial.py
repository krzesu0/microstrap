from serial import Serial
from time import sleep
from typing import List, Tuple

from . import TREE_DIR, WRITE_FILE, CANCEL, REBOOT, RAW_MODE

class Connection:
    _past = False
    def __init__(self, COM: str, initiate: bool = True, debug: bool = False, do_before_restart: bytes = b''):
        self.debug = debug
        self.connection = Serial(COM, 115200, bytesize=8, parity="N", stopbits=1,\
                                 xonxoff=1, timeout=0.1, rtscts=False, dsrdtr=False)

        if do_before_restart:
            # sometimes we need to run some code before we reboot/soft_flash
            self.write(CANCEL)
            self.write(do_before_restart)
            self.connection.read(115200)

        if initiate:
            # reboot, give some time to print all the garbage, and read it
            self.soft_restart()
            self.connection.read(115200)
            sleep(0.2)
            # just to be sure its listening...
            self.write(CANCEL)
            self.write(CANCEL)
            self.write(CANCEL)
            sleep(0.2)
            self.connection.read(115200)

    def write(self, data: bytes) -> int:
        "Write data to the device, prints debug info if debug flag is set"
        if self.debug:
            print("-> " + str(data))
        return self.connection.write(data)

    def read(self, amount: int = 0) -> bytes:
        "Read data from the device, print written data to stdout if debug flag is set"
        data = self.connection.read(amount)
        if self.debug:
            print("<- ", end="")
            print(data)
        return data

    def write_in_paste_mode(self, data: bytes):
        "Write data to device and read it back with the padding created by paste mode"
        sum = 0
        self.read(1000)
        for line in data.split(b"\r\n"):
            sum += self.write(line + b"\r\n")
            self.read(len(line) + 7)
        # usually write returns amount of data written
        return sum
    
    def soft_restart(self) -> None:
        self.write(REBOOT)

    def readline(self) -> bytes:
        data = self.connection.readline()
        if self.debug:
            print("<- ", end="")
            print(data)
        return data

    def prepare_paste_mode(self) -> None:
        "Prepare device for data input in paste_mode"
        if not self._past:
            self.write(CANCEL)
            self.write(b"\r\n")
            self.write(RAW_MODE)
            # making sure
            self._past = True
            data = self.read(1000)
            if not b"\r\npaste mode" in data or data.startswith(b"==="):
                if self.debug:
                    print(data)
                self.write(b"\r\n")
                data = self.read(1000)
                if not b"\r\npaste mode" in data or data.startswith(b"==="):
                    print(data)
                    # FIXME: Random IOErrors while trying to softflash
                    raise IOError("Couldnt start raw mode.")
        else:
            self.exit_paste_mode()
            self.prepare_paste_mode()
    
    def exit_paste_mode(self) -> None:
        if self._past:
            self.write(REBOOT)
            self._past = False
            self.read(2)

    def get_files(self) -> Tuple[List[str], List[str]]:
        "get files in main directory"
        files = []
        directories = []
        print("Downloading file listing.")
        # we use the small executables inside of ./executables/ to perform basic tasks
        # here we upload the small script to printout the flash contents
        self.prepare_paste_mode()
        self.write_in_paste_mode(TREE_DIR)
        self.exit_paste_mode()
        # sort incoming data
        while b">>> " not in (item := self.readline()):
            if item.startswith(b"d "):
                directories.append(item[2:].strip())
            elif item.startswith(b"f "):
                files.append(item[2:].strip())
            elif item == b"":
                continue
            else:
                print("The fuck is this? ", end="")
                print(item)
        print("Done!")
        # remove the b'.' directory
        directories = [x for x in directories if x != b'.']
        if self.debug:
            print(files, directories)
        return files, directories

    def remove_file(self, path: bytes, force: bool = True) -> None:
        "Remove remote file."
        if type(path) is not bytes:
            path = bytes(path, "utf-8")
        # we use bool force to speed up file removal
        # when force is false, it check if the file exist
        if force or path in (files := self.get_files()[0]):
            print(f"Removing file: {str(path, 'utf-8')}")
            self.prepare_paste_mode()
            # too small "executable" to move it to its own file
            self.write_in_paste_mode(b"import os\r\nos.remove('" + path + b"')")
            self.exit_paste_mode()
            sleep(0.2)
            # just to make sure it is succesfully deleted

    def write_file(self, filename: str, dest_filename: bytes):
        files = self.get_files()[0]
        # TODO: implement something to check if the file was even changed
        # and decide whether to remove it or keep it
        if dest_filename in files:
            self.remove_file(dest_filename)
        
        self.prepare_paste_mode()
        # create append on the remote device
        self.write_in_paste_mode(WRITE_FILE)
        self.exit_paste_mode()

        with open(filename, "rb") as file:
            print(f"Writing file {str(dest_filename, 'utf-8')}:", end="")
            while (data := file.read(500)) != b"":
                self.prepare_paste_mode()
                # bytes(str(data)) creates string containing binary literal
                # data => b'\x03\x14asd'
                # str(data) => "b'\x03\x14asd'"
                # bytes(str(data)) => b"""b'\x03\x14asd'"""
                self.write_in_paste_mode(b"append('" + dest_filename + b"'," + bytes(str(data), "utf-8") + b")")
                self.exit_paste_mode()
                print(".", end="")
        print("\nFile written!")
        self.prepare_paste_mode()
        self.write_in_paste_mode(b"del append")
        # we remove the append function to save memory
        self.exit_paste_mode()

    def mkdir(self, dirname: str):
        print(f"Creating directory {dirname}")
        self.prepare_paste_mode()
        self.write_in_paste_mode(bytes(f"import os\r\nos.mkdir('{dirname}')\r\n", "utf-8"))
        self.exit_paste_mode()

    def download_file(self, filename: bytes, destfilename: str):
        print("Downloading file:", filename)
        self.prepare_paste_mode()
        # TODO: this will only work if we are downloading txt file
        self.write_in_paste_mode(bytes(f"print(open('{filename.decode('utf-8')}').read())", "utf-8"))
        self.exit_paste_mode()

        with open(destfilename, "wb") as file:
            # while the line doesnt start with >>>
            # keep appending data to destfile
            while b">>>" not in (data := self.readline()):
                file.write(data.split(b'\r\n')[0])
