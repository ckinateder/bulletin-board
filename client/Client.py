import socket
from queue import Queue
import copy
from ClientCommand import ClientCommand
from ServerCommand import ServerCommand
from MessageSend import MessageSend
from MessageReceive import MessageReceive
import threading
import ast

condition = threading.Condition()

class Client:
    def __init__(self):
        self.host = None
        self.port = None
        self.s = None
        self.username = ""
        self.id = None
        self.current_board = None
        self.get_username()
        self.sentMessages = Queue(MessageSend)
        self.receviedMessages = Queue(MessageReceive)

    def validate_username(self, username: str) -> bool:
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

    def build_client_message(self, command, message_body):
        return MessageSend(self.username, command, "", message_body).get_message()

    def pre_connect(self):
        if self.s:
            return (False, "You are already connected to a server. Please disconnect first.")

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        request_message = f"Connecting to {self.host}: {self.port}..."
        return (True, request_message)

    def post_connect(self, data):
        """Connects to the server."""
        if  data.is_success:
            response = data[9:].strip().split(":")
            assert response[0] == self.username and response[1] == self.id
            print(
                f"success! Your username is '{self.username}'. Your id is '{self.id}'"
            )
            return
        elif (not data.is_success) and data.body['fail_reason'] == "name_taken":
            print(
                f"fail. Username '{self.username}' already taken. Please choose another and try again."
            )
            self.get_username()
            return
        elif (not data.is_success) and data.body['fail_reason'] == "no_id":
            print("fail. Killing corrupted user identity. Try again.")
            self.disconnect()
            self.id = None
            return
        else:
            print("fail. Unknown error.")
            self.disconnect()
            return
        
    def post_reconnect (self, data: MessageReceive):
        if data.is_success:
            response = data[9:].strip().split(":")
            self.id = response[1]
            assert response[0] == self.username  # make sure the username is correct
            print(
                f"success! Your username is '{self.username}'. Your id is '{self.id}'"
            )
            return
        
        print(
            f"fail. Username '{self.username}' already taken. Please choose another and try to connect again."
        )
        self.s.close()
        self.s = None
        self.get_username()

    def disconnect(self):
        """Gracefully disconnects from the server."""
        if self.s:
            self.s.close()
            self.s = None
            return (False, "Disconnected from {self.host}:{self.port}. Your id is still '{self.id}', so you may reconnect.")

        return (False, "You are not connected to a server.")

    def help(self):
        """Prints a list of commands."""
        print("Commands:")
        print("/connect <host>:<port> - connect to a server")
        print("/disconnect - disconnect from the server")
        print("/send <message> - send a message to the server")  # remove later
        print("/setuser <username> - set your username")
        print("/join <board_name> - join a board")
        print("/leave - leave the current board")

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
        
    def pre_join(self):
        if not self.s:
            return (False, "You are not connected to a server.")
        else:
            return (True, "")

    def post_join(self, data: MessageReceive):
        """Joins a board.

        Args:
            board_name (str): The name of the board to join.
        """
        board_name = data.body['board_name']
        if self.s:
            if data.is_success:
                print(f"Joined board '{board_name}'")
                self.current_board = board_name
            elif not data.is_success:
                print(f"Failed to join board '{board_name}'.")
            else:
                print("fail. Unknown error.")
                self.s.close()
                self.s = None
        else:
            print("You are not connected to a server.")

    def pre_leave_board(self):
        if self.s and self.current_board:
            return (True, "")
        return (False, "You are not connected to a server and board.")

    def post_leave_board(self, data):
        """Leaves the current board."""
        if data[:8] == "/success":
            print(f"Left board '{self.current_board}'")
            self.current_board = None
        elif data[:5] == "/fail":
            print(f"Failed to leave board '{self.current_board}'.")
        else:
            print("fail. Unknown error.")
            self.s.close()
            self.s = None

    def pre_change_username(self, new_username):
        if not self.s:  # if not connected to a server it doesn't need update
            self.username = new_username
            return (False, "")
        (True, "")

    def post_change_username(self, data):
        """Changes the username.

        Args:
            new_username (str): The new username.
        """
        if data[:8] == "/success":
            print(f"Username changed to '{new_username}'")
            self.username = new_username
        elif data[:5] == "/fail":
            print(f"Failed to change username to '{new_username}'.")
        else:
            print("fail. Unknown error.")
            self.s.close()
            self.s = None

    def pre_get_users_in_board(self):
        if self.s and self.current_board:
            return (True, "")
        return (False, "You are not connected to a server and board.")

    def post_get_users_in_board(self, data: MessageReceive):
        if data.is_success:
            users = ast.literal_eval(data.body['users'])  
            print(f"Users in board '{self.current_board}': {', '.join(users)}")
            return
        else:
            print(f"Failed to get users in board '{self.current_board}'.")

    def post_user_posted_to_board(self, data):
        pass

    def handle_request_send(self):
        while prompt_response := input(f"{self.username}> ").strip():
            message = MessageSend()
            message_will_be_sent = True
            request_message = ""
            
            if prompt_response == "/help":
                self.help()

            elif prompt_response[:8] == "/connect":
                message_will_be_sent, request_message = self.pre_connect() 
                resp = self.parse_connect(prompt_response)
                if resp:
                    self.host, self.port = resp
                    if not self.id:
                        message_body = {"host": self.host, "port": self.port}
                        message.create_message(self.username, ClientCommand.Connect, "", message_body)
                    else:
                        message_body = {"id": self.id}
                        message.create_message(self.username, ClientCommand.Reconnect, "", message.body)

            elif prompt_response[:8] == "/setuser":
                given_username = prompt_response[9:].strip()
                if self.validate_username(given_username):
                    print("Come on, man! You knew the rules.")
                    continue
                message_body = {"new_username": given_username, "id": self.id}
                message.create_message(self.username, ClientCommand.SetUser, "", message_body)
                message_will_be_sent, request_message = self.pre_change_username(given_username)

            elif prompt_response[:11] == "/disconnect":
                message_will_be_sent, request_message = self.disconnect() # Message will never be sent for a disconnet command, so there is no need to construct one.

            elif prompt_response[:5] == "/send":
                message_body = {"message": prompt_response[6:]}
                message.create_message(self.username, ClientCommand.Send, "", message_body)
                message_will_be_sent = True

            elif prompt_response[:5] == "/join":
                if len(prompt_response) < 7:
                    board_name = "default"  # just for part 1
                else:
                    board_name = prompt_response[6:].strip()
                message_will_be_sent, request_message = self.pre_join() 
                message_body = {"board_name": board_name}
                message.create_message(self.username, ClientCommand.Join, "", message_body)       

            elif prompt_response[:6] == "/leave":
                message_will_be_sent, request_message = self.pre_leave_board()
                message_body = {"id": self.id}
                message.create_message(self.username, ClientCommand.Leave, "", message_body)

            elif prompt_response[:6] == "/users":
                message_body = {"current_board": self.current_board}
                message.create_message(self.username, ClientCommand.Users, "", message_body)
                message_will_be_sent, request_message = self.pre_get_users_in_board()

            elif prompt_response[:5] == "/exit":
                print("bye!")
                self.disconnect()
                break
            
            else:
                message_will_be_sent = False
                request_message = "Invalid Command"

            if message_will_be_sent:
                outbound_message = message.get_message()
                self.sentMessages.put(outbound_message)
                self._send(outbound_message)
            
            print(request_message)

    def handle_inbound_responses(self):
        while True:
            data = MessageReceive()
            data.parse_message(self._receive(echo=False))
            self.receviedMessages.push(data)

    def router(self): # Routes received responses to the correct post_ method
        while True:
            with condition:
                while self.sentMessages == [] and self.receviedMessages == []:
                     condition.wait()

                original_sent_messages = copy.deepcopy(self.sentMessages)
                sent_message = self.sentMessages.get()
                received_message = self.receviedMessages.get()
                if sent_message.id == received_message.acknowledgement_id:
                    match sent_message.command:
                        case ServerCommand.Connect:
                            self.post_connect(received_message)
                        case ServerCommand.Reconnect:
                            self.post_reconnect(received_message)
                        case ServerCommand.SetUser:
                            self.post_change_username(received_message)
                        case ServerCommand.Join:
                            self.post_join(received_message)
                        case ServerCommand.Users:
                            self.post_get_users_in_board(received_message)

                elif received_message.run_without_id_check:
                    match sent_message.command:
                        case ServerCommand.PostMade:
                            self.post_user_posted_to_board(received_message)
                    self.sentMessages.queue = original_sent_messages
                
                else: # If the ids don't match, and the recieved message is not set to run without id check, then reset the sent message queue and put the recieved message to the back of the queue.
                    self.sentMessages.queue = original_sent_messages
                    self.receviedMessages.put(received_message)

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