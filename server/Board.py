from UserContainer import UserContainer
from BoardPost import BoardPost
class Board:
    """Bulletin board object. Contains messages and users."""

    def __init__(self, name: str):
        self.name = name
        self.posts = [BoardPost]
        self.users = UserContainer()  # users who are currently viewing this board

    def get_users(self):
        return self.users
