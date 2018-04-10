import logging
from amusementpark.gate_node import GateNode
from amusementpark.broker import Broker
from amusementpark.network import Network
from amusementpark.messages import NetworkMessage

logging.basicConfig(level=logging.INFO)

node = GateNode(200)
broker = Broker()
network = Network(8002, broker)

network.start_server()

input('Press enter to continue...')

network.connect_to_node(100, ('localhost', 8001))
broker.run(node)
