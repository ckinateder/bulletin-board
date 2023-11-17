import socket
import time


class User:
    """User object. Contains username, socket, and id."""

    def __init__(self, username: str):
        self.username = username
        self.id = hex(hash(str(time.time()) + username))
        self.connected = False

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return (
            f"User(username={self.username}, id={self.id}, connected={self.connected})"
        )
