import pytest
from amusementpark.gate_node import GateNode
from amusementpark.messages import NetworkMessage, LocalMessage
from amusementpark.node_info import NodeInfo
from amusementpark.visitor_repository import Repository, State

nodes = [
    NodeInfo(100, 1, 4),
    NodeInfo(200, 2, 2),
    NodeInfo(300, 3, 6),
    NodeInfo(400, 4, 3),
    NodeInfo(800, 8, 5),
    NodeInfo(900, 9, 9),
]

@pytest.fixture
def visitor_repository(tmpdir):
    filename = tmpdir.join('repository.json')
    return Repository(filename)

def test_hello(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2]], visitor_repository)

    assert list(node.process_message(LocalMessage('say_hello'))) == \
        [NetworkMessage('hello', nodes[0], nodes[1]), NetworkMessage('hello', nodes[0], nodes[2])]
    
    assert list(node.process_message(NetworkMessage('hello', nodes[1], nodes[0]))) == \
        [NetworkMessage('hey', nodes[0], nodes[1])]

def test_start_election(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2]], visitor_repository)

    assert list(node.process_message(LocalMessage('start_election'))) == \
        [NetworkMessage('election_started', nodes[0], nodes[1]), NetworkMessage('election_started', nodes[0], nodes[2])]
    
    assert node.state == GateNode.STATE_INITIATED

def test_first_election_message(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2], nodes[3]], visitor_repository)

    assert list(node.process_message(NetworkMessage('election_started', nodes[1], nodes[0]))) == \
        [NetworkMessage('election_started', nodes[0], nodes[2]), NetworkMessage('election_started', nodes[0], nodes[3])]
    
    assert node.state == GateNode.STATE_ELECTING
    assert node.parent == nodes[1]

def test_another_election_message(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2], nodes[3]], visitor_repository)
    node.state = GateNode.STATE_ELECTING
    node.parent = nodes[1]

    assert list(node.process_message(NetworkMessage('election_started', nodes[2], nodes[0]))) == \
        [NetworkMessage('election_voted', nodes[0], nodes[2], leader=None)]
    
    assert node.state == GateNode.STATE_ELECTING
    assert node.parent == nodes[1]

def test_election_start_without_children(visitor_repository):
    node = GateNode(nodes[0], [nodes[1]], visitor_repository)

    assert list(node.process_message(NetworkMessage('election_started', nodes[1], nodes[0]))) == \
        [NetworkMessage('election_voted', nodes[0], nodes[1], leader=nodes[0])]
    
    assert node.state == GateNode.STATE_WAITING
    assert node.parent == nodes[1]

def test_first_ack(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2], nodes[3]], visitor_repository)
    node.state = GateNode.STATE_INITIATED
    
    assert list(node.process_message(NetworkMessage('election_voted', nodes[1], nodes[0], leader=nodes[5]))) == []
    
    assert node.state == GateNode.STATE_INITIATED
    assert node.answers == {nodes[1]: nodes[5]}

def test_last_ack_intermediate_node(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2], nodes[3]], visitor_repository)
    node.state = GateNode.STATE_ELECTING
    node.parent = nodes[1]
    node.answers = {nodes[2]: nodes[5]}
    
    assert list(node.process_message(NetworkMessage('election_voted', nodes[3], nodes[0], leader=nodes[4]))) == \
        [NetworkMessage('election_voted', nodes[0], nodes[1], leader=nodes[5])]
    
    assert node.state == GateNode.STATE_WAITING
    assert node.answers == {nodes[2]: nodes[5], nodes[3]: nodes[4]}

def test_last_ack_starting_node(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2]], visitor_repository)
    node.state = GateNode.STATE_INITIATED
    node.answers = {nodes[1]: nodes[4]}
    
    assert list(node.process_message(NetworkMessage('election_voted', nodes[2], nodes[0], leader=nodes[5]))) == \
        [NetworkMessage('election_finished', nodes[0], nodes[1], leader=nodes[5]), NetworkMessage('election_finished', nodes[0], nodes[2], leader=nodes[5])]
    
    assert node.state == GateNode.STATE_IDLE
    assert node.leader == nodes[5]

def test_finishing_election(visitor_repository):
    node = GateNode(nodes[0], [nodes[1], nodes[2], nodes[3]], visitor_repository)
    node.state = GateNode.STATE_WAITING

    assert list(node.process_message(NetworkMessage('election_finished', nodes[1], nodes[0], leader=nodes[5]))) == \
        [NetworkMessage('election_finished', nodes[0], nodes[2], leader=nodes[5]), NetworkMessage('election_finished', nodes[0], nodes[3], leader=nodes[5])]
    
    assert node.state == GateNode.STATE_IDLE
    assert node.leader == nodes[5]

