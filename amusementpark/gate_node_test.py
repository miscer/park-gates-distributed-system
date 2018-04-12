from amusementpark.gate_node import GateNode
from amusementpark.messages import NetworkMessage, LocalMessage

def test_hello():
    node = GateNode(100, [200, 300])

    assert list(node.process_message(LocalMessage('say_hello'))) == \
        [NetworkMessage('hello', 100, 200), NetworkMessage('hello', 100, 300)]
    
    assert list(node.process_message(NetworkMessage('hello', 200, 100))) == \
        [NetworkMessage('hey', 100, 200)]

def test_start_election():
    node = GateNode(100, [200, 300])

    assert list(node.process_message(LocalMessage('start_election'))) == \
        [NetworkMessage('election', 100, 200), NetworkMessage('election', 100, 300)]
    
    assert node.state == GateNode.STATE_INITIATED

def test_first_election_message():
    node = GateNode(100, [200, 300, 400])

    assert list(node.process_message(NetworkMessage('election', 200, 100))) == \
        [NetworkMessage('election', 100, 300), NetworkMessage('election', 100, 400)]
    
    assert node.state == GateNode.STATE_ELECTING
    assert node.parent_id == 200

def test_another_election_message():
    node = GateNode(100, [200, 300, 400])
    node.state = GateNode.STATE_ELECTING
    node.parent_id = 200

    assert list(node.process_message(NetworkMessage('election', 300, 100))) == \
        [NetworkMessage('ack', 100, 300, leader=None)]
    
    assert node.state == GateNode.STATE_ELECTING
    assert node.parent_id == 200

def test_first_ack():
    node = GateNode(100, [200, 300, 400])
    node.state = GateNode.STATE_INITIATED
    
    assert list(node.process_message(NetworkMessage('ack', 200, 100, leader=900))) == []
    
    assert node.state == GateNode.STATE_INITIATED
    assert node.answers == {200: 900}

def test_last_ack_intermediate_node():
    node = GateNode(100, [200, 300, 400])
    node.state = GateNode.STATE_ELECTING
    node.parent_id = 200
    node.answers = {300: 900}
    
    assert list(node.process_message(NetworkMessage('ack', 400, 100, leader=800))) == \
        [NetworkMessage('ack', 100, 200, leader=900)]
    
    assert node.state == GateNode.STATE_WAITING
    assert node.answers == {300: 900, 400: 800}

def test_last_ack_starting_node():
    node = GateNode(100, [200, 300])
    node.state = GateNode.STATE_INITIATED
    node.answers = {200: 700}
    
    assert list(node.process_message(NetworkMessage('ack', 300, 100, leader=900))) == \
        [NetworkMessage('leader', 100, 200, leader=900), NetworkMessage('leader', 100, 300, leader=900)]
    
    assert node.state == GateNode.STATE_IDLE

def test_leader():
    node = GateNode(100, [200, 300, 400])
    node.state = GateNode.STATE_WAITING

    assert list(node.process_message(NetworkMessage('leader', 200, 100, leader=900))) == \
        [NetworkMessage('leader', 100, 300, leader=900), NetworkMessage('leader', 100, 400, leader=900)]
    
    assert node.state == GateNode.STATE_IDLE