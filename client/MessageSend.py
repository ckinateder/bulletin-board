
class MessageSend:
    def __init__(self):
        self.id
        self.command
        self.acknowledgement_id
        self.body

    def create_message(self, username, command, acknowledgementId, body):
        self.command = command
        self.id = hex(hash(str(command) + username))
        self.acknowledgement_id = acknowledgementId
        self.body = body

    def get_message(self):
        return {
            "id": self.id,
            "command": self.command.value,
            "acknowledgement_id": self.acknowledgement_id,
            "body": self.body
        }