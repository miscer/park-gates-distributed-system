from unittest.mock import Mock
from amusementpark.broker import Broker
from amusementpark.messages import NetworkMessage, LocalMessage
from amusementpark.node_info import NodeInfo

nodes = [
    NodeInfo(100, 1),
    NodeInfo(200, 2),
    NodeInfo(300, 3),
]

def test_passing_messages():
    in_message_1 = Mock(NetworkMessage)
    in_message_1.sender = nodes[0]
    in_message_2 = Mock(LocalMessage)

    out_message_1 = Mock()
    out_message_1.recipient = nodes[0]
    out_message_2 = Mock()
    out_message_2.recipient = nodes[1]
    out_message_3 = Mock()
    out_message_3.recipient = nodes[2]
    
    node = Mock()
    node.process_message.side_effect = [
        [out_message_1, out_message_2],
        [out_message_3],
    ]

    broker = Broker()
    broker.add_incoming_message(in_message_1)
    broker.add_incoming_message(in_message_2)
    broker.add_incoming_message(Broker.END)

    thread = broker.run(node)
    thread.join()

    outgoing_messages = broker.get_outgoing_messages()
    assert outgoing_messages.get(block=False) == out_message_1
    assert outgoing_messages.get(block=False) == out_message_2
    assert outgoing_messages.get(block=False) == out_message_3
