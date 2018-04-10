from amusementpark.messages import NetworkMessage

class GateNode:
    def __init__(self, node_id, neighbour_ids):
        self.id = node_id
        self.neighbour_ids = neighbour_ids
    
    def process_message(self, message):
        if message.type == 'hello':
            yield NetworkMessage('hey', self.id, message.sender)
        if message.type == 'say_hello':
            yield from self.say_hello()
    
    def say_hello(self):
        for neighbour_id in self.neighbour_ids:
            yield NetworkMessage('hello', self.id, neighbour_id)
        