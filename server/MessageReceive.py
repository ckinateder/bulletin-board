import json
import ClientCommand

class MessageReceive:
    """Message object. Contains sender and content."""
    def __init__(self):
        self.id = None
        self.command = None
        self.username = None
        self.acknowledgement_id = None
        self.body = None
    
    def parse_message(self, raw_message):
        message = json.loads(raw_message)
        self.id = message["id"]
        self.command = ClientCommand.client_command_from_value(int(message["command"]))
        self.username = message["username"]
        self.acknowledgement_id = message["acknowledgement_id"]
        self.body = message["body"]
