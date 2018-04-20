import pytest
from amusementpark.visitor_repository import State, Repository

def test_read_write_delete(tmpdir):
    filename = tmpdir.join('repository.json')
    repository = Repository(filename)

    assert repository.read_state() is None
    
    repository.write_state(State(capacity=10, visitors=[1, 2, 3]))
    assert repository.read_state() == State(capacity=10, visitors=[1, 2, 3])

    repository.delete_state()
    assert repository.read_state() is None

def test_enter():
    state = State(capacity=2, visitors=[100])

    with pytest.raises(AssertionError):
        state.enter(100)
    
    state.enter(200)
    assert state.visitors == [100, 200]

    with pytest.raises(AssertionError):
        state.enter(300)

def test_leave():
    state = State(capacity=2, visitors=[100])

    with pytest.raises(AssertionError):
        state.leave(200)
    
    state.leave(100)
    assert state.visitors == []