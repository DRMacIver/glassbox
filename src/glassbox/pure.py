import sys
from array import array as arr


arrays = []
prev_state = 0


STATE_SIZE = 2 ** 16
STATE_MASK = STATE_SIZE - 1


def push_array():
    array_state = arr('I')
    array_state.append(0)
    while len(array_state) < STATE_SIZE:
        array_state.extend(array_state)
    assert len(array_state) == STATE_SIZE
    arrays.append(array_state)


def inthash(a):
    a = (a ^ 61) ^ (a >> 16)
    a = a + (a << 3)
    a = a ^ (a >> 4)
    a = a * 0x27d4eb2d
    a = a ^ (a >> 15)
    return a


def record_state(filename, line):
    curr_state = hash(filename) * 3 + inthash(line)
    global prev_state
    transition = curr_state ^ prev_state
    # This tracer should never be active when we have an empty stack of
    # arrays but it seems sometimes CPython gets itself a bit confused and
    # does it anyway. This is a workaround to that problem.
    if arrays:
        arrays[-1][transition & STATE_MASK] += 1
    prev_state = curr_state >> 1


def tracer(frame, event, arg):
    record_state(frame.f_code.co_filename, frame.f_lineno)
    return tracer


def _begin():
    """Start tracking program state.

    If begin() has previously been called, any labels that occur during this
    execution will also be made visible to previous begin calls.
    """
    sys.settrace(None)
    assert sys.gettrace() is None
    global prev_state
    prev_state = 0
    push_array()
    sys.settrace(tracer)
    assert sys.gettrace() is tracer


def _collect():
    """Return a set of string labels corresponding to events that have been
    seen since the last begin() call"""
    t = sys.gettrace()
    assert t is tracer, t
    sys.settrace(None)
    assert sys.gettrace() is None
    data = arrays.pop()
    for a in arrays:
        for i in range(len(data)):
            a[i] += data[i]
    return data
