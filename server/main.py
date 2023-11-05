# echo-server.py

from threading import Thread
import socket
import selectors
import types

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65439 # Port to listen on (non-privileged ports are > 1023)

users = []

def send_to_client(client_socket, data):
    client_socket.sendall(data.encode())
    print(f"Sent '{data}' to {client_socket.getpeername()}")

def on_new_client(client_socket, addr):
    username = ""
    while True:
        data = client_socket.recv(1024).decode('utf-8').strip()
        if not data:
            break
        print(f"{addr} >> {data}")
        if data[:5] == "/user":
            username = data[6:].strip()
            if username in users or username == "":
                send_to_client(client_socket, f"/fail {' '.join(users)}")
                break
            else:
                users.append(username.strip())
                send_to_client(client_socket, f"/success {username}")
    client_socket.close()
    users.remove(username)
    print(f"Connection from {addr} closed.")


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
