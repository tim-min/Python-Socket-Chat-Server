import threading
import socket
import os
from logo import print_logo
import hashlib

# --------------------- CONSOLE CLIENT -----------------------


class Client:
    def __init__(self, host, port) -> None:
        self.sock = socket.socket()
        self.sock.connect((host, int(port)))
        self.listen_thread = threading.Thread(target=self.listen) # thread for getting answers from server
        self.listen_thread.start()
        self.commands_thread = threading.Thread(target=self.commands) # thread for console commands (you can remove it)
        self.commands_thread.start()
        self.client_commands = { # !login and register are client commands because we need to generate password hash!
            "help": self.get_help,
            "clear": self.clear_console,
            "login": self.login,
            "register": self.register
        }
        print("New command: (help for help, clear to clear)")
    
    def login(self, args):
        if len(args) < 2:
            print("[Error] Incorrect arguments. Use login username password")
            return
        args[1] = hashlib.md5(args[1].encode()).hexdigest()
        self.sock.send(bytes(f"login {args[0]} {args[1]}", encoding="utf-8"))

    
    def register(self, args):
        if len(args) < 2:
            print("[Error] Incorrect arguments. Use register username password")
            return
        args[1] = hashlib.md5(args[1].encode()).hexdigest()
        self.sock.send(bytes(f"register {args[0]} {args[1]}", encoding="utf-8"))

    def get_help(self, args):
        print("\n")
        print("HELP: \n")
        with open("help.txt", "r") as file:
            for line in file.readlines():
                print(line)
        print("\n\n")

    def clear_console(self, args):
        os.system("cls")
        print_logo()
        print("New command: (help for help, clear to clear)")

    def commands(self): # CONSOLE commands
        while True:
            message = input()
            if self.client_commands.get(message.split()[0]):
                self.client_commands[message.split()[0]](message.split()[1:])
                continue # ignore server check command
            self.sock.send(bytes(message, encoding="utf-8"))
    
    def listen(self): # waiting data from server
        while True:
            data = self.sock.recv(1024)
            data = data.decode("utf-8")
            print(data)


if __name__ == "__main__":
    print_logo()
    client = Client(input("Host: "), input("Port: "))
