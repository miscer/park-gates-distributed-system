from amusementpark.messages import NetworkMessage

class VisitorNode:
    STATE_IDLE = 'idle' # no task is in progress
    STATE_ENTERING = 'entering' # waiting for enter response
    STATE_ENTERED = 'entered' # received enter response allowing the entry
    STATE_LEAVING = 'leaving' # waiting for leave response

    def __init__(self, info):
        self.info = info
        self.state = VisitorNode.STATE_IDLE
    
    def process_message(self, message):
        if message.type == 'enter_park':
            yield from self.enter_park(message)
        elif message.type == 'leave_park':
            yield from self.leave_park(message)
        elif message.type == 'enter_response':
            self.process_enter_response(message)
        elif message.type == 'leave_response':
            self.process_leave_response(message)
    
    def enter_park(self, message):
        gate = message.payload['gate']

        if self.state == VisitorNode.STATE_IDLE:
            yield NetworkMessage('enter_request', self.info, gate)
            self.state = VisitorNode.STATE_ENTERING
        else:
            self.handle_unexpected_state()

    def leave_park(self, message):
        gate = message.payload['gate']

        if self.state == VisitorNode.STATE_ENTERED:
            yield NetworkMessage('leave_request', self.info, gate)
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
        return '%d/%s' % (self.info.id, self.state)