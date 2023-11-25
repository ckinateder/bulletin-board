from UserContainer import UserContainer
from BoardPost import BoardPost


class Board:
    """Bulletin board object. Contains messages and users."""

    def __init__(self, name: str):
        self.name = name
        self.posts = []
        self.users = UserContainer()  # users who are currently viewing this board

    def post_to_board(self, user, content):
        self.posts.append(BoardPost(user, content))

    def get_users(self):
        return self.users
    
    def get_posts(self):
        posts = []
        for post in self.posts:
            posts.append(post.get_post())
        return posts
