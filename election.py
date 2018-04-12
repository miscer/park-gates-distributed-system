import logging
import random
import itertools
from amusementpark.gate_node import GateNode
from amusementpark.broker import Broker
from amusementpark.network import Network
from amusementpark.messages import LocalMessage

logging.basicConfig(level=logging.INFO)

nodes = {
    'a': set('bj'),
    'b': set('agc'),
    'c': set('bde'),
    'd': set('cef'),
    'e': set('cdfg'),
    'f': set('dei'),
    'g': set('behj'),
    'h': set('gi'),
    'i': set('fh'),
    'j': set('ag'),
}

node_ids = dict(zip(nodes.keys(), random.sample(range(100, 1000), k=len(nodes))))
node_ports = dict(zip(nodes.keys(), range(7001, 7001 + len(nodes))))

running = {}

for name in nodes.keys():
    node_id = node_ids[name]
    port = node_ports[name]
    neighbours = nodes[name]

    neighbour_ids = [node_ids[neighbour] for neighbour in neighbours]

    node = GateNode(node_id, neighbour_ids)
    broker = Broker()
    network = Network(port, broker)

    network.start_server()

    running[name] = (node, broker, network)

for name in nodes.keys():
    node, broker, network = running[name]
    neighbours = nodes[name]

    for neighbour in neighbours:
        neighbour_id = node_ids[neighbour]
        neighbour_port = node_ports[neighbour]

        network.connect_to_node(neighbour_id, ('localhost', neighbour_port))
    
    broker.run(node)

node, broker, network = random.choice(list(running.values()))
message = LocalMessage('start_election')
broker.add_incoming_message(message)