from enum import Enum

class ServerErrorCode(Enum):
    NameTaken = 1
    UserDoesntExist = 2
    InvalidCommand = 3
    BoardDoesntExist = 4
    NoPosts = 5
    BoardExists = 6
