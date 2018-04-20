import logging
import random
from amusementpark.messages import LocalMessage
from network_setup import create_network

logging.basicConfig(level=logging.INFO)

nodes, running = create_network({
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
})

_, broker, _ = random.choice(list(running.values()))
message = LocalMessage('start_election')
broker.add_incoming_message(message)