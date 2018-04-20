from amusementpark.messages import NetworkMessage

class GateNode:
    STATE_IDLE = 'idle'
    STATE_INITIATED = 'initiated'
    STATE_ELECTING = 'electing'
    STATE_WAITING = 'waiting'

    def __init__(self, info, neighbours, repository):
        self.info = info
        self.neighbours = neighbours
        self.repository = repository

        self.state = GateNode.STATE_IDLE
        self.parent = None
        self.leader = None
        self.answers = {}

        self.mutex_holder = None
        self.mutex_queue = []

        self.mutex_requested = False
        self.enter_queue = []
        self.leave_queue = []
    
    def process_message(self, message):
        if message.type == 'say_hello':
            yield from self.say_hello()
        elif message.type == 'start_election':
            yield from self.start_election()
        elif message.type == 'hello':
            yield from self.process_hello(message)
        elif message.type == 'election_started':
            yield from self.process_election_started(message)
        elif message.type == 'election_voted':
            yield from self.process_election_voted(message)
        elif message.type == 'election_finished':
            yield from self.process_election_finished(message)
        elif message.type == 'mutex_requested':
            yield from self.process_mutex_requested(message)
        elif message.type == 'mutex_released':
            yield from self.process_mutex_released(message)
        elif message.type == 'enter_request':
            yield from self.process_enter_request(message)
        elif message.type == 'leave_request':
            yield from self.process_leave_request(message)
        elif message.type == 'mutex_granted':
            yield from self.process_mutex_granted(message)
    
    def say_hello(self):
        for neighbour in self.neighbours:
            yield NetworkMessage('hello', self.info, neighbour)

    def start_election(self):
        if self.state == GateNode.STATE_IDLE:
            self.state = GateNode.STATE_INITIATED

            for neighbour in self.neighbours:
                yield NetworkMessage('election_started', self.info, neighbour)
        else:
            raise Exception('Unexpected state')
    
    def process_hello(self, message):
        yield NetworkMessage('hey', self.info, message.sender)
    
    def process_election_started(self, message):
        if self.state == GateNode.STATE_IDLE:
            self.state = GateNode.STATE_ELECTING
            self.parent = message.sender

            for child in self.get_children():
                yield NetworkMessage('election_started', self.info, child)
        
        elif self.state in (GateNode.STATE_ELECTING, GateNode.STATE_INITIATED):
            yield NetworkMessage('election_voted', self.info, message.sender, leader=None)

        else:
            raise Exception('Unexpected state')
    
    def process_election_voted(self, message):
        leader = message.payload['leader']

        if self.state in (GateNode.STATE_ELECTING, GateNode.STATE_INITIATED):
            self.answers[message.sender] = leader

            if self.has_all_answers():
                leader = self.get_best_answer()

                if self.state == GateNode.STATE_ELECTING:
                    self.state = GateNode.STATE_WAITING
                    yield NetworkMessage('election_voted', self.info, self.parent, leader=leader)
                else:
                    self.state = GateNode.STATE_IDLE
                    self.leader = leader
                    
                    for neighbour in self.neighbours:
                        yield NetworkMessage('election_finished', self.info, neighbour, leader=leader)
        else:
            raise Exception('Unexpected state')

    def process_election_finished(self, message):
        leader = message.payload['leader']

        if self.state == GateNode.STATE_WAITING:
            self.state = GateNode.STATE_IDLE
            self.leader = leader

            for neighbour in self.neighbours:
                if neighbour != message.sender:
                    yield NetworkMessage('election_finished', self.info, neighbour, leader=leader)
    
    def process_mutex_requested(self, message):
        if self.mutex_holder is None:
            self.mutex_holder = message.sender
            yield NetworkMessage('mutex_granted', self.info, self.mutex_holder)
        else:
            self.mutex_queue.append(message.sender)
            
    def process_mutex_released(self, message):
        if self.leader != self.info:
            raise Exception('Not a leader')

        if self.mutex_holder is None:
            raise Exception('No mutex holder')

        if self.mutex_holder is not message.sender:
            raise Exception('Invalid sender')
        
        if self.mutex_queue:
            self.mutex_holder = self.mutex_queue.pop(0)
            yield NetworkMessage('mutex_granted', self.info, self.mutex_holder)
        else:
            self.mutex_holder = None
    
    def process_enter_request(self, message):
        if not self.mutex_requested:
            yield NetworkMessage('mutex_requested', self.info, self.leader)
            self.mutex_requested = True
        
        self.enter_queue.append(message.sender)
    
    def process_leave_request(self, message):
        if not self.mutex_requested:
            yield NetworkMessage('mutex_requested', self.info, self.leader)
            self.mutex_requested = True
        
        self.leave_queue.append(message.sender)
    
    def process_mutex_granted(self, message):
        if not self.mutex_requested:
            raise Exception('Mutex not requested')
        
        state = self.repository.read_state()
        
        for entering_node in self.enter_queue:
            try:
                state.enter(entering_node.id)
                yield NetworkMessage('enter_response', self.info, entering_node, allowed=True)
            except AssertionError:
                yield NetworkMessage('enter_response', self.info, entering_node, allowed=False)
        
        for leaving_node in self.leave_queue:
            try:
                state.leave(leaving_node.id)
                yield NetworkMessage('leave_response', self.info, leaving_node, allowed=True)
            except AssertionError:
                yield NetworkMessage('leave_response', self.info, leaving_node, allowed=False)
        
        self.repository.write_state(state)
        
        self.enter_queue = []
        self.leave_queue = []
        
        yield NetworkMessage('mutex_released', self.info, self.leader)

    def get_children(self):
        if self.state == GateNode.STATE_INITIATED:
            return self.neighbours
        elif self.state == GateNode.STATE_ELECTING:
            return [child for child in self.neighbours if child != self.parent]
        else:
            raise Exception('Unexpected state')
    
    def has_all_answers(self):
        return all(child in self.answers for child in self.get_children())
    
    def get_best_answer(self):
        child_answers = [
            self.answers[child]
            for child in self.get_children()
            if self.answers[child] is not None
        ]

        return max(child_answers + [self.info], key=lambda node: node.capacity)
    
    def __str__(self):
        return '%d/%s' % (self.info.id, self.state)