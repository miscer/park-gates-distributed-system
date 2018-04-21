import random
import itertools
from amusementpark.gate_node import GateNode
from amusementpark.visitor_node import VisitorNode
from amusementpark.broker import Broker
from amusementpark.network import Network
from amusementpark.node_info import NodeInfo

def create_node_infos(node_names):
    return {
        name: NodeInfo(id=node_id, address=('localhost', port), capacity=random.randint(1, 10))

        for name, node_id, port in zip(
            node_names,
            random.sample(range(100, 1000), k=len(node_names)),
            range(8001, 9000)
        )
    }

def create_gate_nodes(node_infos, node_neighbours, repository):
    nodes = {}

    for name, info in node_infos.items():
        neighbours = [node_infos[neighbour] for neighbour in node_neighbours[name]]
        _, port = info.address

        gate_node = GateNode(info, neighbours, repository)
        broker = Broker()
        network = Network(port, broker)

        broker.run(gate_node)
        network.run()

        nodes[name] = (gate_node, broker, network)
    
    return nodes

visitor_node_id = 2000
visitor_node_port = 9000

def create_visitor_node():
    global visitor_node_id, visitor_node_port

    node_info = NodeInfo(visitor_node_id, ('localhost', visitor_node_port), 1)
    visitor_node = VisitorNode(node_info)
    broker = Broker()
    network = Network(visitor_node_port, broker)

    broker.run(visitor_node)
    network.run()

    visitor_node_id += 1
    visitor_node_port += 1

    return node_info, visitor_node, broker, network