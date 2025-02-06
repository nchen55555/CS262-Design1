from datetime import datetime

class Message: 
    def __init__(self, sender, receiver, message, timestamp=None):
        self.sender = sender
        self.receiver = receiver
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    