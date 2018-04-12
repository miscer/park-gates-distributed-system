class Node:
    def __init__(self, id):
        self.id = id
        self.incoming_messages = []
        self.outgoing_messages = []

    def process_message(self, message):
        raise NotImplementedError('process_message is not implemented')
    
    def send_message(self, message):
        self.outgoing_messages.append(message)
    