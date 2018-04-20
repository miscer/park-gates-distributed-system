import socket
from threading import Thread
import pickle

from amusementpark.messages import NetworkMessage
from amusementpark.node_info import NodeInfo

class Network:
    def __init__(self, port, broker):
        self.port = port
        self.broker = broker
    
    def start_server(self):
        server = socket.socket()
        server.bind(('0.0.0.0', self.port))
        server.listen()

        thread = Thread(target=self.accept_connections, args=(server,))
        thread.start()
    
    def accept_connections(self, server):
        while True:
            connection, address = server.accept()
            
            thread = Thread(target=self.receive_messages, args=(connection,))
            thread.start()
    
    def receive_messages(self, connection):
        while True:
            data = connection.recv(4096)
            message = parse_message(data)
            self.broker.add_incoming_message(message)
    
    def connect_to_node(self, node):
        connection = socket.create_connection(node.address)

        thread = Thread(target=self.send_messages, args=(node, connection))
        thread.start()
    
    def send_messages(self, node, connection):
        queue = self.broker.get_outgoing_messages(node)
        
        while True:
            message = queue.get()
            data = serialize_message(message)
            connection.sendall(data)
            queue.task_done()
    
def parse_message(data):
    return pickle.loads(data)

def serialize_message(message):
    assert isinstance(message, NetworkMessage)
    return pickle.dumps(message)
