import json
import ServerCommand

class MessageReceive:
    def __init__(self):
        self.id
        self.command
        self.run_without_id_check
        self.is_success
        self.acknowledgement_id
        self.body
    
    def parse_message(self, raw_message):
        message = json.loads(raw_message)
        self.id = message['id']
        self.command = ServerCommand.client_command_from_value(int(message['command']))
        self.run_without_id_check = bool(message['run_without_id_check'])
        self.is_success = bool(message['is_success'])
        self.acknowledgement_id = message['acknowledgement_id']
        self.body = json.loads(message['body'])
