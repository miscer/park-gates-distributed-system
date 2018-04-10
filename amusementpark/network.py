import socket
from threading import Thread
import json

from amusementpark.messages import NetworkMessage

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
        connection, address = server.accept()
        
        thread = Thread(target=self.receive_messages, args=(connection,))
        thread.start()
    
    def receive_messages(self, connection):
        while True:
            data = connection.recv(4096)
            message = self.parse_message(data)
            self.broker.add_incoming_message(message)
    
    def connect_to_node(self, node_id, address):
        connection = socket.create_connection(address)

        thread = Thread(target=self.send_messages, args=(node_id, connection))
        thread.start()
    
    def send_messages(self, node_id, connection):
        queue = self.broker.get_outgoing_messages(node_id)
        
        while True:
            message = queue.get()
            data = self.serialize_message(message)
            connection.sendall(data)
            queue.task_done()
    
    def parse_message(self, data):
        parsed = json.loads(data, encoding='utf-8')

        return NetworkMessage(parsed['type'], parsed['sender'], parsed['recipient'], **parsed['payload'])

    def serialize_message(self, message):
        assert isinstance(message, NetworkMessage)

        serialized = {
            'type': message.type,
            'sender': message.sender,
            'recipient': message.recipient,
            'payload': message.payload,
        }

        return bytes(json.dumps(serialized), 'utf-8')
