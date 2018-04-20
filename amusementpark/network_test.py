from amusementpark.network import serialize_message, parse_message
from amusementpark.messages import NetworkMessage
from amusementpark.node_info import NodeInfo

def test_serialize():
    sender = NodeInfo(100, ('localhost', 3001))
    recipient = NodeInfo(200, ('localhost', 3002))
    leader = NodeInfo(300, ('localhost', 3003))
    message = NetworkMessage('test', sender, recipient, leader=leader)

    assert parse_message(serialize_message(message)) == message
