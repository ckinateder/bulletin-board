import socket
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65439  # The port used by the server

print("Welcome! Type '/help' for a list of commands.")

# get username


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.s = None
        self.username = None
        self.get_username()

    def get_username(self):
        self.username = input("Enter your username (no spaces): ")
        while " " in self.username:
            self.username = input(
                "Come on, man! Your username cannot contain spaces.\nEnter your username: ")

    def connect(self):
        print(f"Connecting to {HOST}: {PORT}...", end=" ")
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))
        self.s.sendall(f"/user {self.username}".encode())  # send the username
        data = self._receive()
        if data[:8] == "/success":
            print(f"success! Your username is '{self.username}'")
        elif data[:5] == "/fail":
            print(f"fail. Username '{
                  self.username}' already taken. Please choose another.")
            self.s.close()
            self.s = None
            self.get_username()

    def disconnect(self):
        if self.s:
            self.s.close()
            self.s = None
            print(f"Disconnected from {HOST}: {PORT}")
        else:
            print("You are not connected to a server.")

    def main(self):
        while prompt_response := input("> ").strip():
            if prompt_response == "/help":
                print("Commands:")
                print("/connect <host>:<port> - connect to a server")
                print("/send <message> - send a message to the server")
                print("/exit - exit the program")
            elif prompt_response[:8] == "/connect":
                self.connect()
            elif prompt_response[:11] == "/disconnect":
                self.disconnect()
            elif prompt_response[:5] == "/exit":
                print("bye!")
                self.disconnect()
                break
            else:
                print("invalid command")

    def _receive(self, buffer_size=1024, echo=True):
        data = self.s.recv(buffer_size).decode('utf-8').strip()
        if echo:
            print(f"receieved '{data}'")
        if not data:
            self.s.close()
            print(f"Connection from {HOST} closed.")
            self.s = None
        return data


if __name__ == "__main__":
    client = Client(HOST, PORT)
    client.main()
