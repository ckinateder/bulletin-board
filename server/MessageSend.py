import json


class MessageSend:
    def __init__(
        self,
        client_username,
        command,
        run_without_id_check,
        is_success,
        acknowledgement_id,
        body,
    ):
        self.id = hex(hash(str(command) + client_username + str(is_success)))
        self.command = command
        self.run_without_id_check = run_without_id_check
        self.is_success = is_success
        self.acknowledgement_id = acknowledgement_id
        self.body = body

    def get_message(self):
        return json.dumps(
            {
                "id": self.id,
                "command": self.command.value,
                "run_without_id_check": self.run_without_id_check,
                "is_success": self.is_success,
                "acknowledgement_id": self.acknowledgement_id,
                "body": self.body,
            }
        )
