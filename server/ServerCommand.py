from enum import Enum

class ServerCommand(Enum):
    Connect = 1
    Reconnect = 2
    SetUser = 3
    Join = 4
    PostMade = 5
    Users = 6
    

def client_command_from_value(value):
    for key, member in ServerCommand.__members__.items():
        if member.value == value:
            return key
    raise ValueError(f"No enum key found for value {value}")