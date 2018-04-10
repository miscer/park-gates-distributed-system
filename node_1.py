import logging
from amusementpark.gate_node import GateNode
from amusementpark.broker import Broker
from amusementpark.network import Network
from amusementpark.messages import NetworkMessage

logging.basicConfig(level=logging.INFO)

node = GateNode(100)
broker = Broker()
network = Network(8001, broker)

network.start_server()

input('Press enter to continue...')

network.connect_to_node(200, ('localhost', 8002))
broker.run(node)

message = NetworkMessage('hello', 100, 200)
broker.get_outgoing_messages(200).put(message)