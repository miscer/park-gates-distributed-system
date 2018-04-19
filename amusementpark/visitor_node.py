from amusementpark.messages import NetworkMessage

class VisitorNode:
    STATE_IDLE = 'idle'
    STATE_ENTERING = 'entering'
    STATE_ENTERED = 'entered'
    STATE_LEAVING = 'leaving'

    def __init__(self, node_id, gate_id):
        self.id = node_id
        self.gate_id = gate_id
        self.state = VisitorNode.STATE_IDLE
    
    def process_message(self, message):
        if message.type == 'enter_park':
            yield from self.enter_park()
        elif message.type == 'leave_park':
            yield from self.leave_park()
        elif message.type == 'enter_response':
            self.process_enter_response(message)
        elif message.type == 'leave_response':
            self.process_leave_response(message)
    
    def enter_park(self):
        if self.state == VisitorNode.STATE_IDLE:
            yield NetworkMessage('enter_request', self.id, self.gate_id)
            self.state = VisitorNode.STATE_ENTERING
        else:
            self.handle_unexpected_state()

    def leave_park(self):
        if self.state == VisitorNode.STATE_ENTERED:
            yield NetworkMessage('leave_request', self.id, self.gate_id)
            self.state = VisitorNode.STATE_LEAVING
        else:
            self.handle_unexpected_state()
    
    def process_enter_response(self, message):
        allowed = message.payload['allowed']

        if self.state == VisitorNode.STATE_ENTERING:
            if allowed:
                self.state = VisitorNode.STATE_ENTERED
            else:
                self.state = VisitorNode.STATE_IDLE
        else:
            self.handle_unexpected_state()

    def process_leave_response(self, message):
        allowed = message.payload['allowed']

        if self.state == VisitorNode.STATE_LEAVING:
            if allowed:
                self.state = VisitorNode.STATE_IDLE
            else:
                self.state = VisitorNode.STATE_ENTERED
        else:
            self.handle_unexpected_state()

    def handle_unexpected_state(self):
        raise Exception('Unexpected state')
    
    def __str__(self):
        return '%d/%s' % (self.id, self.state)