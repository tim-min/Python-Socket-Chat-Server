import socket
import threading
import csv
import json
from logo import print_logo


class Client:
    def __init__(self, conn, address) -> None:
        self.conn = conn
        self.address = address
        self.room_name = "" # users current room
        self.is_admin = False
        self.username = ""
        self.pm_closed = False
    
    def get_info(self):
        return [self.conn, self.address, self.room_name, self.is_admin] # ok

class Room:
    def __init__(self, name, creator) -> None:
        self.name = name
        self.creator = creator
        self.members = list()
    
    def send_message(self, message): # sending something to all users
        for member in self.members:
            member.conn.send(bytes(f"[Room Chat] {message}", encoding="utf-8"))


class Server:
    def __init__(self, host, port, adm_password, adm_login) -> None:
        self.sock = socket.socket()
        self.sock.bind((host, port))
        self.sock.listen(1)
        self.adm_password, self.adm_login = adm_password, adm_login # admin password and login from settings.json
        self.clients = list() # online clients
        self.rooms = list() # online rooms
        self.room_names = list() # online room names
        self.new_cons_thread = threading.Thread(target=self.get_new_connections) # thread to check new connections
        self.client_threads = list() # threads list to listen clients
        self.new_cons_thread.start()
        self.users_base = dict() # usernames and passwords

        self.commands = { # commands list
            "room": self.SetRoomToUser,
            "create_room": self.CreateRoom,
            "alogin": self.AdminLogin,
            "rchat": self.RoomChat,
            "cancel_room": self.CancelRoom,
            "get_rooms": self.GetRoomNames,
            "my_room": self.GetMyRoom,
            "logout": self.logout,
            "stats": self.stats,
            "message": self.message,
            "close_open_pm": self.close_pm
        }
        self.admin_commands = { # admin commands list
            "all_clients": self.GetAllClients,
            "delete_room": self.DeleteRoom
        }
        self.get_users() # get users list from csv file
    
    def close_pm(self, args, client):
        client.pm_closed = not client.pm_closed
        return 1

    def message(self, args, client): # personal message to user
        if len(args) < 2:
            return "[Error] Incorrect arguments!"
        if args[0] not in [client.username for client in self.clients]:
            return "[Error] User should be online!"
        target = [client for client in self.clients if client.username == args[0]][0]
        if target.pm_closed:
            return "[Error] User closed his personal messages chat!"
        target.conn.send(bytes(f"[PersonalMessage] ({client.username}) - {' '.join(args[1:])}", encoding="utf-8"))
        return 1

    def DeleteRoom(self, args, client):
        if len(args) < 1 or args[0] not in self.room_names:
            return "[Error] Incorrect arguments or room not found!"
        room_index = self.room_names.index(args[0])
        self.CancelRoom([], self.rooms[room_index].creator)
        return 1

    def stats(self, args, client):
        client.conn.send(bytes(f" Username - [{client.username}]\nCurrent room - [{client.room_name}]\n Admin level - [{int(client.is_admin)}]", encoding="utf-8"))
        return 2

    def logout(self, args, client):
        if client.room_name:
            self.CancelRoom([], client)
        client.username = ""
        return 1

    def GetMyRoom(self, args, client):
        if not client.room_name:
            return "[Error] You don't have a room!"
        client.conn.send(bytes(f"[Info] Your room is '{client.room_name}'", encoding="utf-8"))
        return 2

    def CancelRoom(self, args, client): # cancel room command
        if not client.room_name:
            return "[Error] You are not in the room!"
        room_index = self.room_names.index(client.room_name)
        self.rooms[room_index].members.remove(client) # remove user from room users list
        client.room_name = ""
        if self.rooms[room_index].creator == client: # if user was creator of the room, delete this room!
            self.rooms[room_index].send_message("(System) - You was removed from your room becouse room creator canceled this room or room was deleted by admin!")
            print(f"[ROOM DELETED] Room name - {self.rooms[room_index].name}, Creator - {self.rooms[room_index].creator.username}")
            for member in self.rooms[room_index].members:
                member.room_name = ""
            del self.rooms[room_index]
            del self.room_names[room_index]
        return 1 # 1 for success
    
    def GetRoomNames(self, args, client): # get all available rooms!
        answer = list()
        for room_index, room in enumerate(self.room_names):
            answer.append(f"Name: {room}|Members: {len(self.rooms[room_index].members)}|Creator: {self.rooms[room_index].creator.username}")
        client.conn.send(bytes("[RoomList]" + ";".join(answer), encoding="utf-8"))
        return 2 # 2 for empty message

    def CreateRoom(self, args, client): # create room
        if len(args) < 1 or args[0] in self.room_names:
            return "[Error] Incorrect arguments or room with this name already exists!"
        if client.room_name:
            return "[Error] You already have a room!"
        room = Room(args[0], client)
        client.room_name = args[0]
        self.room_names.append(args[0])
        self.rooms.append(room)
        self.rooms[-1].members.append(client)
        print(f"[NEW ROOM CREATED] Room - {self.room_names[-1]}, Creator - {self.rooms[-1].creator.username}")
        return 1
    
    def RoomChat(self, args, client):
        if len(args) < 1 or client.room_name == "":
            return "[Error] Incorrect arguments or you don't have a room!"
        
        room_index = self.room_names.index(client.room_name)
        self.rooms[room_index].send_message(f'({client.username}) - {" ".join(args)}')
        return 2
        

    def AdminLogin(self, args, client):
        if len(args) < 2:
            return "[Error] Incorrect arguments!"
        if (args[0] == self.adm_login and args[1] == self.adm_password):
            client.is_admin = True
            return 1
        return "[Error] Incorrect login or password!"
    
    def SetRoomToUser(self, args, client):
        if len(args) < 1 or args[0] not in self.room_names:
            return "[Error] Args are incorrect or room not find!"
        if client.room_name:
            return "[Error] You already in the room!"
        client.room_name = args[0]
        room_index = self.room_names.index(args[0])
        self.rooms[room_index].send_message(f"(System) - {client.username} joined your room!")
        self.rooms[room_index].members.append(client)
        return 1
    
    def GetAllClients(self, args, client):
        client.conn.send(bytes(str([client.get_info() for client in self.clients]), encoding="utf-8"))
        return 2
    
    def get_new_connections(self): # check for new connections
        while True:
            conn, address = self.sock.accept()
            print("[NEW USER CONNECTED]", conn, address)
            client = Client(conn, address)
            self.clients.append(client)
            self.client_threads.append(threading.Thread(target=lambda: self.listen_commands(client)))
            self.client_threads[-1].start()
    
    def start(self):
        print("Server started!")

    def get_users(self):
        with open('users.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in reader:
                self.users_base[row[0]] = row[1:]
        #print(self.users_base)
    
    def update_users(self): # update users base (users.csv)
        with open('users.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for key, user in self.users_base.items():
                writer.writerow([key, user[0], user[1]])
    
    def listen_commands(self, client): # listening commands from user
        while True:
            try:
                data = client.conn.recv(1024).decode("utf-8")
                data = data.split(":")

                if not client.username:
                    if data[0].split()[0] == "login":
                        if len(data[0].split()) < 3:
                            client.conn.send(b"[Error] Arguments are incorrect!")
                            continue
                        username, password = data[0].split()[1], data[0].split()[2]
                        if self.users_base.get(username):
                            if username in [client.username for client in self.clients]:
                                client.conn.send(b"[LoginError] Someone with this name already online!")
                                continue
                            if self.users_base[username][0] == password:
                                client.username = username
                                client.conn.send(bytes(f"[Login:{username}] Welcome back, {username}!", encoding="utf-8"))
                                continue
                            else:
                                client.conn.send(b"[LoginError] Login or password are incorrect!")
                                continue
                        else:
                            client.conn.send(b"[LoginError] User not found!")
                            continue
                    elif data[0].split()[0] == "register":
                        if len(data[0].split()) < 3:
                            client.conn.send(b"[Error] Arguments are incorrect!")
                            continue
                        username, password = data[0].split()[1], data[0].split()[2]
                        if self.users_base.get(username):
                            client.conn.send(b"[Error] User already exist!")
                            continue
                        self.users_base[username] = [password, 0]
                        self.update_users()
                        client.conn.send(b"[Ok] Success! Use login now!")
                        continue
                    else:
                        client.conn.send(b"[Error] You are not logged in!")
                        continue

                success = 1

                for command in data:
                    command = command.split()
                    if self.commands.get(command[0]):
                        success = self.commands[command[0]](command[1:], client)
                    elif self.admin_commands.get(command[0]) and client.is_admin:
                        success = self.admin_commands[command[0]](command[1:], client)
                    else:
                        success = "[Error] Command not found or arguments are incorrect or you are trying to use login or register command :("

                if success == 1:
                    client.conn.send(b"[Ok] Success!")
                elif success != 2: # 2 for emty message, 1 for success, other is error message
                    client.conn.send(bytes(success, encoding="utf-8"))
            except ConnectionResetError: # if client disconnected, delete him)
                client_index = self.clients.index(client)
                print(f"[CLIENT DISCONNECTED] username - {client.username}")
                self.CancelRoom('', client)
                self.clients.remove(client)
                del self.client_threads[client_index]
                break

def get_server_settings(settings_file):
    with open(settings_file, "r") as file:
        data = json.load(file)

    return data

if __name__ == "__main__":
    settings = get_server_settings("settings.json")
    print_logo()
    server = Server(settings[1]["host"], settings[1]["port"], settings[0]["admin_password"], settings[0]["admin_login"])
    server.start()