def test_request_mutex(visitor_repository):
    node = GateNode(nodes[0], [], visitor_repository)
    node.leader = nodes[0]

    assert list(node.process_message(NetworkMessage('mutex_requested', nodes[1], nodes[0]))) == \
        [NetworkMessage('mutex_granted', nodes[0], nodes[1])]
    assert node.mutex_holder == nodes[1]
    assert not node.mutex_queue

    assert list(node.process_message(NetworkMessage('mutex_requested', nodes[2], nodes[0]))) == []
    assert node.mutex_queue == [nodes[2]]

    assert list(node.process_message(NetworkMessage('mutex_requested', nodes[3], nodes[0]))) == []
    assert node.mutex_queue == [nodes[2], nodes[3]]

    assert list(node.process_message(NetworkMessage('mutex_released', nodes[1], nodes[0]))) == \
        [NetworkMessage('mutex_granted', nodes[0], nodes[2])]
    assert node.mutex_holder == nodes[2]
    assert node.mutex_queue == [nodes[3]]

    assert list(node.process_message(NetworkMessage('mutex_released', nodes[2], nodes[0]))) == \
        [NetworkMessage('mutex_granted', nodes[0], nodes[3])]
    assert node.mutex_holder == nodes[3]
    assert node.mutex_queue == []

    assert list(node.process_message(NetworkMessage('mutex_released', nodes[3], nodes[0]))) == []
    assert node.mutex_holder is None
    assert node.mutex_queue == []

def test_enter_request(visitor_repository):
    visitor_repository.write_state(State(capacity=1, visitors=[]))

    node = GateNode(nodes[0], [], visitor_repository)
    node.leader = nodes[5]

    assert list(node.process_message(NetworkMessage('enter_request', nodes[1], nodes[0]))) == \
        [NetworkMessage('mutex_requested', nodes[0], nodes[5])]
    assert node.enter_queue == [nodes[1]]

    assert list(node.process_message(NetworkMessage('enter_request', nodes[2], nodes[0]))) == []
    assert node.enter_queue == [nodes[1], nodes[2]]

    assert list(node.process_message(NetworkMessage('mutex_granted', nodes[5], nodes[0]))) == \
        [NetworkMessage('enter_response', nodes[0], nodes[1], allowed=True),
            NetworkMessage('enter_response', nodes[0], nodes[2], allowed=False),
            NetworkMessage('mutex_released', nodes[0], nodes[5])]
    assert node.enter_queue == []

    assert list(node.process_message(NetworkMessage('enter_request', nodes[3], nodes[0]))) == \
        [NetworkMessage('mutex_requested', nodes[0], nodes[5])]
    assert node.enter_queue == [nodes[3]]

def test_leave_request(visitor_repository):
    visitor_repository.write_state(State(capacity=1, visitors=[nodes[1].id]))

    node = GateNode(nodes[0], [], visitor_repository)
    node.leader = nodes[5]

    assert list(node.process_message(NetworkMessage('leave_request', nodes[1], nodes[0]))) == \
        [NetworkMessage('mutex_requested', nodes[0], nodes[5])]
    assert node.leave_queue == [nodes[1]]

    assert list(node.process_message(NetworkMessage('leave_request', nodes[2], nodes[0]))) == []
    assert node.leave_queue == [nodes[1], nodes[2]]

    assert list(node.process_message(NetworkMessage('mutex_granted', nodes[5], nodes[0]))) == \
        [NetworkMessage('leave_response', nodes[0], nodes[1], allowed=True),
            NetworkMessage('leave_response', nodes[0], nodes[2], allowed=False),
            NetworkMessage('mutex_released', nodes[0], nodes[5])]
    assert node.leave_queue == []

    assert list(node.process_message(NetworkMessage('leave_request', nodes[3], nodes[0]))) == \
        [NetworkMessage('mutex_requested', nodes[0], nodes[5])]
    assert node.leave_queue == [nodes[3]]

def test_terminate():
    node = GateNode(nodes[0], [nodes[1], nodes[2]], visitor_repository)

    assert list(node.process_message(LocalMessage('terminate'))) == \
        [NetworkMessage('terminated', nodes[0], nodes[1]),
            NetworkMessage('terminated', nodes[0], nodes[2]),
            None]

def test_terminated():
    node = GateNode(nodes[0], [nodes[1], nodes[2]], visitor_repository)

    assert list(node.process_message(NetworkMessage('terminated', nodes[1], nodes[0]))) == []
    assert node.neighbours == [nodes[2]]

def test_remove_leader():
    node = GateNode(nodes[0], [nodes[1], nodes[2]], visitor_repository)
    node.leader = nodes[0]

    assert list(node.process_message(LocalMessage('remove_leader'))) == \
        [NetworkMessage('leader_removed', nodes[0], nodes[1]),
            NetworkMessage('leader_removed', nodes[0], nodes[2])]
    assert node.leader is None

def test_leader_removed():
    node = GateNode(nodes[0], [nodes[1], nodes[2]], visitor_repository)
    node.leader = nodes[5]

    assert list(node.process_message(NetworkMessage('leader_removed', nodes[1], nodes[0]))) == \
        [NetworkMessage('leader_removed', nodes[0], nodes[2])]
    assert node.leader is None