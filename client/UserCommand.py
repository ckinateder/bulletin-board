from enum import Enum


class UserCommand(Enum):
    Connect = ("connect", "<host>:<port> - connect to a server")
    Setuser = ("setuser", "<username> - set your username")
    Join = ("join", "<board> - join a board")
    Leave = ("leave", "<board> - leave a board")
    Users = ("users", "<board> - list users on a board")
    Disconnect = ("disconnect", "disconnect from the server")
    Exit = ("exit", "exit the program")
    Help = ("help", "show this help message")
    Post = ("post", "<message> - post a message to the current board")
    GetPosts = ("getposts", "<content> - get the messages that have been posted to a board")
    CreateBoard = ("newboard", "<boardname> - creates a new board on the server.")

    def get_commands(escape_char:str="/"):
        return [escape_char+command.value[0] for command in UserCommand]


def compare_commands(command:UserCommand, user_command:str, escape_char:str="/"):
    if user_command.startswith(escape_char+command.value[0]):
        return True
    else:
        return False

def user_command_from_value(value):
    for _, member in UserCommand.__members__.items():
        if member.value == value:
            return "/" + member
    raise ValueError(f"No enum key found for value {value}")
