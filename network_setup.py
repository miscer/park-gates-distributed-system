import random
import itertools
from amusementpark.gate_node import GateNode
from amusementpark.broker import Broker
from amusementpark.network import Network
from amusementpark.node_info import NodeInfo

def create_network(node_defs):
    nodes = {
        name: NodeInfo(node_id, ('localhost', port))

        for name, node_id, port in zip(
            node_defs.keys(),
            random.sample(range(100, 1000), k=len(node_defs)),
            range(8001, 9000)
        )
    }

    running = {}

    for name, info in nodes.items():
        neighbours = [nodes[neighbour] for neighbour in node_defs[name]]
        _, port = info.address

        gate_node = GateNode(info, neighbours)
        broker = Broker()
        network = Network(port, broker)

        broker.run(gate_node)
        network.run()

        running[name] = (gate_node, broker, network)
    
    return nodes, running