from glassbox import Record
import hypothesis.strategies as st
from array import array
from hypothesis import given, assume
from glassbox.novelty import NoveltyDetector


def build_record(labels):
    labels = sorted(set(labels))
    return Record(array('I', labels))


Records = st.builds(build_record, st.lists(st.integers(0, 2 ** 32 - 1)))

@given(Records)
def test_record_contained_in_self(x):
    assert x.contained_in(x)


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
    assert set(z.labels) == set(x.labels) | set(y.labels)


@given(st.lists(Records))
def test_novelty_is_containment_in_union(ls):
    u = Record(array('I'))
    detector = NoveltyDetector()
    for l in ls:
        assert l.contained_in(u) == (not detector.novel(l))
        u |= l
    
