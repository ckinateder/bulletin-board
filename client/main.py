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

    def validate_username(self, username:str)->bool:
        """Validates the username."""
        restrictions = [" ", ":", "/", "\\", "<", ">", "|", "?", "*"]
        if username == "" or any([r in username for r in restrictions]):
            return False
        return True

    def get_username(self):
        """Gets the username from the user."""
        self.username = input("Enter your username (no spaces or weird chars): ")
        while self.validate_username(self.username) is False:
            self.username = input(
                "Come on, man! You knew the rules.\nEnter your username: "
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
            self.s.sendall(f"/newuser {self.username}".encode())  # send the username
            data = self._receive()
            if data[:8] == "/success":
                response = data[9:].strip().split(":")
                self.id = response[1]
                assert response[0] == self.username # make sure the username is correct
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
        print("/send <message> - send a message to the server") # remove later
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

    def join(self, board_name):
        """Joins a board.

        Args:
            board_name (str): The name of the board to join.
        """
        if self.s:
            self._send(f"/join {board_name}")
            data = self._receive()
            if data[:8] == "/success":
                print(f"Joined board '{board_name}'")
            elif data[:5] == "/fail":
                print(f"Failed to join board '{board_name}'.")
            else:
                print("fail. Unknown error.")
                self.s.close()
                self.s = None
        else:
            print("You are not connected to a server.")

    def change_username(self, new_username:str):
        """Changes the username.

        Args:
            new_username (str): The new username.
        """
        if not self.s: # if not connected to a server it doesn't need update
            self.username = new_username
            return

        self._send(f"/chguser {new_username}:{self.id}")
        data = self._receive()
        if data[:8] == "/success":
            print(f"Username changed to '{new_username}'")
            self.username = new_username
        elif data[:5] == "/fail":
            print(f"Failed to change username to '{new_username}'.")
        else:
            print("fail. Unknown error.")
            self.s.close()
            self.s = None

    def main(self):
        """Main loop."""
        while prompt_response := input(f"{self.username}> ").strip():
            if prompt_response == "/help":
                self.help()
            elif prompt_response[:8] == "/setuser":
                given_username = prompt_response[9:].strip()
                if self.validate_username(given_username) is False:
                    print("Come on, man! You knew the rules.")
                    continue
                self.change_username(given_username)
            elif prompt_response[:8] == "/connect":
                resp = self.parse_connect(prompt_response)
                if resp:
                    self.host, self.port = resp
                    self.connect()
            elif prompt_response[:11] == "/disconnect":
                self.disconnect()
            elif prompt_response[:5] == "/send":
                self._send(prompt_response[6:])
            elif prompt_response[:5] == "/join":
                if len(prompt_response) < 7:
                    board_name = "default"
                else:
                    board_name = prompt_response[6:].strip()
                self.join(board_name)
            elif prompt_response[:5] == "/exit":
                print("bye!")
                self.disconnect()
                break
            else:
                print("invalid command")

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
