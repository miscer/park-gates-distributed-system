---
title: CS4103 Practical 2
date: 23 April 2018
author: 140015533
toc: true
geometry: margin=1in
---

# Introduction

In this practical I implement a simple distributed system for controlling entrance and exit gates in an amusement park. The nodes in the system are connected wirelessly. One node is elected as the leader using a distributed election algorithm. The leader node controls access to a shared resource used by all nodes to keep track of visitors in the park.

In my implementation, there are two types of nodes: gates and visitors. Gates control access to the park and one of the gates may be the leader. Gate nodes form a network as described in the practical specification. Visitor nodes connect to the gate nodes and request permission to enter or exit the park.

I completed all three parts of the specification: the gate nodes in the system form a network and communicate over TCP sockets. The user can manually instruct any gate node to start an election using the wireless algorithm. Once the leader is elected, visitor nodes can connect to gate nodes to request entry or exit from the park. Gate node obtains a permission from the leader to access and modify a shared file and informs the visitor node whether the entry or exit is allowed.

The system is implemented in Python. I used only the Python standard library for the implementation and the pytest library for unit tests.

# Design and Implementation

I designed the system so that the functionality is separated and each component can be easily tested.

## Messages

First, all communication in the system is done through messages. There are two types of messages:

* Local messages are manually sent by the user directly to a node. These are for instructing the system to perform some action

* Network messages are sent between the nodes in the system over the network.

Each message has a type and can carry a payload, which is a dictionary with arbitrary keys and values. Network messages also include the sender and the receiver node identification.

## Node Info

To identify nodes, I defined the `NodeInfo` data type. It contains

* the node ID

* the IP address and port of the node

* and the capacity

This data type is used throughout the system to identify nodes. It is included in the messages as well -- this is useful, for example, when the leader is elected, and its address and port needs to be broadcast to all nodes.

## Nodes

Gate and visitor nodes are implemented as simple classes that must have a single method, `process_message`. This method takes a message as its only parameter, and can produce any number of messages, or none. The method must be a Python generator, i.e. use the `yield` keyword to generate messages, instead of returning them. I decided to use generators as they are easy to implement and test.

In addition to the `process_message` method, each node class has other attributes that control its behaviour. The idea is that the `process_message` method will return the same result for a specific combination of the attribute values and the message parameter. This makes the system predictable and easy to test, as the values of the attributes can be modified to simulate a specific state of the system.

## Visitor Repository

The shared resource in the system is implemented as a single file that all nodes can access. The file contains a JSON document with two values:

* The capacity (maximum number of visitors) as an integer

* The list of IDs of all visitors who are currently in the park

The number of visitors is not stored, as it can be obtained simply by counting the values in the visitor ID list.

Contents of this file and the system state are represented by the `State` class, which has two methods, `enter` and `leave`. These check pre-conditions for entering and leaving the park and update the visitor list accordingly.

The access to the file is implemented through the `Repository` class, which has methods for reading, writing and destroying the state. It implements accessing the file and serialising and parsing the state.

## Network and Message Broker

Since the node classes are able to only process messages by producing new messages, some way of delivering the messages to the node classes is needed. This is the role of the `Broker` class, which has two queues -- one for incoming messages, and one for outgoing messages. Messages directed to the node are added to the incoming message queue. The broker starts a thread that monitors this queue and when a message is added, it passes it to the `process_message` method of the node class. Messages yielded by this method are then added to the outgoing message queue, which can be monitored by some other thread. The broker also logs received and sent messages.

By having a broker class, the exact implementation of the communication between nodes is independent from the behaviour of the nodes. This practical implements the communication through TCP sockets in the `Network` class. The role of this class is to

* start a server and listen for connections,

* for each connection, receive messages and add them to the incoming message queue in the broker,

* and monitor the outgoing message queue in the broker, create connections to other nodes and send the messages.

