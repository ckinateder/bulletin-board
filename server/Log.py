import time

class Log:
    """Hold a log of what happens"""

    def __init__(self):
        self.log = []

    def add(self, id: str, type: str, data: str = None, echo=True):
        """Add an entry to the log.

        Args:
            id (str): id
            type (str): type of entry
            data (str, optional): any extra info. Defaults to None.
        """
        record = {id: {"time": time.time(), "type": type, "data": data}}
        self.log.append(record)
        if echo:
            print(f"{record}")

    def __str__(self):
        if len(self.log) == 0:
            return "Log(log=[])"
        s = "ConnectionsLog(log=[\n"
        for entry in self.log:
            s += f"  {entry}\n"
        s += "])"
        return s