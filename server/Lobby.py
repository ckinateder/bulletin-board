from UserContainer import UserContainer
from Log import Log
from User import User
from Board import Board


class Lobby:
    """Contains all bulletin boards."""

    def __init__(self):
        self.users = UserContainer()
        self.log = Log()
        self.boards = []

    def new_board(self, name: str):
        self.boards.append(Board(name))

    def add_user_to_lobby(self, user: User):
        self.users.add_user(user)
        self.log.add(user.id, "connect")  # log the connection

    def add_user_to_board(self, user: User, board_name: str):
        self.get_board_by_name(board_name).users.add_user(user)
        self.log.add(user.id, "board_join", board_name)
        # now notify all users on the board that a new user has joined

    def remove_user_from_board(self, user: User, board_name: str):
        self.get_board_by_name(board_name).users.remove_user(user)
        self.log.add(user.id, "board_leave", board_name)

    def get_board_by_name(self, name: str):
        for board in self.boards:
            if board.name == name:
                return board
        return None

    def does_username_already_exsist(self, username):
        return username in self.users.get_all_usernames()