The messages are encoded and decoded using the `pickle` module, which can encode any Python object using binary encoding. I tried using JSON for encoding, but there were issues with encoding and decoding custom data types, such as `NodeInfo`. Additionally, when sending a message through a socket, it is prefixed with its size encoded as a 4-byte integer. This is needed for the receiver to know how many bytes it needs to read from the socket. Without this, I encountered issues where from two consecutive received messages only the first one was decoded correctly.

There are two sockets between nodes -- one for each direction of communication. A new thread is started for the server, for each incoming connection, and for sending messages.

## Election Algorithm

The system uses the wireless algorithm as it was described in the lectures. Each node knows the IDs and addresses of its neighbouring nodes.

Election starts with the user instructing one of the gate nodes to send out the `election_started` message to its neighbours. When a node receives the `election_started` message, it sends it to its neighbours, except for the node from which it received the message. If it receives another `election_started` message, it responds with an empty `election_voted` message. Each node waits for its neighbours to send back an `election_voted` message, which can contain the `NodeInfo` of the potential leader. The node then selects the best candidate for the leader based on their capacity and sends another `election_voted` message to its parent node. When the node which started the election receives responses from all its neighbours, it selects the leader and sends out the `election_finished` message to the neighbours. These forward the messages to more nodes, eventually flooding the whole network. At this point the election is finished and each node knows the ID and the address of the leader.

A leader node can be removed as the leader of the network. This is done manually by the user. `leader_removed` messages are sent throughout the network and each node removes the leader's info. The network is then in the same state as before the election was started.

Election can be started multiple times, but there is no support for concurrent elections. Election can be started even if there is a leader -- this simply elects the same leader.

Node that is not a leader can leave the network by sending the `terminated` message to its neighbours, who simply remove it from the list of their neighbours.

## Mutual Exclusion

The leader node manages access to a shared resource using a simple mutex. The mutex can be obtained by any node by sending the `mutex_requested` message to the leader node. If the mutex is not currently held by any node, the leader sends back a `mutex_granted` message. If it is held, it adds the requesting node to a FIFO queue. Once the first node releases the mutex with a `mutex_released` message, the next node in the queue is granted the mutex.

## Entering and Leaving

Using the mutual exclusion algorithm we can control access to the visitor repository -- the shared resource. A visitor node sends an `enter_request` message to any gate node. The gate node then proceeds to request the mutex, if it has not already, and adds the visitor node to a queue. Similarly, to leave, the visitor node sends a `leave_request` message and the gate node adds it to a queue.

Once the mutex is granted to the gate node, it reads the state from the repository and goes through the nodes in the enter and leave queues. For each node, it modifies the state and sends a `enter_response` or `leave_response` message to the visitor node. This message contains a boolean value which tells the visitor node whether the entry or exit was allowed. Finally, the gate node writes the updated state and releases the mutex.

This way the visitors requesting entry or exit through a gate node are queued until the mutex is granted to the gate node.

When the leader node is used by a visitor node to request entry or exit, the leader node acts as any other gate node -- it connects to the leader, which in this case is the same node.

# Examples

All examples here use the command line interface I built to manually control the system. This is implemented in the `cli.py` script. It sets up a network of 10 nodes as shown in the practical specification and lets the user control it by typing commands. Node IDs and capacities are assigned randomly.

## Starting an Election

Random gate is used to start the election. The nodes vote and eventually a leader is elected.

```
>>> start_election(random_gate())
Node 456/idle receive local message: start_election {}
Node 456/initiated send to 807: election_started {}
Node 456/initiated send to 156: election_started {}
Node 456/initiated send to 986: election_started {}
...
Node 694/electing receive from 166: election_started {}
Node 220/electing receive from 696: election_voted {'leader': None}
Node 694/electing send to 166: election_voted {'leader': None}
Node 694/electing receive from 166: election_voted {'leader': None}
Node 220/waiting send to 166: election_voted
  {'leader': NodeInfo(id=220, address=('localhost', 60509), capacity=7)}
...
Node 696/idle receive from 742: election_finished
  {'leader': NodeInfo(id=156, address=('localhost', 60504), capacity=9)}
Node 742/idle receive from 696: election_finished
  {'leader': NodeInfo(id=156, address=('localhost', 60504), capacity=9)}
```

