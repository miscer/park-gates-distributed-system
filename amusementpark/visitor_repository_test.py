from amusementpark.visitor_repository import State, Repository

def test_read_write_delete(tmpdir):
    filename = tmpdir.join('repository.json')
    repository = Repository(filename)

    assert repository.read_state() is None
    
    repository.write_state(State(capacity=10, visitors=[1, 2, 3]))
    assert repository.read_state() == State(capacity=10, visitors=[1, 2, 3])

    repository.delete_state()
    assert repository.read_state() is None