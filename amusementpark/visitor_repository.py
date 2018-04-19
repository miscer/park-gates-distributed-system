import os
import json
import collections

State = collections.namedtuple('State', 'capacity visitors')

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
            data = state._asdict()
            json.dump(data, file)

    def delete_state(self):
        os.remove(self.filename)
