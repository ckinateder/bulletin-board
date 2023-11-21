import socket
import json
import threading
from User import User
from Lobby import Lobby
from ClientCommand import ClientCommand
from ServerCommand import ServerCommand
from ServerErrorCode import ServerErrorCode
from MessageReceive import MessageReceive
from MessageSend import MessageSend
from ClientConnection import ClientConnection

class Server:
    def __init__(self, lobby: Lobby):
        self.lobby = lobby
        self.client_connections = []

    def new_connection(self, c, addr):
        client_connection = ClientConnection(c, addr)
        self.start_listening(client_connection)
        self.client_connections.append(client_connection)
        return

    def start_listening(self, client_connection):
        listening_thread = threading.Thread(target=self.listen_for_requests, args=(client_connection,))
        listening_thread.start()

    def listen_for_requests(self, client_connection):
        while True:
            try:
                raw_message_receive = client_connection.socket.recv(1024).decode("utf-8").strip()
                if not raw_message_receive:
                    break
                response_message = self.handle_inbound_request(raw_message_receive, client_connection)
                if (response_message.command == ServerCommand.PostMade):
                    self.send_to_all_clients(response_message, self.lobby.get_board_by_name(response_message.body["board_name"]).getusers())
                client_connection.send_to_client(response_message.get_message())
            except Exception as e:
                print(f"Error handling request: {e}")
                break

        client_connection.socket.close()
        # if the user was logged in, remove them from the users list and log the disconnection
        print(f"Connection from {client_connection.addr} closed.")

    def send_to_all_clients(self, response_message: MessageSend, users):
        user_ids = {user.id for user in users}
        client_connections = [client_connection for client_connection in self.client_connections if client_connection.user_id in user_ids ]
        for client_connection in client_connections:
            client_connection.send_to_client(response_message.get_message())

    def handle_connect_request(self, message_receive, client_connection):
        if self.lobby.does_username_already_exsist(message_receive.username) or message_receive.username == "":
            message_body_send = {"error_code": ServerErrorCode.NameTaken}
            message_send = MessageSend(message_receive.username, ServerCommand.Connect, False, False, message_receive.id, message_body_send)
            return message_send

        user = User(message_receive.username)
        user.connected = True
        client_connection.user_id = user.id
        self.lobby.add_user_to_lobby(user)
        message_body_send = {"username": user.username, "id": user.id}
        message_send = MessageSend(user.username, ServerCommand.Connect, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_reconnect_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        if not user:
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
            message_send = MessageSend(message_receive.username, ServerCommand.Reconnect, False, False, message_receive.id, message_body_send)
            return message_send

        if user.username == message_receive.username or not self.lobby.does_username_already_exsist(message_receive.username):
            user.connected = True
            user.username = message_receive.username
            message_body_send = {"username": user.username, "id": user.id}
            self.lobby.log.add(user.id, "reconnect")
            message_send = MessageSend(user.username, ServerCommand.Reconnect, False, True, message_receive.id, message_body_send)
            return message_send
        else:
            message_body_send = {"error_code": ServerErrorCode.NameTaken}
            message_send = MessageSend(user.username, ServerCommand.Reconnect, False, False, message_receive.id, message_body_send)
            return message_send

    def handle_change_username_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        new_username = message_receive.body["new_username"]
        if not user:
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
            message_send = MessageSend(message_receive.username, ServerCommand.SetUser, False, False, message_receive.id, message_body_send)
            return message_send

        if self.lobby.does_username_already_exsist(new_username):
            message_body_send = {"error_code": ServerErrorCode.NameTaken, "new_username": new_username}
            message_send = MessageSend(user.username, ServerCommand.SetUser, False, False, message_receive.id, message_body_send)
            return message_send

        user.username = new_username
        message_body_send = {"id": user.id, "new_username": new_username}
        self.lobby.log.add(user.id, "username_change", user.username)
        message_send = MessageSend(user.username, ServerCommand.SetUser, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_join_board_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board_name = message_receive.body["board_name"]
        if not user:
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
            message_send = MessageSend(message_receive.username, ServerCommand.Join, False, False, message_receive.id, message_body_send)
            return message_send

        self.lobby.add_user_to_board(user, board_name)
        message_body_send = {"board_name": board_name}
        message_send = MessageSend(user.username, ServerCommand.Join, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_leave_board_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board_name = message_receive.body["board_name"]
        if not user:
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
            message_send = MessageSend(message_receive.username, ServerCommand.Leave, False, False, message_receive.id, message_body_send)
            return message_send

        self.lobby.remove_user_from_board(user, board_name)
        message_body_send = {"board_name": board_name}
        message_send = MessageSend(user.username, ServerCommand.Leave, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_get_users_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board_name = message_receive.body["board_name"]
        if not user:
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
            message_send = MessageSend(message_receive.username, ServerCommand.Users, False, False, message_receive.id, message_body_send)
            return message_send

        users_in_board = self.lobby.get_board_by_name(board_name).get_users().get_all_usernames()
        message_body_send = {"users": users_in_board}
        message_send = MessageSend(message_receive.username, ServerCommand.Users, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_invalid_command_request(self, message_receive):
        message_body_send = {
            "error_code": ServerErrorCode.InvalidCommand
        }
        message_send = MessageSend(message_receive.username, ServerCommand.Invalid, False, False, message_receive.id, message_body_send)
        return message_send

    def handle_inbound_request(self, raw_message_receive, client_connection):
        message_receive = MessageReceive()
        message_receive.parse_message(raw_message_receive)
        match message_receive.command:
            case ClientCommand.Connect:
                return self.handle_connect_request(message_receive, client_connection)
            case ClientCommand.Reconnect:
                return self.handle_reconnect_request(message_receive)
            case ClientCommand.SetUser:
                return self.handle_change_username_request(message_receive)
            case ClientCommand.Join:
                return self.handle_join_board_request(message_receive)
            case ClientCommand.Leave:
                return self.handle_leave_board_request(message_receive)
            case ClientCommand.Users:
                return self.handle_get_users_request(message_receive)
            case _:
                return self.handle_invalid_command_request(message_receive)
