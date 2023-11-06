# echo-server.py

from threading import Thread
import socket
import time
import argparse
import sys

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 64538  # Port to listen on (non-privileged ports are > 1023)


class Message:
    """Message object. Contains sender and content."""

    def __init__(self, sender, content):
        self.sender = sender
        self.content = content
        self.time = time.time()


class Log:
    """Hold a log of what happens"""

    def __init__(self):
        self.log = []

    def add(self, id: str, type: str, data: str = None, echo=True):
        """Add an entry to the log.

        Args:
            id (str): id
            type (str): type of entry
            data (str, optional): any extra info. Defaults to None.
        """
        record = {id: {"time": time.time(), "type": type, "data": data}}
        self.log.append(record)
        if echo:
            print(f"{record}")

    def __str__(self):
        s = "ConnectionsLog(log=[\n"
        for entry in self.log:
            s += f"  {entry}\n"
        s += "])"
        return s


class User:
    """User object. Contains username, socket, and id."""

    def __init__(self, username: str, sock: socket.socket):
        self.username = username
        self.socket = sock
        self.id = hex(hash(str(time.time()) + username))

    def __str__(self):
        return f"User(username={self.username}, id={self.id})"


class UserContainer:
    """Container for users. Contains methods for adding, removing, and getting users."""

    def __init__(self):
        self.users = []

    def add_user(self, user: User):
        self.users.append(user)

    def remove_user(self, user: User):
        for u in self.users:
            if u.id == user.id:
                self.users.remove(user)

    def get_user_by_id(self, userid: str):
        for user in self.users:
            if user.id == userid:
                return user
        return None

    def get_user_by_username(self, username: str):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def get_all_users(self):
        return self.users

    def get_all_usernames(self):
        return [user.username for user in self.users]

    def __str__(self):
        if len(self.users) == 0:
            return "UserContainer(users=[])"
        s = "UserContainer(users=[\n"
        for entry in self.users:
            s += f"  {entry}\n"
        s += "])"
        return s

    def __iter__(self):
        return iter(self.users)


class Board:
    """Bulletin board object. Contains messages and users."""

    def __init__(self, name: str):
        self.name = name
        self.messages = []
        self.users = UserContainer()  # users who are currently viewing this board

    def send_to_all_clients(self, data: str):
        for u in self.users:
            send_to_client(u.socket, data)


class Lobby:
    """Contains all bulletin boards."""

    def __init__(self):
        self.users = UserContainer()
        self.log = Log()
        self.boards = []

    def new_board(self, name: str):
        self.boards.append(Board(name))


def send_to_client(client_socket: socket.socket, data: str):
    """Sends data to a client."""
    client_socket.sendall(data.encode())
    print(f"Sent '{data}' to {client_socket.getpeername()}")


def on_new_client(client_socket: socket.socket, addr: tuple, lobby: Lobby): # one thread per user
    user = None
    while True:
        # receive data from client
        data = client_socket.recv(1024).decode("utf-8").strip()
        if not data:
            break

        # show what was said
        if user:
            print(f"{user.username} >> {data}")
        else:
            print(f"{addr} >> {data}")

        # handle commands
        if data[:8] == "/newuser":
            username = data[9:].strip()
            if (
                username in lobby.users.get_all_usernames() or username == ""
            ):  # unsuccessful

                send_to_client(client_socket, f"/fail {' '.join(lobby.users.get_all_usernames())}")
            else:  # successful
                user = User(username, client_socket)
                lobby.users.add_user(user)
                send_to_client(client_socket, f"/success {username}:{user.id}")
                lobby.log.add(user.id, "connect", user.username)
        if data[:8] == "/chguser":
            info = data[9:].strip()
            username, userid = info.split(":")
            if user.id != userid: # unsuccessful
                send_to_client(client_socket, f"/fail {user.username}")
            elif (
                username in lobby.users.get_all_usernames() or username == ""
            ):
                send_to_client(client_socket, f"/fail {' '.join(lobby.users.get_all_usernames())}")
            else:
                user.username = username
                send_to_client(client_socket, f"/success {username}:{user.id}")
                lobby.log.add(user.id, "username_change", username)

        elif data[:5] == "/join":
            board_name = data[6:].strip()


    # close the connection
    client_socket.close()

    # if the user was logged in, remove them from the users list and log the disconnection
    if user:
        lobby.users.remove_user(user)
        lobby.log.add(user.id, "disconnect", user.username)
    print(f"Connection from {addr} closed.")
    print(f"users: {lobby.users}")
    print(lobby.log)


def main(host: str, port: int, lobby: Lobby):
    """Runs the server.

    Args:
        host (str): host
        port (int): port
        lobby (Lobby): lobby
    """
    s = socket.socket()
    s.bind((host, port))  # bind the socket to the port and ip address

    s.listen(5)  # wait for new connections

    try:
        while True:
            c, addr = s.accept()  # Establish connection with client.
            # this returns a new socket object and the IP address of the client
            print(f"New connection from: {addr}")
            c.sendall("".encode())
            thread = Thread(
                target=on_new_client, args=(c, addr, lobby)
            )  # create the thread
            thread.start()  # start the thread
        c.close()
        thread.join()
    except KeyboardInterrupt:
        print("Closing server...")
        s.close()
    print(lobby.log)

if __name__ == "__main__":
    # set the args
    parser = argparse.ArgumentParser(
        prog="Bulletin Board Server",
        description="Runs a server for a bulletin board.",
        epilog="See the README for more information.",
    )
    parser.add_argument("-H", "--host", type=str, required=True)
    parser.add_argument("-P", "--port", type=int, required=True)

    # parse the arguments
    args = parser.parse_args()

    # add into environment variables
    with open(".env", "w+", encoding="utf-8") as f:
        f.write(f"{args.host}:{args.port}\n")

    # create the lobby and add a default board
    boards = Lobby()
    boards.new_board("default")

    # run the server
    print(f"Welcome to the Bulletin Board Server! Listening on {args.host}:{args.port}...")
    main(args.host, args.port, boards)
