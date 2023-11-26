from enum import Enum


class ServerCommand(Enum):
    Connect = 1
    Reconnect = 2
    SetUser = 3
    Join = 4
    Post = 5
    Users = 6
    Leave = 7
    PostMade = 8
    GetPosts = 9
    CreateBoard = 10
    BoardCreated = 11
    UserJoinedBoard = 12
    Invalid = 99


def client_command_from_value(value):
    for _, member in ServerCommand.__members__.items():
        if member.value == value:
            return member
    raise ValueError(f"No enum key found for value {value}")
