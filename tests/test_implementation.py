from glassbox.implementation import merge_arrays
from array import array
from hypothesis import given
import hypothesis.strategies as st

deduped_arrays = st.lists(
    st.integers(0, 2 ** 32 - 1), unique=True).map(
    lambda x: array('I', sorted(x)))


@given(deduped_arrays, deduped_arrays)
def test_merges_correctly(x, y):
    t = merge_arrays(x, y)
    assert list(t) == sorted(set(x) | set(y))
