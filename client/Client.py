from datetime import datetime
import socket
from collections import deque
from ClientCommand import ClientCommand
from UserCommand import UserCommand, compare_commands
from ServerCommand import ServerCommand
from MessageSend import MessageSend
from MessageReceive import MessageReceive
from ServerErrorCode import ServerErrorCode, server_error_code_from_response
import threading
from tkinter import *
import time
# import readline

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
        self.root = Tk()

        self.root.geometry("1000x1000")
        self.root.title(" Bulletin Board ")
        self.current_board_label = Label(text="Current Board: None")
        self.connected_label = Label(text="Connected: False")
        self.help_label = Label(text=self.help())
        self.enter_user_name_label = Label(
            text="Enter your username (no spaces or weird chars)")
        # Grid.rowconfigure(self.root, index=0, weight=1)
        # Grid.columnconfigure(self.root, index=0, weight=1)

        # Grid.rowconfigure(self.root, index=1, weight=1)
        # Grid.rowconfigure(self.root, index=2, weight=1)
        # Grid.rowconfigure(self.root, index=3, weight=1)

        self.inputtxt = Text(self.root, height=5,
                             width=100,
                             bg="light yellow")
        self.Chat = Text(self.root, height=35,
                         width=100,
                         bg="light cyan")
        self.EnterButton = Button(self.root, height=2,
                                  width=50,
                                  text="Enter",
                                  command=lambda: self.handle_commands())
        self.GetUserButton = Button(self.root, height=2,
                                    width=50,
                                    text="Login",
                                    command=lambda: self.get_username())

        # self.inputtxt.grid(row=0, column=0, sticky="nsew")
        # self.Chat.grid(row=0, column=0, sticky="nsew")
        # self.EnterButton.grid(row=2, column=0, sticky="nsew")
        # self.GetUserButton.grid(row=3, column=0, sticky="nsew")

        self.command_to_send = ""
        self.current_board_label.pack()
        self.connected_label.pack()
        self.enter_user_name_label.pack()
        self.inputtxt.pack()
        self.GetUserButton.pack()
        self.start()

    def addText(self, new_output):
        self.Chat.insert(END, f'\n{new_output}')

    def set_command_to_send(self):
        self.command_to_send = self.inputtxt.get("1.0", "end-1c")
        self.inputtxt.delete(1.0, END)

    def validate_username(self, username: str) -> bool:
        """Validates the username."""
        restrictions = [" ", ":", "/", "\\", "<", ">", "|", "?", "*"]
        if username == "" or any([r in username for r in restrictions]):
            return False
        return True

    def get_username(self):
        """Gets the username from the user."""
        self.enter_user_name_label.config(
            text=f"Enter your command below")
        self.username = self.inputtxt.get("1.0", END)
        self.inputtxt.delete(1.0, END)
        while self.validate_username(self.username) is False:
            self.addText(
                "Come on, man! You knew the rules.\nEnter your username: ")
            self.username = self.inputtxt.get("1.0", "end-1c")
        self.GetUserButton.pack_forget()
        self.EnterButton.pack()
        self.Chat.pack()
        self.help_label.pack()

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
                self.connected_label.config(text=f'Connected:{self.connected}')
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
                self.connected_label.config(text=f'Connected:{self.connected}')
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
            self.connected_label.config(text=f'Connected:{self.connected}')
            self.current_board_label.config(text=f'Current Board: None')
            return (
                False,
                f"Disconnected from {self.host}:{self.port}. Your id is still '{self.id}', so you may reconnect.",
            )
        return (False, "You are not connected to a server.")

    def help(self):
        return "Commands:\n" + "\n".join(["/ " + " ".join(command.value) for command in UserCommand])

    def parse_connect(self, prompt_response):
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
            self.addText("Invalid host or port.")
            return None

    def is_user_connected(self):
        if self.connected:
            return (True, "")
        return (False, "You are not connected to a server.")

    def pre_join(self):
        match (self.connected, self.current_board):
            case (False, _):
                return (False, "You are not connected to a server.")
            case (_, None):
                return (True, "")
            case (_, _):
                return (False, f"You are already connected to board {self.current_board}. Please leave it before joining a new board.")

    def post_join(self, message_receive):
        successful_join = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                self.current_board = message_receive.body['board_name']
                response_output = f"Joined Board: {self.current_board}"
                self.current_board_label.config(
                    text=f'Current Board: {self.current_board}')
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_join = False
                response_output = "The board you tried to join doesn't exist."
            case (_, _):
                successful_join = False
                response_output = "Unknown error"
        return (successful_join, response_output)

    def post_user_joined_board(self, message_receive):
        successful_user_join = True
        response_output = f'User {message_receive.body["username"]} joined board {message_receive.body["board_name"]}.'
        return (successful_user_join, response_output)

    def does_user_have_socket_and_board(self):
        match (self.connected, self.current_board):
            case (False, None):
                return (False, "You are not connected to a server or board.")
            case (False, _):
                return (False, "You are not connected to a server.")
            case (True, None):
                return (False, "You are not connected to a board.")
        return (True, "")

    def post_leave_board(self, message_receive):
        """Leaves the current board."""
        successful_leave = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                response_output = f"Left Board: {message_receive.body['board_name']}"
                self.current_board = None
                self.current_board_label.config(
                    text=f'Current Board: None')
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_leave = False
                response_output = "The board you tried to leave doesn't exist."
            case (_, _):
                successful_leave = False
                response_output = "Unknown error"
        return (successful_leave, response_output)

    def post_post_to_board(self, message_receive):
        successful_post = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                response_output = f'Posted to board {message_receive.body["board_name"]}'
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_post = False
                response_output = "The board you tried to post to doesn't exist."
            case (False, ServerErrorCode.UserDoesntExist):
                successful_post = False
                response_output = f'The user with id: {self.id} doesnt exist.'
            case (_, _):
                successful_post = False
                response_output = "Unknown error"
        return (successful_post, response_output)

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

    def post_get_users_in_board(self, message_receive):
        successful_get_users = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                users = message_receive.body["users"]
                response_output = f"Users in board '{self.current_board}': {', '.join(users)}"
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_get_users = False
                response_output = "The board you tried to get users from doesn't exist."
            case (False, ServerErrorCode.UserDoesntExist):
                successful_get_users = False
                response_output = f'The user with id: {self.id} doesnt exist.'
            case (_, _):
                successful_get_users = False
                response_output = "Unknown error"
        return (successful_get_users, response_output)

    def post_user_posted_to_board(self, message_receive):
        successful_user_posted = True
        response_output = f'User: {message_receive.body["username"]} posted to board {message_receive.body["board_name"]}. Do /getposts to view their post.'
        return (successful_user_posted, response_output)

    def post_get_posts_from_board(self, message_receive):
        successful_get_posts = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                posts = message_receive.body["posts"]
                response_output = f"Posts in board: '{self.current_board}':"
                for post in posts:
                    timestamp = post["time"]
                    formatted_time = datetime.utcfromtimestamp(
                        timestamp).strftime('%m/%d %H:%M')
                    response_output = response_output + '\n' + \
                        f'{post["username"]}: {post["content"]} ({formatted_time})'
            case (False, ServerErrorCode.BoardDoesntExist):
                successful_get_posts = False
                response_output = "The board you tried to get users from doesn't exist."
            case (False, ServerErrorCode.UserDoesntExist):
                successful_get_posts = False
                response_output = f'The user with id: {self.id} doesnt exist.'
            case (False, ServerErrorCode.NoPosts):
                successful_get_posts = True
                response_output = "There are no posts on this board at the moment."
            case (_, _):
                successful_get_posts = False
                response_output = "Unknown error"
        return (successful_get_posts, response_output)

    def post_create_board(self, message_receive):
        successful_create_board = True
        response_output = ""
        match (message_receive.is_success, server_error_code_from_response(message_receive)):
            case (True, None):
                new_board_name = message_receive.body["board_name"]
                self.current_board = new_board_name
                response_output = f"New board created and joined: '{self.current_board}'"
                self.current_board_label.config(
                    text=f'Current Board: {self.current_board}')
            case (False, ServerErrorCode.UserDoesntExist):
                successful_create_board = False
                response_output = f'The user with id: {self.id} doesnt exist.'
            case (False, ServerErrorCode.BoardExists):
                successful_create_board = False
                response_output = "The board you attempted to create already exists."
            case (_, _):
                successful_create_board = False
                response_output = "Unknown error"
        return (successful_create_board, response_output)

    def post_user_created_new_board(self, message_receive):
        successful_user_created_board = True
        response_output = f'User: {message_receive.body["username"]} created a new board: {message_receive.body["board_name"]}. Do /join {message_receive.body["board_name"]} to view posts on that board.'
        return (successful_user_created_board, response_output)

    def handle_commands(self):
        self.command_to_send = self.inputtxt.get("1.0", "end-1c")
        self.inputtxt.delete(1.0, END)
        prompt_response = self.command_to_send
        self.command_to_send = None
        message = MessageSend()
        message_will_be_sent = False
        request_message = ""

        if compare_commands(UserCommand.Help, prompt_response):
            message_will_be_sent = False
            request_message = self.help()

        elif compare_commands(UserCommand.Connect, prompt_response):
            resp = self.parse_connect(prompt_response)

            if resp:
                self.host, self.port = resp
                message_will_be_sent, request_message = self.pre_connect()
                if not self.id:
                    message_body = {
                        "host": self.host, "port": self.port}
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
                self.addText(
                    "Come on, man! You knew the rules.")
            else:
                message_body = {"id": self.id,
                                "new_username": given_username}
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
            message_will_be_sent, request_message = self.does_user_have_socket_and_board()
            message_body = {"id": self.id,
                            "board_name": self.current_board}
            message.create_message(
                self.username, ClientCommand.Leave, "", message_body
            )

        elif compare_commands(UserCommand.Users, prompt_response):
            message_will_be_sent, request_message = self.does_user_have_socket_and_board()
            message_body = {"id": self.id,
                            "board_name": self.current_board}
            message.create_message(
                self.username, ClientCommand.Users, "", message_body
            )

        elif compare_commands(UserCommand.Post, prompt_response):
            content = prompt_response[5:]
            message_will_be_sent, request_message = self.does_user_have_socket_and_board()
            message_body = {
                "id": self.id, "board_name": self.current_board, "content": content}
            message.create_message(
                self.username, ClientCommand.Post, "", message_body)

        elif compare_commands(UserCommand.GetPosts, prompt_response):
            message_will_be_sent, request_message = self.does_user_have_socket_and_board()
            message_body = {"id": self.id,
                            "board_name": self.current_board}
            message.create_message(
                self.username, ClientCommand.GetPosts, "", message_body)

        elif compare_commands(UserCommand.CreateBoard, prompt_response):
            new_board_name = prompt_response[10:]
            message_will_be_sent, request_message = self.is_user_connected()
            message_body = {
                "id": self.id, "current_board_name": self.current_board, "new_board_name": new_board_name}
            message.create_message(
                self.username, ClientCommand.CreateBoard, "", message_body)

        elif compare_commands(UserCommand.Exit, prompt_response):
            request_message = "bye!"
            self.disconnect()
            # this doesn't work
        else:
            message_will_be_sent = False
            request_message = "Invalid Command: Use /help to learn commands"

        self.addText(request_message)
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
            sent_message = None
            received_message = None
            if self.receviedMessages != deque():
                with lock:
                    received_message = self.receviedMessages.popleft()
                    success = None
                    response_output = ""
                    if self.sentMessages != deque():
                        sent_message = self.sentMessages.popleft()
                        if sent_message.id == received_message.acknowledgement_id:
                            match received_message.command:
                                case ServerCommand.Connect:
                                    success, response_output = self.post_connect(
                                        received_message)
                                case ServerCommand.Reconnect:
                                    success, response_output = self.post_reconnect(
                                        received_message)
                                case ServerCommand.SetUser:
                                    success, response_output = self.post_change_username(
                                        received_message)
                                case ServerCommand.Join:
                                    success, response_output = self.post_join(
                                        received_message)
                                case ServerCommand.Users:
                                    success, response_output = self.post_get_users_in_board(
                                        received_message)
                                case ServerCommand.Leave:
                                    success, response_output = self.post_leave_board(
                                        received_message)
                                case ServerCommand.Post:
                                    success, response_output = self.post_post_to_board(
                                        received_message)
                                case ServerCommand.GetPosts:
                                    success, response_output = self.post_get_posts_from_board(
                                        received_message)
                                case ServerCommand.CreateBoard:
                                    success, response_output = self.post_create_board(
                                        received_message)
                                case ServerCommand.Invalid:
                                    success = False
                                    response_output = "The provided command was invalid."

                    if received_message.run_without_id_check:
                        match received_message.command:
                            case ServerCommand.PostMade:
                                success, response_output = self.post_user_posted_to_board(
                                    received_message)
                            case ServerCommand.BoardCreated:
                                success, response_output = self.post_user_created_new_board(
                                    received_message)
                            case ServerCommand.UserJoinedBoard:
                                success, response_output = self.post_user_joined_board(
                                    received_message)
                        if sent_message:
                            self.sentMessages.appendleft(sent_message)

                    # If the ids don't match, and the recieved message is not set to run without id check, then reset the sent message queue and put the recieved message to the back of the queue.
                    if not (received_message.run_without_id_check or sent_message.id == received_message.acknowledgement_id):
                        self.receviedMessages.append(received_message)

                    if success:
                        # print(f"Success! {response_output}")
                        self.addText(f"Sucess! {response_output}")

                    else:
                        # print(f"Command Failed! ")
                        self.addText(
                            f"Commmand Failed! {response_output}")

    def _receive(self, buffer_size=1024, echo=True):
        try:
            data = self.s.recv(buffer_size).decode("utf-8").strip()
            if echo:
                self.addText(
                    f"receieved '{data}' from {self.s.getpeername()}")
            if not data:
                self.s.close()
                self.addText(f"Connection from {self.host} closed.")
                self.s = None
            return data
        except (OSError, ConnectionAbortedError):
            return ""

    def _send(self, data, echo=False):
        if self.s:
            self.s.sendall(data.encode())
            if echo:
                self.addText(
                    f"sent '{data}' to {self.s.getpeername()}")
        else:
            self.addText("You are not connected to a server.")

    def start(self):
        router_thread = threading.Thread(target=self.router)
        receive_message_thread = threading.Thread(
            target=self.handle_inbound_responses)

        router_thread.start()
        receive_message_thread.start()

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        self.addText("No longer handling commands. Closing client...")
        router_thread.join()
        receive_message_thread.join()
