import time
import json
import ClientCommand

class MessageReceive:
    """Message object. Contains sender and content."""

    def __init__(self):
        self.message_id
        self.command
        self.sender_username
        self.acknowledgement_id
        self.body
        self.time = time.time()
    
    def parse_message(self, client_username, raw_message):
        message = json.loads(raw_message)
        self.message.id = message["id"]
        self.command = ClientCommand.client_command_from_value(int(message["command"]))
        self.sender_username = client_username
        self.acknowledgement_id = message["acknowledgement_id"]
        self.body = json.loads(message["body"])