## Removing a Leader

Once the leader is elected, it can be instructed to remove itself as the leader.

```
>>> remove_leader('e')
Node 156/idle receive local message: remove_leader {}
Node 156/idle send to 456: leader_removed {}
Node 156/idle send to 807: leader_removed {}
Node 156/idle send to 897: leader_removed {}
Node 156/idle send to 166: leader_removed {}
...
Node 696/idle send to 742: leader_removed {}
Node 696/idle receive from 742: leader_removed {}
Node 742/idle receive from 696: leader_removed {}
```

## Terminating a Node

Node that is not a leader can be terminated.

```
>>> terminate_gate('a')
Node 696/idle receive local message: terminate {}
Node 696/idle send to 220: terminated {}
Node 696/idle send to 742: terminated {}
Node 696/idle stop processing messages
Node 220/idle receive from 696: terminated {}
Node 742/idle receive from 696: terminated {}
```

## Entering the Park

Visitor node is created and instructed to connect to a random gate and send an enter request. The gate requests a mutex from the leader, updates the state (shown below), allows the visitor to enter and releases the mutex.

```
>>> visitor = create_visitor()
>>> enter_park(visitor)
Node 2000/idle receive local message: enter_park
  {'gate': NodeInfo(id=694, address=('localhost', 60507), capacity=4)}
Node 2000/idle send to 694: enter_request {}
Node 694/idle receive from 2000: enter_request {}
Node 694/idle send to 156: mutex_requested {}
Node 156/idle receive from 694: mutex_requested {}
Node 156/idle send to 694: mutex_granted {}
Node 694/idle receive from 156: mutex_granted {}
Node 694/idle send to 2000: enter_response {'allowed': True}
Node 694/idle send to 156: mutex_released {}
Node 2000/entering receive from 694: enter_response {'allowed': True}
Node 156/idle receive from 694: mutex_released {}
```

```json
{"capacity": 3, "visitors": [2000]}
```

## Leaving the Park

Leaving the park works similarly to entering the park.

```
>>> leave_park(visitor)
Node 2000/entered receive local message: leave_park
  {'gate': NodeInfo(id=220, address=('localhost', 60509), capacity=7)}
Node 2000/entered send to 220: leave_request {}
Node 220/idle receive from 2000: leave_request {}
Node 220/idle send to 156: mutex_requested {}
Node 156/idle receive from 220: mutex_requested {}
Node 156/idle send to 220: mutex_granted {}
Node 220/idle receive from 156: mutex_granted {}
Node 220/idle send to 2000: leave_response {'allowed': True}
Node 2000/leaving receive from 220: leave_response {'allowed': True}
Node 220/idle send to 156: mutex_released {}
Node 156/idle receive from 220: mutex_released {}
```

## Stress Test

Since we can use any Python code in the command line interface, we can instruct the system to create any number of visitors and have them all try to enter the park at the same time.

```
>>> repository.write_state(State(capacity=30, visitors=[]))
>>> visitors = [create_visitor() for _ in range(20)]
>>> for visitor in visitors:
...     enter_park(visitor)
INFO:amusementpark.broker:Node 2000/idle receive local message: enter_park
  {'gate': NodeInfo(id=615, address=('localhost', 49924), capacity=2)}
INFO:amusementpark.broker:Node 2000/idle send to 615: enter_request {}
...
INFO:amusementpark.broker:Node 908/idle send to 294: mutex_granted {}
INFO:amusementpark.broker:Node 294/idle receive from 908: mutex_granted {}
INFO:amusementpark.broker:Node 294/idle send to 2007: enter_response
  {'allowed': True}
INFO:amusementpark.broker:Node 294/idle send to 2002: enter_response
  {'allowed': True}
INFO:amusementpark.broker:Node 294/idle send to 908: mutex_released {}
...
```

