from queue import Queue
from threading import Thread
from collections import defaultdict
import logging

log = logging.getLogger('amusementpark.broker')

class Broker:
    END = 'end'

    def __init__(self):
        self.incoming_messages = Queue()
        self.outgoing_messages = defaultdict(Queue)
    
    def run(self, node):
        thread = Thread(target=self.process_messages, args=(node,))
        thread.start()
        return thread
    
    def process_messages(self, node):
        while True:
            incoming_message = self.incoming_messages.get()

            if incoming_message == Broker.END:
                break
            
            log.info('Receive from %s: %s', incoming_message.sender, incoming_message)
            
            for outgoing_message in node.process_message(incoming_message):
                recipient = outgoing_message.recipient
                log.info('Send to %s: %s', recipient, outgoing_message)
                self.outgoing_messages[recipient].put(outgoing_message)
    
    def add_incoming_message(self, message):
        self.incoming_messages.put(message)
    
    def get_outgoing_messages(self, recipient):
        return self.outgoing_messages[recipient]
