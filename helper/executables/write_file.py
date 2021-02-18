def append(file, contents):
    with open(file, "ab") as file:
        file.write(contents)