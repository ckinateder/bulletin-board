# echo-server.py

import sys
import socket
import selectors
import types

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65431  # Port to listen on (non-privileged ports are > 1023)



sel = selectors.DefaultSelector()

host, port = HOST, PORT
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

users = {} # identify users by their client id. assign here and then send

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def send_message(key, message)->None:
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_WRITE:
        print(f"sending {message!r} to {data.addr}")
        sent = sock.send(message)  # Should be ready to write
        data.outb = data.outb[sent:]


def service_connection(key, mask)->None:
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
            print(f"Received {recv_data!r} from {data.addr}")
            # parse the message
            if recv_data[:5] == b"/user":
                username = recv_data[6:].decode()
                print(f"username: {username}")
                users[username] = len(users)
                print(users)
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
                #send_message(key, f"id: {len(users)}")
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()
