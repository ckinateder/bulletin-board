from enum import Enum


class ServerErrorCode(Enum):
    NameTaken = 1
    UserDoesntExist = 2
    InvalidCommand = 3
