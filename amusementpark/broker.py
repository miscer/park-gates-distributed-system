from queue import PriorityQueue
from threading import Thread
from collections import defaultdict
import time
import logging

from amusementpark.messages import NetworkMessage, LocalMessage

log = logging.getLogger('amusementpark.broker')

class Broker:
    def __init__(self, node):
        self.node = node
        self.incoming_messages = PriorityQueue()
        self.outgoing_messages = PriorityQueue()
    
    def run(self):
        thread = Thread(target=self.process_messages)
        thread.start()
        return thread
    
    def process_messages(self):
        while True:
            _, incoming_message = self.incoming_messages.get()
            
            self.log_incoming_message(incoming_message)
            
            for outgoing_message in self.node.process_message(incoming_message):
                if outgoing_message is not None:
                    self.log_outgoing_message(outgoing_message)
                    self.outgoing_messages.put((time.time(), outgoing_message))
                else:
                    self.log_end()
                    return
    
    def add_incoming_message(self, message):
        self.incoming_messages.put((time.time(), message))
    
    def get_outgoing_message(self, block=True):
        _, message = self.outgoing_messages.get(block=block)
        return message
    
    def finish_outgoing_message(self):
        self.outgoing_messages.task_done()
    
    def log_incoming_message(self, message):
        if isinstance(message, LocalMessage):
            log.info('Node %s receive local message: %s', self.node, message)
        elif isinstance(message, NetworkMessage):
            log.info('Node %s receive from %s: %s', self.node, message.sender.id, message)
    
    def log_outgoing_message(self, message):
        if isinstance(message, LocalMessage):
            log.info('Node %s send message: %s', self.node, message)
        elif isinstance(message, NetworkMessage):
            log.info('Node %s send to %s: %s', self.node, message.recipient.id, message)
    
    def log_end(self):
        log.info('Node %s stop processing messages', self.node)
