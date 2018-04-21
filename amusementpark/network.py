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
            connection.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1) # send all data immediately

            _, port = address
            log.debug('Network %d receive connection from %d' % (self.port, port))
            
            thread = Thread(target=self.receive_messages, args=(connection, address))
            thread.start()
    
    def receive_messages(self, connection, address):
        while True:
            data = receive_data(connection)
            message = parse_message(data)

            _, port = address
            log.debug('Network %d received message from %d: %s' % (self.port, port, message))

            self.broker.add_incoming_message(message)

    def send_messages(self):
        while True:
            message = self.broker.get_outgoing_message()
            
            connection = self.get_connection(message.recipient)
            data = serialize_message(message)
            send_data(connection, data)

            _, port = message.recipient.address
            log.debug('Network %d send message to %d: %s' % (self.port, port, message))
            
            self.broker.finish_outgoing_message()
    
    def get_connection(self, node):
        if node not in self.connections:
            connection = socket.create_connection(node.address, timeout=10)
            connection.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1) # send all data immediately

            self.connections[node] = connection

            _, port = node.address
            log.debug('Network %d connect to %d' % (self.port, port))
        
        return self.connections[node]
    
def parse_message(data):
    return pickle.loads(data)

def serialize_message(message):
    assert isinstance(message, NetworkMessage)
    return pickle.dumps(message)

INT_BYTE_LENGTH = 4

def send_data(connection, data_buffer):
    # first send the size of the data as a 4-byte integer, then send the data
    size_buffer = len(data_buffer).to_bytes(INT_BYTE_LENGTH, byteorder='big')
    connection.sendall(size_buffer + data_buffer)

def receive_data(connection):
    # first read four bytes from the socket
    size_buffer = bytes()

    while len(size_buffer) < INT_BYTE_LENGTH:
        size_buffer += connection.recv(INT_BYTE_LENGTH - len(size_buffer))
    
    # then decode it into an integer specifying the size of the data in bytes
    size = int.from_bytes(size_buffer, byteorder='big')

    # read the specified amount of bytes
    data_buffer = bytes()
    
    while len(data_buffer) < size:
        data_buffer += connection.recv(size - len(data_buffer))
    
    return data_buffer
