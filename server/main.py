# echo-server.py

from threading import Thread
import socket
import time
import selectors
import types

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 64438 # Port to listen on (non-privileged ports are > 1023)

# this is the current list of users on the server.
users = {} # id: {username: username, socket: socket}
# realtime log of connections and disconnections. {id: {time: time, type: connect/disconnect}}
connections_log = []

def get_all_connected_usernames()->list:
    u = []
    for user in users.values():
        u.append(user["username"])
    return u

def send_to_client(client_socket, data):
    client_socket.sendall(data.encode())
    print(f"Sent '{data}' to {client_socket.getpeername()}")

def send_to_all_clients(data):
    for u in users.values():
        send_to_client(u["socket"], data)

def on_new_client(client_socket, addr):
    hsh = None
    while True:
        # receive data from client
        data = client_socket.recv(1024).decode('utf-8').strip()
        if not data:
            break

        # show what was said
        if hsh:
            print(f"{users[hsh]} >> {data}")
        else:
            print(f"{addr} >> {data}")
        
        # handle commands
        if data[:5] == "/user":
            username = data[6:].strip()
            if username in get_all_connected_usernames() or username == "": # unsuccessful
                send_to_client(client_socket, f"/fail {' '.join(users)}")
                break
            else: # successful
                hsh = hex(hash(str(time.time())+username))
                users[hsh] = {"username": username, "socket": client_socket}
                send_to_client(client_socket, f"/success {hsh}")
                connections_log.append({"id": {"time": time.time(), "type": "connect"}})

    # close the connection
    client_socket.close()

    # if the user was logged in, remove them from the users list and log the disconnection
    if hsh:
        del users[hsh]
        connections_log.append({"id": {"time": time.time(), "type": "disconnect"}})
    print(f"Connection from {addr} closed.")
    print(f"users: {users}")
    print(f"connections_log: {connections_log}")


def main():
    s = socket.socket()
    s.bind((HOST, PORT))  # bind the socket to the port and ip address

    s.listen(5)  # wait for new connections

    while True:
        c, addr = s.accept()  # Establish connection with client.
        # this returns a new socket object and the IP address of the client
        print(f"New connection from: {addr}")
        c.sendall("".encode())
        thread = Thread(target=on_new_client, args=(
            c, addr))  # create the thread
        thread.start()  # start the thread
    c.close()
    thread.join()


if __name__ == '__main__':
    main()
