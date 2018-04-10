from amusementpark.gate_node import GateNode
from amusementpark.messages import NetworkMessage, LocalMessage

def test_gate_node_hello():
    node = GateNode(100, [200, 300])

    assert list(node.process_message(LocalMessage('say_hello'))) == \
        [NetworkMessage('hello', 100, 200), NetworkMessage('hello', 100, 300)]
    
    assert list(node.process_message(NetworkMessage('hello', 200, 100))) == \
        [NetworkMessage('hey', 100, 200)]
