from glassbox import Record
import hypothesis.strategies as st
from array import array
from hypothesis import given, assume

STATE_SIZE = 16


def build_record(labels):
    labels = sorted(set(labels))
    return Record(array('I', labels))


Records = st.builds(build_record, st.lists(st.integers(0, 2 ** 32 - 1)))


@given(st.lists(Records))
def test_sortable(records):
    records.sort()
    for i in range(len(records)):
        for j in range(i, len(records)):
            assert records[i] <= records[j]


@given(Records, Records)
def test_contains_is_compatible_with_ordering(x, y):
    assume(x.contained_in(y))
    if y.contained_in(x):
        assert x == y


@given(st.lists(Records))
def test_records_are_hashable(xs):
    d = {}
    for i, x in enumerate(xs):
        d[x] = i
    for i, x in enumerate(xs):
        assert d[x] >= i


@given(Records, Records)
def test_union_produces_larger(x, y):
    z = x | y
    assert x.contained_in(z)
    assert y.contained_in(z)
    if y.contained_in(x):
        assert z == x
    if x.contained_in(y):
        assert z == y
