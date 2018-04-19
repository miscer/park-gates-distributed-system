from amusementpark.visitor_node import VisitorNode
from amusementpark.messages import NetworkMessage, LocalMessage

def test_enter_allowed():
    node = VisitorNode(100, 200)

    assert list(node.process_message(LocalMessage('enter_park'))) == \
        [NetworkMessage('enter_request', 100, 200)]
    assert node.state == VisitorNode.STATE_ENTERING

    assert not list(node.process_message(NetworkMessage('enter_response', 200, 100, allowed=True)))
    assert node.state == VisitorNode.STATE_ENTERED

def test_enter_refused():
    node = VisitorNode(100, 200)

    assert list(node.process_message(LocalMessage('enter_park'))) == \
        [NetworkMessage('enter_request', 100, 200)]
    assert node.state == VisitorNode.STATE_ENTERING

    assert not list(node.process_message(NetworkMessage('enter_response', 200, 100, allowed=False)))
    assert node.state == VisitorNode.STATE_IDLE

def test_leave_allowed():
    node = VisitorNode(100, 200)
    node.state = VisitorNode.STATE_ENTERED

    assert list(node.process_message(LocalMessage('leave_park'))) == \
        [NetworkMessage('leave_request', 100, 200)]
    assert node.state == VisitorNode.STATE_LEAVING

    assert not list(node.process_message(NetworkMessage('leave_response', 200, 100, allowed=True)))
    assert node.state == VisitorNode.STATE_IDLE

def test_leave_rejected():
    node = VisitorNode(100, 200)
    node.state = VisitorNode.STATE_ENTERED

    assert list(node.process_message(LocalMessage('leave_park'))) == \
        [NetworkMessage('leave_request', 100, 200)]
    assert node.state == VisitorNode.STATE_LEAVING

    assert not list(node.process_message(NetworkMessage('leave_response', 200, 100, allowed=False)))
    assert node.state == VisitorNode.STATE_ENTERED