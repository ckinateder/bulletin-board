import socket
import json
from User import User
from Lobby import Lobby
from ClientCommand import ClientCommand
from ServerCommand import ServerCommand
from ServerErrorCode import ServerErrorCode
from MessageReceive import MessageReceive
from MessageSend import MessageSend
class Server:
    def __init__(self, lobby: Lobby):
        self.lobby = lobby
    
    def handle_connect_request(self, message_receive):
        if (self.lobby.does_username_already_exsist(message_receive.username) or message_receive.username == ""): # Invalid connection attempt
            message_body_send = {"error_code": ServerErrorCode.NameTaken, "message": ":".join(self.lobby.users.get_all_usernames())}
            message_send = MessageSend(message_receive.username, ServerCommand.Connect, False, False, message_receive.id, message_body_send)
            return message_send
        
        user = User(message_receive.username)  # create the user
        user.connected = True  # connect the user
        self.lobby.add_user_to_lobby(user)  # add the user to the list of users
        message_body_send = {"username": user.username, "id": user.id}
        message_send = MessageSend(user.username, ServerCommand.Connect, False, True, message_receive.id, message_body_send)
        return message_send
            
    def handle_reconnect_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        if not user:
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist, "message": "Your connection is still open, but your id doesn't match any existing users."}
            message_send = MessageSend(message_receive.username, ServerCommand.Reconnect, False, False, message_receive.id, message_body_send)
            return message_send
        
        match (user.username == message_receive.sender_username, self.lobby.does_username_already_exsist(message_receive.username)):
            case (False, True): # user's username changed, and the new username already exists
                message_body_send = {"error_code": ServerErrorCode.NameTaken, "message": ":".join(self.lobby.users.get_all_usernames())}
                message_send = MessageSend(user.username, ServerCommand.Reconnect, False, False, message_receive.id, message_body_send)
                return message_send
            case (False, False): # user's username changed. The username doesn't already exist and the user's username changes
                user.username = message_receive.sender_username
                user.connected = True
                message_body_send = {"username": user.username, "id": user.id}
                self.lobby.log.add(user.id, "reconnect")
                self.lobby.log.add(user.id, "username_change", user.username)
                message_send = MessageSend(user.username, ServerCommand.Reconnect, False, True, message_receive.id, message_body_send)
                return message_send
            case _: # user's username is the same
                user.connected = True
                message_body_send = {"username": user.username, "id": user.id}
                self.lobby.log.add(user.id, "reconnect")
                message_send = MessageSend(user.username, ServerCommand.Reconnect, False, True, message_receive.id, message_body_send)
                return message_send
    
    def handle_change_username_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        if not user: # User doesn't exist. Invalid request
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist, "message": "Your connection is still open, but your id doesn't match any existing users."}
            message_send = MessageSend(message_receive.username, ServerCommand.SetUser, False, False, message_receive.id, message_body_send)
            return message_send
        
        if self.lobby.does_username_already_exsist(message_receive.username): # Username is already taken
            message_body_send = {"error_code": ServerErrorCode.NameTaken, "message": ":".join(self.lobby.users.get_all_usernames())}
            message_send = MessageSend(user.username, ServerCommand.SetUser, False, False, message_receive.id, message_body_send)
            return message_send
        
        # user's username changed. The username doesn't already exist and the user's username changes
        user.username = message_receive.sender_username
        user.connected = True
        message_body_send = {"username": user.username, "id": user.id}
        self.lobby.log.add(user.id, "username_change", user.username)
        message_send = MessageSend(user.username, ServerCommand.SetUser, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_join_board_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board_name = message_receive.body["board_name"]
        if not user: # User doesn't exist. Invalid request
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist, "message": "Your connection is still open, but your id doesn't match any existing users."}
            message_send = MessageSend(message_receive.username, ServerCommand.Join, False, False, message_receive.id, message_body_send)
            return message_send
        
        #TODO: add chacking to make sure the requested board exisists.
        self.lobby.add_user_to_board(user, board_name)
        message_body_send = {"board_name": board_name}
        message_send = MessageSend(user.username, ServerCommand.Join, False, True, message_receive.id, message_body_send)
        return message_send
    
    def handle_leave_board_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board_name = message_receive.body["board_name"]
        if not user: # User doesn't exist. Invalid request
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist, "message": "Your connection is still open, but your id doesn't match any existing users."}
            message_send = MessageSend(message_receive.username, ServerCommand.Leave, False, False, message_receive.id, message_body_send)
            return message_send
        
        #TODO: add checking to make sure the user is in that board. And that the board exisists
        self.lobby.remove_user_from_board(user, board_name)
        message_body_send = {"board_name": board_name}
        message_send = MessageSend(user.username, ServerCommand.Leave, False, True, message_receive.id, message_body_send)
        return message_send
    
    def handle_get_users_request(self, message_receive):
        user = self.lobby.users.get_user_by_id(message_receive.body["id"])
        board_name = message_receive.body["board_name"]
        if not user: # User doesn't exist. Invalid request
            message_body_send = {"error_code": ServerErrorCode.UserDoesntExist, "message": "Your connection is still open, but your id doesn't match any existing users."}
            message_send = MessageSend(message_receive.username, ServerCommand.Users, False, False, message_receive.id, message_body_send)
            return message_send

        #TODO: add checking to make sure the user is in that board. And that the board exisists
        users_in_board = self.lobby.get_board_by_name(board_name).get_users()
        message_body_send = {"users": users_in_board}
        message_send = MessageSend(message_receive.username, ServerCommand.Users, False, True, message_receive.id, message_body_send)
        return message_send

    def handle_invalid_command_request(self, message_receive):
        message_body_send = {"error_code": ServerErrorCode.InvalidCommand, "message": f"{message_receive.command} is an invalid command."}
        message_send = MessageSend(message_receive.username, ServerCommand.Invalid, False, False, message_receive.id, message_body_send)
        return message_send
    
    def handle_inbound_request(self, raw_message_receive):
        message_receive = MessageReceive()
        message_receive.parse_message(raw_message_receive)
        match message_receive.command:
            case ClientCommand.Connect:
                return self.handle_connect_request(message_receive)
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
        