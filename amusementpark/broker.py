from queue import Queue
from threading import Thread
from collections import defaultdict
import logging
from amusementpark.messages import NetworkMessage, LocalMessage

log = logging.getLogger('amusementpark.broker')

class Broker:
    END = 'end'

    def __init__(self):
        self.incoming_messages = Queue()
        self.outgoing_messages = Queue()
    
    def run(self, node):
        thread = Thread(target=self.process_messages, args=(node,))
        thread.start()
        return thread
    
    def process_messages(self, node):
        while True:
            incoming_message = self.incoming_messages.get()

            if incoming_message == Broker.END:
                break
            
            self.log_incoming_message(node, incoming_message)
            
            for outgoing_message in node.process_message(incoming_message):
                self.log_outgoing_message(node, outgoing_message)
                self.outgoing_messages.put(outgoing_message)
    
    def add_incoming_message(self, message):
        self.incoming_messages.put(message)
    
    def get_outgoing_messages(self):
        return self.outgoing_messages
    
    def log_incoming_message(self, node, message):
        if isinstance(message, LocalMessage):
            log.info('Node %s receive local message: %s', node, message)
        elif isinstance(message, NetworkMessage):
            log.info('Node %s receive from %s: %s', node, message.sender.id, message)
    
    def log_outgoing_message(self, node, message):
        if isinstance(message, LocalMessage):
            log.info('Node %s send message: %s', node, message)
        elif isinstance(message, NetworkMessage):
            log.info('Node %s send to %s: %s', node, message.recipient.id, message)
