from unittest.mock import Mock
from amusementpark.broker import Broker

def test_passing_messages():
    in_message_1 = Mock()
    in_message_2 = Mock()

    out_message_1 = Mock()
    out_message_1.recipient = 100
    out_message_2 = Mock()
    out_message_2.recipient = 200
    out_message_3 = Mock()
    out_message_3.recipient = 300
    
    node = Mock()
    node.process_message.side_effect = [
        [out_message_1, out_message_2],
        [out_message_3]
    ]

    broker = Broker()
    broker.add_incoming_message(in_message_1)
    broker.add_incoming_message(in_message_2)
    broker.add_incoming_message(Broker.END)

    thread = broker.run(node)
    thread.join()

    assert broker.get_outgoing_messages(100).get(block=False) == out_message_1
    assert broker.get_outgoing_messages(200).get(block=False) == out_message_2
    assert broker.get_outgoing_messages(300).get(block=False) == out_message_3
