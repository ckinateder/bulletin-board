import time

class BoardPost:
    def __init__(self, user, content):
        self.user = user
        self.content = content
        self.time = time.time()

    def get_post(self):
        return {"username": self.user.username, "content": self.content, "time": self.time}
