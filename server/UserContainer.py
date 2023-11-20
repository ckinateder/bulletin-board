from User import User


class UserContainer:

    """Container for users. Contains methods for adding, removing, and getting users."""

    def __init__(self):
        self.users = []

    def add_user(self, user: User):
        for u in self.users:
            if user == u:  # user already exists
                return False
        self.users.append(user)
        return True

    def remove_user(self, user: User):
        for u in self.users:
            if user == u:
                self.users.remove(user)
                return True
        return False

    def get_user_by_id(self, userid: str):
        for user in self.users:
            if user.id == userid:
                return user
        return None

    def get_all_users(self):
        return self.users

    def get_all_usernames(self):
        return [user.username for user in self.users]

    def __str__(self):
        if len(self.users) == 0:
            return "UserContainer(users=[])"
        s = "UserContainer(users=[\n"
        for entry in self.users:
            s += f"  {entry}\n"
        s += "])"
        return s

    def __iter__(self):
        return iter(self.users)
