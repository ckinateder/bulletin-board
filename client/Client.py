import json
import socket
from collections import deque
import copy
from ClientCommand import ClientCommand
from UserCommand import UserCommand, compare_commands
from ServerCommand import ServerCommand
from MessageSend import MessageSend
from MessageReceive import MessageReceive
from ServerErrorCode import ServerErrorCode, server_error_code_from_response
import threading
import ast
import sys
#import readline

condition = threading.Condition()
lock = threading.Lock()

class Client:
    def __init__(self):
        self.host = None
        self.port = None
        self.s = None
        self.connected = False
        self.username = ""
        self.id = None
        self.current_board = None
        self.sentMessages = deque()
        self.receviedMessages = deque()
        self.start()

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
            return (
                False,
                "You are already connected to a server. Please disconnect first.",
            )

        request_message = f"Connecting to {self.host}: {self.port}..."
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        self.connected = True

        return (True, request_message)

    def post_connect(self, message_receive):
        """Connects to the server."""
        successful_connect = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                self.username = message_receive.body["username"]
                self.id = message_receive.body["id"]
                response_output = f"Your username is '{self.username}'. Your id is '{self.id}'"
            case (False, ServerErrorCode.NameTaken):
                successful_connect = False
                response_output = f"Username '{self.username}' already taken. Please change it and try again."
                self.disconnect()
            case (_, _):
                successful_connect = False
                response_output = "Unknown error"
                self.disconnect()
        return (successful_connect, response_output)

    def post_reconnect(self, message_receive):
        successful_connect = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                self.id = message_receive.body["id"]
                self.username = message_receive.body["username"]
                response_output = f"Your username is '{self.username}'. Your id is still '{self.id}'"
            case (False, ServerErrorCode.NameTaken):
                successful_connect = False
                response_output = f"Username '{self.username}' already taken. Please change it and try again."
                self.disconnect()
            case (_, _):
                successful_connect = False
                response_output = "Unknown error"
                self.disconnect()
        return (successful_connect, response_output)

    def disconnect(self):
        """Gracefully disconnects from the server."""
        if self.s:
            self.s.close()
            self.s = None
            self.connected = False
            return (
                False,
                f"Disconnected from {self.host}:{self.port}. Your id is still '{self.id}', so you may reconnect.",
            )
        return (False, "You are not connected to a server.")

    def help(self):
        """Prints a list of commands."""
        print("Commands:")
        [print("/"+" ".join(command.value)) for command in UserCommand]

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

    def post_join(self, message_receive: MessageReceive):
        successful_join = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                self.current_board = message_receive.body['board_name']
                response_output = f"Joined Board: {self.current_board}"
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_join = False
                response_output = "The board you tried to join doesn't exist."
            case (_, _):
                successful_join = False
                response_output = "Unknown error"
        return (successful_join, response_output)

    def pre_leave_board(self):
        if self.s and self.current_board:
            return (True, "")
        return (False, "You are not connected to a server and board.")

    def post_leave_board(self, message_receive):
        """Leaves the current board."""
        successful_leave = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                response_output = f"Left Board: {message_receive.body['board_name']}"
                self.current_board = None
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_leave = False
                response_output = "The board you tried to leave doesn't exist."
            case (_, _):
                successful_leave = False
                response_output = "Unknown error"
        return (successful_leave, response_output)

    def pre_change_username(self, new_username):
        if not self.s:  # if not connected to a server it doesn't need update
            self.username = new_username
            return (False, "")
        return (True, "")

    def post_change_username(self, message_receive):
        successful_change_username = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                self.username = message_receive.body["new_username"]
                response_output = f'Username changed to: {self.username}'
            case (False, ServerErrorCode.UserDoesntExist):
                successful_change_username = False
                response_output = "Your user doesn't exist on the server"
            case (False, ServerErrorCode.NameTaken):
                successful_change_username = False
                response_output = f'Username {message_receive.body["new_username"]} is already taken'
            case (_, _):
                successful_change_username = False
                response_output = "Unknown error"
        return (successful_change_username, response_output)

    def pre_get_users_in_board(self):
        if self.s and self.current_board:
            return (True, "")
        return (False, "You are not connected to a server and board.")

    def post_get_users_in_board(self, message_receive: MessageReceive):
        successful_get_users = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                users = message_receive.body["users"]
                response_output = f"Users in board '{self.current_board}': {', '.join(users)}"
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_get_users = False
                response_output = "The board you tried to get users from doesn't exist."
            case (_, _):
                successful_get_users = False
                response_output = "Unknown error"
        return (successful_get_users, response_output)

    def post_user_posted_to_board(self, data):
        pass

    def handle_commands(self):
        prompt_response = ""
        while prompt_response != "/exit":
            prompt_response = input(f"{self.username}> ").strip()
            message = MessageSend()
            message_will_be_sent = False
            request_message = ""

            if compare_commands(UserCommand.Help, prompt_response):
                message_will_be_sent = False
                self.help()

            elif compare_commands(UserCommand.Connect, prompt_response):
                resp = self.parse_connect(prompt_response)

                if resp:
                    self.host, self.port = resp
                    message_will_be_sent, request_message = self.pre_connect()
                    if not self.id:
                        message_body = {"host": self.host, "port": self.port}
                        message.create_message(
                            self.username, ClientCommand.Connect, "", message_body
                        )
                    else:
                        message_body = {"id": self.id}
                        message.create_message(
                            self.username, ClientCommand.Reconnect, "", message_body
                        )

            elif compare_commands(UserCommand.Setuser, prompt_response):
                given_username = prompt_response[9:].strip()
                if not self.validate_username(given_username):
                    print("Come on, man! You knew the rules.")
                    continue
                message_body = {"id": self.id, "new_username": given_username}
                message.create_message(
                    self.username, ClientCommand.SetUser, "", message_body
                )
                message_will_be_sent, request_message = self.pre_change_username(
                    given_username
                )

            elif compare_commands(UserCommand.Disconnect, prompt_response):
                (
                    message_will_be_sent,
                    request_message,
                ) = (
                    self.disconnect()
                )  # Message will never be sent for a disconnet command, so there is no need to construct one.

            elif compare_commands(UserCommand.Send, prompt_response):
                message_body = {"id": self.id, "message": prompt_response[6:]}
                message.create_message(
                    self.username, ClientCommand.Send, "", message_body
                )
                message_will_be_sent = True

            elif compare_commands(UserCommand.Join, prompt_response):
                if len(prompt_response) < 7:
                    board_name = "default"  # just for part 1
                else:
                    board_name = prompt_response[6:].strip()
                message_will_be_sent, request_message = self.pre_join()
                message_body = {"id": self.id, "board_name": board_name}
                message.create_message(
                    self.username, ClientCommand.Join, "", message_body
                )

            elif compare_commands(UserCommand.Leave, prompt_response):
                message_will_be_sent, request_message = self.pre_leave_board()
                message_body = {"id": self.id, "board_name": self.current_board}
                message.create_message(
                    self.username, ClientCommand.Leave, "", message_body
                )

            elif compare_commands(UserCommand.Users, prompt_response):
                message_body = {"id": self.id, "board_name": self.current_board}
                message.create_message(
                    self.username, ClientCommand.Users, "", message_body
                )
                message_will_be_sent, request_message = self.pre_get_users_in_board()

            elif compare_commands(UserCommand.Exit, prompt_response):
                request_message = "bye!"
                self.disconnect()
                break  # this doesn't work
            elif prompt_response == "":
                continue
            else:
                message_will_be_sent = False
                request_message = "Invalid Command"
            
            print(request_message)
            if message_will_be_sent:
                outbound_message = message.get_message()
                with lock:
                    self.sentMessages.append(message)
                self._send(outbound_message)

    def handle_inbound_responses(self):
        while True:
            if self.s and self.connected == True:
                data = self._receive(echo=False)
                with lock:
                    if data != "":
                        self.receviedMessages.append(MessageReceive(data))

    def router(self):  # Routes received responses to the correct post_ method
        while True:
            if self.sentMessages != deque() and self.receviedMessages != deque():
                with lock:
                    sent_message = self.sentMessages.popleft()
                    received_message = self.receviedMessages.popleft()
                    success = None
                    response_output = ""
                    if sent_message.id == received_message.acknowledgement_id:
                        match received_message.command:
                            case ServerCommand.Connect:
                                success, response_output = self.post_connect(received_message)
                            case ServerCommand.Reconnect:
                                success, response_output = self.post_reconnect(received_message)
                            case ServerCommand.SetUser:
                                success, response_output = self.post_change_username(received_message)
                            case ServerCommand.Join:
                                success, response_output = self.post_join(received_message)
                            case ServerCommand.Users:
                                success, response_output = self.post_get_users_in_board(received_message)
                            case ServerCommand.Leave:
                                success, response_output = self.post_leave_board(received_message)
                            case ServerCommand.Invalid:
                                success = False
                                response_output = "The provided command was invalid."

                    elif received_message.run_without_id_check:
                        match sent_message.command:
                            case ServerCommand.PostMade:
                                self.post_user_posted_to_board(received_message)
                        self.sentMessages.appendleft(sent_message)

                    else:  # If the ids don't match, and the recieved message is not set to run without id check, then reset the sent message queue and put the recieved message to the back of the queue.
                        self.sentMessages.appendleft(sent_message)
                        self.receviedMessages.append(received_message)
                    
                    if success:
                        print(f"Success! {response_output}")
                    else:
                        print(f"Command Failed! {response_output}")
                    print()

    def _receive(self, buffer_size=1024, echo=True):
        try:
            data = self.s.recv(buffer_size).decode("utf-8").strip()
            if echo:
                print(f"receieved '{data}' from {self.s.getpeername()}")
            if not data:
                self.s.close()
                print(f"Connection from {self.host} closed.")
                self.s = None
            return data
        except (OSError, ConnectionAbortedError):
            return ""

    def _send(self, data, echo=False):
        if self.s:
            self.s.sendall(data.encode())
            if echo:
                print(f"sent '{data}' to {self.s.getpeername()}")
        else:
            print("You are not connected to a server.")

    def start(self):
        self.get_username()

        router_thread = threading.Thread(target=self.router)
        receive_message_thread = threading.Thread(target=self.handle_inbound_responses)

        router_thread.start()
        receive_message_thread.start()
        try:
            self.handle_commands()
        except KeyboardInterrupt:
            pass
        print("No longer handling commands. Closing client...")
        router_thread.join()
        receive_message_thread.join()
