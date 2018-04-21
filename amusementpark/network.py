import socket
from threading import Thread
import pickle
import logging

from amusementpark.messages import NetworkMessage
from amusementpark.node_info import NodeInfo

log = logging.getLogger('amusementpark.network')

class Network:
    def __init__(self, port, broker):
        self.port = port
        self.broker = broker
        self.connections = {}

    def run(self):
        Thread(target=self.start_server).start()
        Thread(target=self.send_messages).start()
    
    def start_server(self):
        server = socket.socket()
        server.bind(('0.0.0.0', self.port))
        server.listen()

        log.debug('Network %d start server' % self.port)

        while True:
            connection, address = server.accept()

            _, port = address
            log.debug('Network %d receive connection from %d' % (self.port, port))
            
            thread = Thread(target=self.receive_messages, args=(connection, address))
            thread.start()
    
    def receive_messages(self, connection, address):
        while True:
            data = connection.recv(4096)
            message = parse_message(data)

            _, port = address
            log.debug('Network %d received message from %d: %s' % (self.port, port, message))

            self.broker.add_incoming_message(message)

    def send_messages(self):
        while True:
            message = self.broker.get_outgoing_message()
            
            connection = self.get_connection(message.recipient)
            data = serialize_message(message)
            connection.sendall(data)

            _, port = message.recipient.address
            log.debug('Network %d send message to %d: %s' % (self.port, port, message))
            
            self.broker.finish_outgoing_message()
    
    def get_connection(self, node):
        if node not in self.connections:
            self.connections[node] = socket.create_connection(node.address, timeout=10)

            _, port = node.address
            log.debug('Network %d connect to %d' % (self.port, port))
        
        return self.connections[node]
    
def parse_message(data):
    return pickle.loads(data)

def serialize_message(message):
    assert isinstance(message, NetworkMessage)
    return pickle.dumps(message)
