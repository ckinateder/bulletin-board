import socket
import readline


class Client:
    def __init__(self):
        self.host = None
        self.port = None
        self.s = None
        self.username = ""
        self.id = None
        self.get_username()

    def get_username(self):
        """Gets the username from the user."""
        self.username = input("Enter your username (no spaces): ")
        while " " in self.username or self.username == "":
            self.username = input(
                "Come on, man! Your username cannot contain spaces.\nEnter your username: "
            )

    def connect(self):
        """Connects to the server."""
        try:
            if self.s:
                print("You are already connected to a server. Please disconnect first.")
                return
            print(f"Connecting to {self.host}: {self.port}...", end=" ")
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.host, self.port))
            self.s.sendall(f"/user {self.username}".encode())  # send the username
            data = self._receive()
            if data[:8] == "/success":
                self.id = data[9:]
                print(
                    f"success! Your username is '{self.username}'. Your id is '{self.id}'"
                )
            elif data[:5] == "/fail":
                print(
                    f"fail. Username '{self.username}' already taken. Please choose another and try to connect again."
                )
                self.s.close()
                self.s = None
                self.get_username()
            else:
                print("fail. Unknown error.")
                self.s.close()
                self.s = None
        except Exception as e:
            print(f"fail. {e}")
            self.s = None

    def disconnect(self):
        """Gracefully disconnects from the server."""
        if self.s:
            self.s.close()
            self.s = None
            print(f"Disconnected from {self.host}:{self.port}")
        else:
            print("You are not connected to a server.")

    def help(self):
        """Prints a list of commands."""
        print("Commands:")
        print("/connect <host>:<port> - connect to a server")
        print("/disconnect - disconnect from the server")
        print("/send <message> - send a message to the server")
        print("/setuser <username> - set your username")
        print("/exit - exit the program")

    def parse_connect(self, prompt_response):
        """Parses the connect command.

        Args:
            prompt_response (str): The user's response to the prompt.

        Returns:
            tuple: A tuple containing the host and port.
        """
        try:
            if len(prompt_response) < 10:
                with open(".env", "r", encoding="utf-8") as f:
                    host, port = f.read().strip().split(":")
            else:
                host, port = prompt_response[9:].strip().split(":")
                if (
                    not port.isdigit()
                    or int(port) > 65535
                    or int(port) < 0
                    or host == ""
                ):
                    raise ValueError
            return host, int(port)
        except ValueError:
            print("Invalid host or port.")
            return None

    def main(self):
        """Main loop."""
        try:
            while prompt_response := input(f"{self.username}> ").strip():
                if prompt_response == "/help":
                    self.help()
                elif prompt_response[:8] == "/setuser":
                    given_username = prompt_response[9:].strip()
                    if given_username == "" or " " in given_username:
                        print("Come on, man! Your username cannot contain spaces.")
                        continue
                    self.username = given_username
                    print(f"Username set to '{self.username}'")
                elif prompt_response[:8] == "/connect":
                    resp = self.parse_connect(prompt_response)
                    if resp:
                        self.host, self.port = resp
                        self.connect()
                elif prompt_response[:11] == "/disconnect":
                    self.disconnect()
                elif prompt_response[:5] == "/send":
                    self._send(prompt_response[6:])
                elif prompt_response[:5] == "/exit":
                    print("bye!")
                    self.disconnect()
                    break
                else:
                    print("invalid command")
        except KeyboardInterrupt:
            print("\nbye!")
            self.disconnect()

    def _receive(self, buffer_size=1024, echo=True):
        data = self.s.recv(buffer_size).decode("utf-8").strip()
        if echo:
            print(f"receieved '{data}' from {self.s.getpeername()}")
        if not data:
            self.s.close()
            print(f"Connection from {self.host} closed.")
            self.s = None
        return data

    def _send(self, data, echo=True):
        if self.s:
            self.s.sendall(data.encode())
            if echo:
                print(f"sent '{data}' to {self.s.getpeername()}")
        else:
            print("You are not connected to a server.")


if __name__ == "__main__":
    print("Welcome! Type '/help' for a list of commands.")
    client = Client()
    client.main()
