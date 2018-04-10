from amusementpark.messages import NetworkMessage

class GateNode:
    def __init__(self, node_id):
        self.id = node_id
    
    def process_message(self, message):
        if message.type == 'hello':
            yield NetworkMessage('hey', self.id, message.sender)
