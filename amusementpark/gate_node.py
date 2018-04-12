from amusementpark.messages import NetworkMessage

class GateNode:
    STATE_IDLE = 'idle'
    STATE_INITIATED = 'initiated'
    STATE_ELECTING = 'electing'
    STATE_WAITING = 'waiting'

    def __init__(self, node_id, neighbour_ids):
        self.id = node_id
        self.neighbour_ids = neighbour_ids
        self.state = GateNode.STATE_IDLE
        self.parent_id = None
        self.answers = {}
    
    def process_message(self, message):
        if message.type == 'say_hello':
            yield from self.say_hello()
        elif message.type == 'start_election':
            yield from self.start_election()
        elif message.type == 'hello':
            yield from self.process_hello(message)
        elif message.type == 'election':
            yield from self.process_election(message)
        elif message.type == 'ack':
            yield from self.process_ack(message)
        elif message.type == 'leader':
            yield from self.process_leader(message)
    
    def say_hello(self):
        for neighbour_id in self.neighbour_ids:
            yield NetworkMessage('hello', self.id, neighbour_id)

    def start_election(self):
        if self.state == GateNode.STATE_IDLE:
            self.state = GateNode.STATE_INITIATED

            for neighbour_id in self.neighbour_ids:
                yield NetworkMessage('election', self.id, neighbour_id)
        else:
            raise Exception('Unexpected state')
    
    def process_hello(self, message):
        yield NetworkMessage('hey', self.id, message.sender)
    
    def process_election(self, message):
        if self.state == GateNode.STATE_IDLE:
            self.state = GateNode.STATE_ELECTING
            self.parent_id = message.sender

            for child_id in self.get_child_ids():
                yield NetworkMessage('election', self.id, child_id)
        
        elif self.state in (GateNode.STATE_ELECTING, GateNode.STATE_INITIATED):
            yield NetworkMessage('ack', self.id, message.sender, leader=None)

        else:
            raise Exception('Unexpected state')
    
    def process_ack(self, message):
        leader_id = message.payload['leader']

        if self.state in (GateNode.STATE_ELECTING, GateNode.STATE_INITIATED):
            self.answers[message.sender] = leader_id

            if self.has_all_answers():
                leader = self.get_best_answer()

                if self.state == GateNode.STATE_ELECTING:
                    self.state = GateNode.STATE_WAITING
                    yield NetworkMessage('ack', self.id, self.parent_id, leader=leader)
                else:
                    self.state = GateNode.STATE_IDLE
                    
                    for neighbour_id in self.neighbour_ids:
                        yield NetworkMessage('leader', self.id, neighbour_id, leader=leader)
        else:
            raise Exception('Unexpected state')

    def process_leader(self, message):
        leader_id = message.payload['leader']

        if self.state == GateNode.STATE_WAITING:
            self.state = GateNode.STATE_IDLE

            for neighbour_id in self.neighbour_ids:
                if neighbour_id != message.sender:
                    yield NetworkMessage('leader', self.id, neighbour_id, leader=leader_id)

    def get_child_ids(self):
        if self.state == GateNode.STATE_INITIATED:
            return self.neighbour_ids
        elif self.state == GateNode.STATE_ELECTING:
            return [child_id for child_id in self.neighbour_ids if child_id != self.parent_id]
        else:
            raise Exception('Unexpected state')
    
    def has_all_answers(self):
        return all(child_id in self.answers for child_id in self.get_child_ids())
    
    def get_best_answer(self):
        child_answers = [
            self.answers[child_id]
            for child_id in self.get_child_ids()
            if self.answers[child_id] is not None
        ]

        return max(child_answers + [self.id])
    
    def __str__(self):
        return '%d/%s' % (self.id, self.state)