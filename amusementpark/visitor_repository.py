import os
import json
import collections

class State:
    def __init__(self, capacity, visitors):
        self.capacity = capacity
        self.visitors = visitors
    
    def enter(self, visitor):
        assert visitor not in self.visitors
        assert len(self.visitors) < self.capacity
        self.visitors.append(visitor)
    
    def leave(self, visitor):
        assert visitor in self.visitors
        self.visitors.remove(visitor)
    
    def __eq__(self, other):
        if isinstance(other, State):
            return self.capacity == other.capacity and self.visitors == other.visitors
        else:
            return super().__eq__(other)

class Repository:
    def __init__(self, filename):
        self.filename = filename

    def read_state(self):
        try:
            with open(self.filename) as file:
                data = json.load(file)
                return State(**data)
        except FileNotFoundError:
            return None

    def write_state(self, state):
        with open(self.filename, 'w') as file:
            data = {'capacity': state.capacity, 'visitors': state.visitors}
            json.dump(data, file)

    def delete_state(self):
        os.remove(self.filename)
