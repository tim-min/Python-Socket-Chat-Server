def print_logo():
    with open("logo.txt", "r") as file:
            for line in file.readlines():
                print(line)