When we check the state stored in the file, we can see that it correctly recorded all 20 visitors.

```json
{"capacity": 20, "visitors": [2001, 2007, ..., 2019]}
```

# Testing

My implementation is thoroughly tested with a combination of automated unit and integration tests.

## Unit Tests

Unit tests are used for the `Broker`, `GateNode`, `VisitorNode`, `Repository` and `State` classes, as well as for encoding and decoding network messages. Instructions for running the unit tests are included at the end of this report.

Tests for the gate and visitor nodes check the functionality of the election and mutual exclusion algorithms. Each test creates a new node, modifies its state to simulate a certain condition (such as being in the middle of an election) and calls the `process_message` method. The generated messages and resulting state are then checked with the expected output. This way I am able to make sure that the algorithm works as it is supposed in every corner case, without having to construct a whole network for each case. 

Unit tests were also very helpful during development. I was able to think about the expected behaviour, write the unit tests for the behaviour and finally implement it. After making changes I could easily check that the existing functionality still works as required.

## Integration Tests

While unit tests are good for checking the functionality of a small part of the system, integration tests are needed as well to make sure that the system works as a whole. For this, I developed a number of scripts that create a network and instruct the system to perform a task.

The simplest one is `hello.py`, which creates a network of 10 nodes and instructs every node to send a `hello` message to its neighbours, who then respond with a `hey` message. This is to make sure that the communication between nodes works correctly.

The `election.py` script creates the same network and instructs a random gate node to start an election. I used this script to make sure that elections can be completed successfully. This was useful when I was trying to find a bug where the election did not finish -- using the script I was able to quickly check if a code change fixed the bug.

Finally, the `cli.py` script can be used to control the system manually. I used this script for testing entering and leaving the park, removing the leader node, terminating nodes, and to stress-test the system, as shown in the examples.

# Evaluation

I implemented all three parts as specified in the practical specification. The system supports electing a leader node using the wireless algorithm and implements mutual exclusion. All messages are logged into the console, but since the Python `logging` module is used, it would be possible to configure it to use a file as well.

My implementation is tested using unit and integration tests. However, more automated integration tests could be implemented, for example to test entering and leaving the park.

All nodes run in the same process, but they do not share any memory -- they could be started as different processes and the system would still work. This is achieved by using only TCP sockets for communication between nodes. The current implementation would not work when it is started on different machines, as the shared resource is implemented using a file.

Error handling in the nodes could be improved. At the moment, when an error occurs, the thread running the node simply crashes, but the rest of the system keeps running. A single failure will most likely render the system unusable, as there is no fault tolerance built in, except for manually terminating nodes. For instance, if a node crashes during the election, the election will never finish.

# Conclusion

My task in this practical was to implement a simple distributed system for controlling the entry and exit gates in an amusement park. The system uses TCP sockets to communicate between the gate and visitor nodes. A leader node can be elected and then used by other nodes to control mutual exclusion on access to a shared resource, which contains the list of all visitors who are currently in the park. Visitor nodes connect to gate nodes and ask for permission to enter or leave the park. The functionality of the system is thoroughly checked with unit and integration tests.

This practical enforced my knowledge in designing and implementing simple distributed algorithms. I improved my experience with using raw TCP sockets to implement communication, and using threads and queues to build concurrent systems. I enjoyed working on this practical, as the task was challenging and interesting.

# User Manual

The system was developed using Python 3.6. To use it, first create and activate a Python virtual environment and install dependencies:

```
$ virtualenv-3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

At this point, you can run unit tests:

```
$ pytest
```

You can also run the integration test scripts:

```
$ python hello.py
$ python election.py
```

Finally, you can start the command line interface:

```
$ python cli.py
```
