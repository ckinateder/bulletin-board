# echo-server.py

from threading import Thread
import socket
import time
import selectors
import types

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 64538 # Port to listen on (non-privileged ports are > 1023)

class Message:
    """Message object. Contains sender and content.
    """
    def __init__(self, sender, content):
        self.sender = sender
        self.content = content

class Log:
    """Hold a log of what happens
    """
    def __init__(self):
        self.log = []

    def add(self, id:str, type:str, data=None):
        self.log.append({id: {"time": time.time(), "type": type, "data": data}})
    
    def __str__(self):
        s = "ConnectionsLog(log=[\n"
        for entry in self.log:
            s += f"  {entry}\n"
        s += "])"
        return s

class UserContainer:
    """Container for users. Contains methods for adding, removing, and getting users.
    """
    def __init__(self):
        self.users = []
    
    def add_user(self, user):
        self.users.append(user)
        print(self.users)
    
    def remove_user(self, user):
        for u in self.users:
            if u.id == user.id:
                self.users.remove(user)

    def get_user_by_id(self, userid):
        for user in self.users:
            if user.id == userid:
                return user
        return None

    def get_user_by_username(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def get_all_users(self):
        return self.users

    def get_all_usernames(self):
        return [user.username for user in self.users]
    
    def __str__(self):
        return f"UserContainer(users={self.users})"

    def __iter__(self):
        return iter(self.users)

class User:
    """User object. Contains username, socket, and id.
    """
    def __init__(self, username, sock):
        self.username = username
        self.socket = sock
        self.id = hex(hash(str(time.time())+username))

    def __str__(self):
        return f"User(username={self.username}, socket={self.socket}, id={self.id})"

class Board:
    """Bulletin board object. Contains messages and users.
    """
    def __init__(self, name):
        self.name = name
        self.messages = []
        self.users = UserContainer() # users who are currently viewing this board

    def send_to_all_clients(self, data):
        for u in self.users:
            send_to_client(u.socket, data)

class Lobby:
    """Contains all bulletin boards. 
    """
    def __init__(self):
        self.users = UserContainer()
        self.log = Log()
        self.boards = []

    def new_board(self, name):
        self.boards.append(Board(name))

def send_to_client(client_socket, data):
    """Sends data to a client.
    """
    client_socket.sendall(data.encode())
    print(f"Sent '{data}' to {client_socket.getpeername()}")


def on_new_client(client_socket, addr, lobby: Lobby):
    user = None
    while True:
        # receive data from client
        data = client_socket.recv(1024).decode('utf-8').strip()
        if not data:
            break

        # show what was said
        if user:
            print(f"{user.username} >> {data}")
        else:
            print(f"{addr} >> {data}")
        
        # handle commands
        if data[:5] == "/user":
            username = data[6:].strip()
            if username in lobby.users.get_all_usernames() or username == "": # unsuccessful
                send_to_client(client_socket, f"/fail {' '.join(lobby.users)}")
                break
            else: # successful
                user = User(username, client_socket)
                lobby.users.add_user(user)
                send_to_client(client_socket, f"/success {user.id}")
                lobby.log.add(user.id, "connect")

    # close the connection
    client_socket.close()

    # if the user was logged in, remove them from the users list and log the disconnection
    if user:
        lobby.users.remove_user(user)
        lobby.log.add(user.id, "disconnect")
    print(f"Connection from {addr} closed.")
    print(f"users: {lobby.users}")
    print(lobby.log)


def main(lobby: Lobby):
    s = socket.socket()
    s.bind((HOST, PORT))  # bind the socket to the port and ip address

    s.listen(5)  # wait for new connections

    while True:
        c, addr = s.accept()  # Establish connection with client.
        # this returns a new socket object and the IP address of the client
        print(f"New connection from: {addr}")
        c.sendall("".encode())
        thread = Thread(target=on_new_client, args=(
            c, addr, lobby))  # create the thread
        thread.start()  # start the thread
    c.close()
    thread.join()


if __name__ == '__main__':
    boards = Lobby()
    boards.new_board("general")
    main(boards)
