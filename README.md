# Python-Socket-Chat-Server
Server on python to chat with your friends)

<img src="https://i.imgur.com/pqrvq1P.png">

<h3>server settings:</h3>
edit server/settings.json file to change server host, port, admin login and password <br>

<h3>server commands:</h3>
<h4> Common commands: </h4>
login [username] [password] - login <br>
register [username] [password] - registration <br>
logout - logout <br>
alogin [username] [password] - login as admin (only after login) <br>
stats - account stats (username, current room, admin level) <br>
message [user] [text] - personal message to user <br>
create_room [room_name] - create new chat room <br>
room [room_name] - join chat room <br>
cancel_room - cancel chat room <br>
rchat [text] - room chat <br>
close_open_pm - close or open personal messages <br>
my_room - shows your current room <br>
<h4> Admin commands </h4>
all_clients - get list of online clients <br>
delete_room [room_name] - delete room <br>

<h3> Client commands: </h3>
help - commands list <br>
clear - clear console <br>

