import time

class BoardPost:
    def __init__(self):
        self.user
        self.content
        self.time = time.time()

    def create_post(self, user, content):
        self.user = user
        self.content = content
    
    def get_post(self):
        return {
            "user": self.user,
            "content": self.content,
            "time": self.time
        }
