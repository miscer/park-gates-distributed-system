from amusementpark.visitor_node import VisitorNode
from amusementpark.messages import NetworkMessage, LocalMessage
from amusementpark.node_info import NodeInfo

nodes = [
    NodeInfo(100, 1, 4),
    NodeInfo(200, 2, 8),
]

def test_enter_allowed():
    node = VisitorNode(nodes[0])

    assert list(node.process_message(LocalMessage('enter_park', gate=nodes[1]))) == \
        [NetworkMessage('enter_request', nodes[0], nodes[1])]
    assert node.state == VisitorNode.STATE_ENTERING

    assert not list(node.process_message(NetworkMessage('enter_response', nodes[1], nodes[0], allowed=True)))
    assert node.state == VisitorNode.STATE_ENTERED

def test_enter_refused():
    node = VisitorNode(nodes[0])

    assert list(node.process_message(LocalMessage('enter_park', gate=nodes[1]))) == \
        [NetworkMessage('enter_request', nodes[0], nodes[1])]
    assert node.state == VisitorNode.STATE_ENTERING

    assert not list(node.process_message(NetworkMessage('enter_response', nodes[1], nodes[0], allowed=False)))
    assert node.state == VisitorNode.STATE_IDLE

def test_leave_allowed():
    node = VisitorNode(nodes[0])
    node.state = VisitorNode.STATE_ENTERED

    assert list(node.process_message(LocalMessage('leave_park', gate=nodes[1]))) == \
        [NetworkMessage('leave_request', nodes[0], nodes[1])]
    assert node.state == VisitorNode.STATE_LEAVING

    assert not list(node.process_message(NetworkMessage('leave_response', nodes[1], nodes[0], allowed=True)))
    assert node.state == VisitorNode.STATE_IDLE

def test_leave_rejected():
    node = VisitorNode(nodes[0])
    node.state = VisitorNode.STATE_ENTERED

    assert list(node.process_message(LocalMessage('leave_park', gate=nodes[1]))) == \
        [NetworkMessage('leave_request', nodes[0], nodes[1])]
    assert node.state == VisitorNode.STATE_LEAVING

    assert not list(node.process_message(NetworkMessage('leave_response', nodes[1], nodes[0], allowed=False)))
    assert node.state == VisitorNode.STATE_ENTERED