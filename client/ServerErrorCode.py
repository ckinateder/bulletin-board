from enum import Enum

class ServerErrorCode(Enum):
    NameTaken = 1
    UserDoesntExist = 2
    InvalidCommand = 3
    BoardDoesntExist = 4
    NoPosts = 5
    BoardExists = 6

def server_error_code_from_response(message_response):
    if message_response.is_success:
        return None
    for _, member in ServerErrorCode.__members__.items():
        if member.value == message_response.body["error_code"]:
            return member
    return None