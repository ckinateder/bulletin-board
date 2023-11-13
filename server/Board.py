from UserContainer import UserContainer

class Board:
    """Bulletin board object. Contains messages and users."""

    def __init__(self, name: str):
        self.name = name
        self.messages = []
        self.users = UserContainer()  # users who are currently viewing this board

    def send_to_all_clients(self, data: str):
        for u in self.users:
            send_to_client(u.socket, data)