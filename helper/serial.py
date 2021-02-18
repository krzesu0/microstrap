from serial import Serial
from time import sleep

from . import TREE_DIR, WRITE_FILE, CANCEL, REBOOT, RAW_MODE

class Connection:
    _past = False
    def __init__(self, COM: str, initiate: bool = True, debug: bool = False, do_before_restart: bytes = b''):
        self.debug = debug
        self.connection = Serial(COM, 115200, bytesize=8, parity="N", stopbits=1,\
                                 xonxoff=1, timeout=0.1, rtscts=False, dsrdtr=False)

        if do_before_restart:
            self.write(CANCEL)
            self.write(do_before_restart)
            self.connection.read(115200)

        if initiate:
            # reboot, give some time to print all the garbage, and read it
            self.write(REBOOT)
            self.connection.read(115200)
            sleep(0.2)
            self.write(CANCEL)
            self.write(CANCEL)
            self.write(CANCEL)
            sleep(0.2)
            self.connection.read(115200)

    def write(self, data: bytes):
        if self.debug:
            print("-> " + str(data))
        return self.connection.write(data)

    def read(self, amount: int = 0) -> bytes:
        data = self.connection.read(amount)
        if self.debug:
            print("<- ", end="")
            print(data)
        return data

    def write_in_paste_mode(self, data: bytes):
        sum = 0
        self.read(1000)
        for line in data.split(b"\r\n"):
            sum += self.write(line + b"\r\n")
            self.read(len(line) + 7)
        return sum
    
    def soft_restart(self):
        self.write(REBOOT)

    def readline(self):
        data = self.connection.readline()
        if self.debug:
            print("<- ", end="")
            print(data)
        return data

    def prepare_paste_mode(self):
        if not self._past:
            self.write(CANCEL)
            self.write(b"\r\n")
            self.write(RAW_MODE)
            self._past = True
            data = self.read(1000)
            if not b"\r\npaste mode" in data or data.startswith(b"==="):
                if self.debug:
                    print(data)
                self.write(b"\r\n")
                data = self.read(1000)
                if not b"\r\npaste mode" in data or data.startswith(b"==="):
                    print(data)
                    raise IOError("Couldnt start raw mode.")
        else:
            self.exit_paste_mode()
            self.prepare_paste_mode()
    
    def exit_paste_mode(self):
        if self._past:
            self.write(REBOOT)
            self._past = False
            self.read(2)

    def get_files(self):
        # get files in main directory
        files = []
        directories = []
        print("Downloading file listing.")
        self.prepare_paste_mode()
        self.write_in_paste_mode(TREE_DIR)
        self.exit_paste_mode()
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
        directories = [x for x in directories if x != b'.']
        if self.debug:
            print(files, directories)
        return files, directories

    def remove_file(self, path: bytes, force: bool = True):
        if type(path) is not bytes:
            path = bytes(path, "utf-8")
        if force or path in (files := self.get_files()[0]):
            print(f"Removing file: {str(path, 'utf-8')}")
            self.prepare_paste_mode()
            self.write_in_paste_mode(b"os.remove('" + path + b"')")
            self.exit_paste_mode()
            sleep(1)

    def write_file(self, filename: str, dest_filename: bytes):
        files = self.get_files()[0]
        if dest_filename in files:
            self.remove_file(dest_filename)
        
        self.prepare_paste_mode()
        self.write_in_paste_mode(WRITE_FILE)
        self.exit_paste_mode()

        with open(filename, "rb") as file:
            print(f"Writing file {str(dest_filename, 'utf-8')}:", end="")
            while (data := file.read(500)) != b"":
                self.prepare_paste_mode()
                self.write_in_paste_mode(b"append('" + dest_filename + b"'," + bytes(str(data), "utf-8") + b")")
                self.exit_paste_mode()
                print(".", end="")
        print("\nFile written!")
        self.prepare_paste_mode()
        self.write_in_paste_mode(b"del append")
        self.exit_paste_mode()

    def mkdir(self, dirname: str):
        print(f"Creating directory {dirname}")
        self.prepare_paste_mode()
        self.write_in_paste_mode(bytes(f"os.mkdir('{dirname}')\r\n", "utf-8"))
        self.exit_paste_mode()

    def download_file(self, filename: bytes, destfilename: str):
        print("Downloading file:", filename)
        self.prepare_paste_mode()
        self.write_in_paste_mode(bytes(f"print(open('{filename.decode('utf-8')}').read())", "utf-8"))
        self.exit_paste_mode()

        with open(destfilename, "wb") as file:
            while b">>>" not in (data := self.readline()):
                file.write(data.split(b'\r\n')[0])
