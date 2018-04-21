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
        elif message.type == 'terminate':
            yield from self.terminate()
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
        elif message.type == 'terminated':
            self.process_terminated(message)
    
    def say_hello(self):
        for neighbour in self.neighbours:
            yield NetworkMessage('hello', self.info, neighbour)

    def start_election(self):
        if self.state == GateNode.STATE_IDLE:
            self.state = GateNode.STATE_INITIATED
            
            self.parent = None
            self.leader = None
            self.answers = {}

            for neighbour in self.neighbours:
                yield NetworkMessage('election_started', self.info, neighbour)
        else:
            self.handle_error('Unexpected state')
    
    def terminate(self):
        if self.state == GateNode.STATE_IDLE:
            for neighbour in self.neighbours:
                yield NetworkMessage('terminated', self.info, neighbour)
            
            yield None
        else:
            self.handle_error('Unexpected state')
    
    def process_hello(self, message):
        yield NetworkMessage('hey', self.info, message.sender)
    
    def process_election_started(self, message):
        if self.state == GateNode.STATE_IDLE:
            self.state = GateNode.STATE_ELECTING

            self.parent = message.sender
            self.leader = None
            self.answers = {}

            for child in self.get_children():
                yield NetworkMessage('election_started', self.info, child)
            
            if self.has_all_answers():
                self.state = GateNode.STATE_WAITING
                yield NetworkMessage('election_voted', self.info, message.sender, leader=self.info)
        
        elif self.state in (GateNode.STATE_ELECTING, GateNode.STATE_INITIATED):
            yield NetworkMessage('election_voted', self.info, message.sender, leader=None)

        else:
            self.handle_error('Unexpected state')
    
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
            self.handle_error('Unexpected state')

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
            self.handle_error('Not a leader')

        if self.mutex_holder is None:
            self.handle_error('No mutex holder')

        if self.mutex_holder != message.sender:
            self.handle_error('Invalid sender')
        
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
            self.handle_error('Mutex not requested')
        
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
        
        self.mutex_requested = False
        self.enter_queue = []
        self.leave_queue = []
        
        yield NetworkMessage('mutex_released', self.info, self.leader)
    
    def process_terminated(self, message):
        if self.state != GateNode.STATE_IDLE:
            self.handle_error('Unexpected state')
        
        self.neighbours.remove(message.sender)

    def get_children(self):
        if self.state == GateNode.STATE_INITIATED:
            return self.neighbours
        elif self.state == GateNode.STATE_ELECTING:
            return [child for child in self.neighbours if child != self.parent]
        else:
            self.handle_error('Unexpected state')
    
    def has_all_answers(self):
        return all(child in self.answers for child in self.get_children())
    
    def get_best_answer(self):
        child_answers = [
            self.answers[child]
            for child in self.get_children()
            if self.answers[child] is not None
        ]

        return max(child_answers + [self.info], key=lambda node: node.capacity)
    
    def handle_error(self, message):
        raise Exception('Node %s: %s' % (self, message))
    
    def __str__(self):
        return '%d/%s' % (self.info.id, self.state)