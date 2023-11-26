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
        match (user, self.lobby.does_username_already_exsist(new_username)):
            case (None, _):
                message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
                message_send = MessageSend(message_receive.username, ServerCommand.SetUser, False, False, message_receive.id, message_body_send)
            case (_, True):
                message_body_send = {"error_code": ServerErrorCode.NameTaken, "new_username": new_username}
                message_send = MessageSend(user.username, ServerCommand.SetUser, False, False, message_receive.id, message_body_send)
            case (_, _):
                user.username = new_username
                message_body_send = {"id": user.id, "new_username": new_username}
                self.lobby.log.add(user.id, "username_change", user.username)
                message_send = MessageSend(user.username, ServerCommand.SetUser, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_join_board_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board = self.lobby.get_board_by_name(message_receive.body["board_name"])
        match (user, board):
                case (None, _):
                    message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
                    message_send = MessageSend(message_receive.username, ServerCommand.Join, False, False, message_receive.id, message_body_send)
                case (_, None):
                    message_body_send = {"error_code": ServerErrorCode.BoardDoesntExist}
                    message_send = MessageSend(message_receive.username, ServerCommand.Join, False, False, message_receive.id, message_body_send)
                case(_, _):
                    self.lobby.add_user_to_board(user, board.name)
                    message_body_send = {"board_name": board.name}
                    message_send = MessageSend(user.username, ServerCommand.Join, False, True, message_receive.id, message_body_send)
                    message_body_send_to_all = {"username": message_receive.username, "board_name": board.name}
                    message_send_to_all = MessageSend(user.username, ServerCommand.UserJoinedBoard, True, True, message_receive.id, message_body_send_to_all)
                    users_in_board = board.get_users()
                    self.send_to_all_clients(message_send_to_all, users_in_board)
        return message_send

    def handle_leave_board_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board = self.lobby.get_board_by_name(message_receive.body["board_name"])
        match (user, board):
                case (None, _):
                    message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
                    message_send = MessageSend(message_receive.username, ServerCommand.Leave, False, False, message_receive.id, message_body_send)
                case (_, None):
                    message_body_send = {"error_code": ServerErrorCode.BoardDoesntExist}
                    message_send = MessageSend(message_receive.username, ServerCommand.Leave, False, False, message_receive.id, message_body_send)
                case (_, _):
                    self.lobby.remove_user_from_board(user, board.name)
                    message_body_send = {"board_name": board.name}
                    message_send = MessageSend(user.username, ServerCommand.Leave, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_get_users_request(self, message_receive):
            user = self.lobby.users.get_user_by_id(message_receive.body["id"])
            board = self.lobby.get_board_by_name(message_receive.body["board_name"])
            match (user, board):
                case (None, _):
                    message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
                    message_send = MessageSend(message_receive.username, ServerCommand.Users, False, False, message_receive.id, message_body_send)
                case (_, None):
                    message_body_send = {"error_code": ServerErrorCode.BoardDoesntExist}
                    message_send = MessageSend(message_receive.username, ServerCommand.Users, False, False, message_receive.id, message_body_send)
                case (_, _):
                    users_in_board = board.get_users().get_all_usernames()
                    message_body_send = {"users": users_in_board}
                    message_send = MessageSend(message_receive.username, ServerCommand.Users, False, True, message_receive.id, message_body_send)
            return message_send
    
    def handle_post_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board = self.lobby.get_board_by_name(message_receive.body["board_name"])
        content = message_receive.body["content"]
        match (user, board):
            case (None, _):
                message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
                message_send = MessageSend(message_receive.username, ServerCommand.Post, False, False, message_receive.id, message_body_send)
            case (_, None):
                message_body_send = {"error_code": ServerErrorCode.BoardDoesntExist}
                message_send = MessageSend(message_receive.username, ServerCommand.Post, False, False, message_receive.id, message_body_send)
            case (_, _):
                board.post_to_board(user, content)
                message_body_send = {"board_name": board.name}
                message_send = MessageSend(message_receive.username, ServerCommand.Post, False, True, message_receive.id, message_body_send)
                message_body_send_to_all = {"username": message_receive.username, "board_name": board.name}
                message_send_to_all = MessageSend(message_receive.username, ServerCommand.PostMade, True, True, "", message_body_send_to_all)
                users_in_board = board.get_users()
                self.send_to_all_clients(message_send_to_all, users_in_board)
        return message_send

    def handle_get_posts_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board = self.lobby.get_board_by_name(message_receive.body["board_name"])
        match (user, board):
            case (None, _):
                message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
                message_send = MessageSend(message_receive.username, ServerCommand.GetPosts, False, False, message_receive.id, message_body_send)
            case (_, None):
                message_body_send = {"error_code": ServerErrorCode.BoardDoesntExist}
                message_send = MessageSend(message_receive.username, ServerCommand.GetPosts, False, False, message_receive.id, message_body_send)
            case (_, _):
                posts = board.get_posts()
                if (posts == []):
                    message_body_send = {"error_code": ServerErrorCode.NoPosts}
                    message_send = MessageSend(message_receive.username, ServerCommand.GetPosts, False, False, message_receive.id, message_body_send)
                else:
                    message_body_send = {"posts": posts}
                    message_send = MessageSend(message_receive.username, ServerCommand.GetPosts, False, True, message_receive.id, message_body_send)

        return message_send
    
    def handle_create_board_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        new_board_name = message_receive.body["new_board_name"]
        current_board_name = message_receive.body["current_board_name"]
        board_exists = self.lobby.board_exists(new_board_name)
        match (user, board_exists):
            case (None, _):
                message_body_send = {"error_code": ServerErrorCode.UserDoesntExist}
                message_send = MessageSend(message_receive.username, ServerCommand.CreateBoard, False, False, message_receive.id, message_body_send)
            case (_, True):
                message_body_send = {"error_code": ServerErrorCode.BoardExists}
                message_send = MessageSend(message_receive.username, ServerCommand.CreateBoard, False, False, message_receive.id, message_body_send)
            case (_, _):
                if current_board_name:
                    self.lobby.remove_user_from_board(user, current_board_name)
                self.lobby.new_board(new_board_name)
                self.lobby.add_user_to_board(user, new_board_name)
                message_body_send = {"board_name": new_board_name}
                message_send = MessageSend(message_receive.username, ServerCommand.CreateBoard, False, True, message_receive.id, message_body_send)
                message_body_send_to_all = {"username": message_receive.username, "board_name": new_board_name}
                message_send_to_all = MessageSend(message_receive.username, ServerCommand.BoardCreated, True, True, "", message_body_send_to_all)
                users_in_lobby = self.lobby.get_users()
                self.send_to_all_clients(message_send_to_all, users_in_lobby)
        return message_send

    def handle_invalid_command_request(self, message_receive):
        message_body_send = {"error_code": ServerErrorCode.InvalidCommand}
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
            case ClientCommand.Post:
                return self.handle_post_request(message_receive)
            case ClientCommand.GetPosts:
                return self.handle_get_posts_request(message_receive)
            case ClientCommand.CreateBoard:
                return self.handle_create_board_request(message_receive)
            case _:
                return self.handle_invalid_command_request(message_receive)
