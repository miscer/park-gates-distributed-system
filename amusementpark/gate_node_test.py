from amusementpark.gate_node import GateNode
from amusementpark.messages import NetworkMessage

def test_gate_node_hello():
    node = GateNode(100)
    message = NetworkMessage('hello', 200, 100)
    assert list(node.process_message(message)) == [NetworkMessage('hey', 100, 200)]
