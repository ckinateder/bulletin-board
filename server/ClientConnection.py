import threading
from socket import socket


class ClientConnection:
    def __init__(self, client_socket: socket, addr):
        self.socket = client_socket
        self.addr = addr
        self.user_id = None

    def send_to_client(self, data: str):
        """Sends data to a client."""
        self.socket.sendall(data.encode())
        print(f"Sent '{data}' to {self.socket.getpeername()}")

