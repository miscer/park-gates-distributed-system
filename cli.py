import logging
import random
import readline
import code

from amusementpark.visitor_repository import Repository, State
from amusementpark.messages import LocalMessage
from helpers import create_node_infos, create_gate_nodes, create_visitor_node

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

def random_gate():
    return random.choice(list(network_map.keys()))

def start_election(gate_name):
    _, broker, _ = gate_nodes[gate_name]

    message = LocalMessage('start_election')
    broker.add_incoming_message(message)

def terminate_gate(gate_name):
    _, broker, _ = gate_nodes[gate_name]

    message = LocalMessage('terminate')
    broker.add_incoming_message(message)

def create_visitor():
    return create_visitor_node()

def enter_park(visitor):
    _, _, broker, _ = visitor
    gate_name = random_gate()
    gate_info = gate_node_infos[gate_name]

    message = LocalMessage('enter_park', gate=gate_info)
    broker.add_incoming_message(message)

def leave_park(visitor):
    _, _, broker, _ = visitor
    gate_name = random_gate()
    gate_info = gate_node_infos[gate_name]

    message = LocalMessage('leave_park', gate=gate_info)
    broker.add_incoming_message(message)

code.interact(local=locals())
