import logging
import random
from amusementpark.messages import LocalMessage
from amusementpark.visitor_repository import Repository, State
from helpers import create_node_infos, create_gate_nodes

logging.basicConfig(level=logging.INFO)

network_map = {
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

repository = Repository('repository.json')
repository.write_state(State(capacity=3, visitors=[]))

gate_node_infos = create_node_infos(network_map.keys())
gate_nodes = create_gate_nodes(gate_node_infos, network_map, repository)

for _, broker, _ in gate_nodes.values():
    message = LocalMessage('say_hello')
    broker.add_incoming_message(message)