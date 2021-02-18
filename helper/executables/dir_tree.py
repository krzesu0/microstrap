import os

files = []
directories = set()

def list_dir(name):
    items = []
    for item in os.listdir(name):
        items.append(name + "/" + item)
        directories.add(name)
    return items

def generate(_list):
    for item in _list:
        try:
            if "." in item[1:]:
                files.append(item)
            else:
                generate(list_dir(item))
        except OSError:
            files.append(item)

generate(".")
for item in files:
    print("f ", end="")
    print(item)

for item in directories:
    print("d ", end="")
    print(item)

del files
del directories
del list_dir
del generate
