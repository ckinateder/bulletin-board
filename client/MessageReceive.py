import json
import ServerCommand

class MessageReceive:
    def __init__(self, raw_message_receive):
        message = json.loads(raw_message_receive)
        self.id = message['id']
        self.command = ServerCommand.client_command_from_value(int(message['command']))
        self.run_without_id_check = bool(message['run_without_id_check'])
        self.is_success = bool(message['is_success'])
        self.acknowledgement_id = message['acknowledgement_id']
        self.body = message['body']
