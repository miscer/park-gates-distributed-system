import socket
from threading import Thread
import pickle

from amusementpark.messages import NetworkMessage
from amusementpark.node_info import NodeInfo

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

        while True:
            connection, address = server.accept()
            
            thread = Thread(target=self.receive_messages, args=(connection,))
            thread.start()
    
    def receive_messages(self, connection):
        while True:
            data = connection.recv(4096)
            message = parse_message(data)
            self.broker.add_incoming_message(message)

    def send_messages(self):
        while True:
            message = self.broker.get_outgoing_message()
            
            connection = self.get_connection(message.recipient)
            data = serialize_message(message)
            connection.sendall(data)
            
            self.broker.finish_outgoing_message()
    
    def get_connection(self, node):
        if node not in self.connections:
            self.connections[node] = socket.create_connection(node.address, timeout=10)
        
        return self.connections[node]
    
def parse_message(data):
    return pickle.loads(data)

def serialize_message(message):
    assert isinstance(message, NetworkMessage)
    return pickle.dumps(message)
