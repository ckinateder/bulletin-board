import json


class MessageSend:
    def __init__(self):
        self.username = None
        self.id = None
        self.command = None
        self.acknowledgement_id = None
        self.body = {}

    def create_message(self, username, command, acknowledgementId, body):
        self.username = username
        self.command = command
        self.id = hex(hash(str(command) + username))
        self.acknowledgement_id = acknowledgementId
        self.body = body

    def get_message(self):
        return json.dumps(
            {
                "username": self.username,
                "id": self.id,
                "command": self.command.value,
                "acknowledgement_id": self.acknowledgement_id,
                "body": self.body,
            }
        )
