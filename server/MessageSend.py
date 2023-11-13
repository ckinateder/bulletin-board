
class MessageSend:
    def __init__(self):
        self.id
        self.command
        self.run_without_id_check
        self.is_success
        self.acknowledgement_id
        self.body
    
    def create_message(self, client_username, command, is_success, run_without_id_check, acknowledgement_id, body):
        self.id = hex(hash(str(command) + client_username + str(is_success)))
        self.command = command
        self.run_without_id_check = run_without_id_check
        self.self.acknowledgement_id = acknowledgement_id
        self.body = body
    
    def get_message(self):
        return {
            "id": self.id,
            "command": self.command.value,
            "run_without_id_check": self.run_without_id_check,
            "is_success": self.is_success,
            "acknowledgement_id": self.acknowledgement_id,
            "body": self.body
        }