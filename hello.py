import logging
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

for _, broker, _ in running.values():
    message = LocalMessage('say_hello')
    broker.add_incoming_message(message)