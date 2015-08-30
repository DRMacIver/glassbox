from glassbox import Record
import hypothesis.strategies as st
from array import array
from hypothesis import given, assume

STATE_SIZE = 16


def build_record(indices):
    data = array('I', [0] * STATE_SIZE)
    for i in indices:
        data[i] += 1
    return Record(data)


Records = st.builds(
    build_record,
    st.lists(st.integers(0, STATE_SIZE - 1), average_size=STATE_SIZE))


@given(st.lists(Records))
def test_sortable(records):
    records.sort()
    for i in range(len(records)):
        for j in range(i, len(records)):
            assert records[i] <= records[j]


@given(Records, Records)
def test_contains_is_compatible_with_ordering(x, y):
    assume(x.contained_in(y))
    assert x <= y
    if y.contained_in(x):
        assert x == y
