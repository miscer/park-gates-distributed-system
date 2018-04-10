class Message:
    def __init__(self, message_type, **payload):
        self.type = message_type
        self.payload = payload
    
    def __eq__(self, other):
        return isinstance(other, Message) and \
            self.type == other.type and \
            self.payload == other.payload

    def __str__(self):
        return '%s %s' % (self.type, self.payload)

class NetworkMessage(Message):
    def __init__(self, message_type, sender, recipient, **payload):
        super().__init__(message_type, **payload)
        self.sender = sender
        self.recipient = recipient
    
    def __eq__(self, other):
        return super().__eq__(other) and \
            self.sender == other.sender and \
            self.recipient == other.recipient
    