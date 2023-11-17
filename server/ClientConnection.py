import threading
from Server import Server
from socket import socket


class ClientConnection:
    def __init__(self, server: Server, client_socket: socket, addr):
        self.server = server
        self.socket = client_socket
        self.addr = addr

    def send_to_client(self, data: str):
        """Sends data to a client."""
        self.socket.sendall(data.encode())
        print(f"Sent '{data}' to {self.socket.getpeername()}")

    def start_listening(self):
        listening_thread = threading.Thread(target=self.listen_for_requests)
        listening_thread.start()

    def listen_for_requests(self):
        while True:
            try:
                raw_message_receive = self.socket.recv(1024).decode("utf-8").strip()
                if not raw_message_receive:
                    break
                response_message = self.server.handle_inbound_request(
                    raw_message_receive
                )
                self.send_to_client(response_message.get_message())
            except Exception as e:
                print(f"Error handling request: {e}")
                break

        self.socket.close()
        # if the user was logged in, remove them from the users list and log the disconnection
        print(f"Connection from {self.addr} closed.")
