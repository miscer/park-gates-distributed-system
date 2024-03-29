from amusementpark.messages import NetworkMessage

class GateNode:
    STATE_IDLE = 'idle' # no election is in progress
    STATE_INITIATED = 'initiated' # this node started the election
    STATE_ELECTING = 'electing' # waiting for child nodes to respond
    STATE_WAITING = 'waiting' # waiting for the leader to be announced

    def __init__(self, info, neighbours, repository):
        self.info = info
        self.neighbours = neighbours
        self.repository = repository

        # state attributes related to elections
        self.state = GateNode.STATE_IDLE
        self.parent = None # parent node during election
        self.leader = None # leader node
        self.answers = {} # answers from child nodes

        # state attributes related to mutual exclusion
        self.mutex_holder = None # node currently holding the mutex
        self.mutex_queue = [] # nodes waiting for mutex to be released

        # state attributes related to enter/leave requests
        self.mutex_requested = False
        self.enter_queue = []
        self.leave_queue = []
    
    def process_message(self, message):
        if message.type == 'say_hello':
            yield from self.say_hello()
        elif message.type == 'start_election':
            yield from self.start_election()
        elif message.type == 'remove_leader':
            yield from self.remove_leader()
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
        elif message.type == 'leader_removed':
            yield from self.process_leader_removed(message)
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
    
    def remove_leader(self):
        if self.state != GateNode.STATE_IDLE:
            self.handle_error('Unexpected state')
        
        if self.leader != self.info:
            self.handle_error('Not the leader')
        
        self.leader = None
        
        for neighbour in self.neighbours:
            yield NetworkMessage('leader_removed', self.info, neighbour)
    
    def terminate(self):
        if self.state == GateNode.STATE_IDLE:
            for neighbour in self.neighbours:
                yield NetworkMessage('terminated', self.info, neighbour)
            
            yield None # no more messages will be sent by this node
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
                # in this case there are no children for this node, so it votes for itself as the leader
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

            if self.has_all_answers(): # all children have responded now
                leader = self.get_best_answer() # select the leader

                if self.state == GateNode.STATE_ELECTING: # this is an intermediate node
                    self.state = GateNode.STATE_WAITING
                    yield NetworkMessage('election_voted', self.info, self.parent, leader=leader)
                else: # this is the node which started the election
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
        
        if self.mutex_queue: # some nodes are waiting in the queue
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
            except AssertionError: # if node cannot enter
                yield NetworkMessage('enter_response', self.info, entering_node, allowed=False)
        
        for leaving_node in self.leave_queue:
            try:
                state.leave(leaving_node.id)
                yield NetworkMessage('leave_response', self.info, leaving_node, allowed=True)
            except AssertionError: # if node cannot leave
                yield NetworkMessage('leave_response', self.info, leaving_node, allowed=False)
        
        self.repository.write_state(state)
        
        self.mutex_requested = False
        self.enter_queue = []
        self.leave_queue = []
        
        yield NetworkMessage('mutex_released', self.info, self.leader)
    
    def process_leader_removed(self, message):
        if self.leader is None: # leader was already removed by a previous message
            return
        
        self.leader = None

        for neighbour in self.neighbours:
            if neighbour != message.sender:
                yield NetworkMessage('leader_removed', self.info, neighbour)
    
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

        # select node with the highest capacity
        return max(child_answers + [self.info], key=lambda node: node.capacity)
    
    def handle_error(self, message):
        raise Exception('Node %s: %s' % (self, message))
    
    def __str__(self):
        return '%d/%s' % (self.info.id, self.state)