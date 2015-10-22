import sys
from array import array as arr
from glassbox.compat import _range


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
    return _labels(data)


def label(a, b):
    if b > 4:
        if b <= 8:
            b = 5
        elif b <= 16:
            b = 6
        elif b <= 32:
            b = 7
        elif b <= 128:
            b = 8
        else:
            b = 9
    return (a << 4) + b


def _labels(data):
    orig = sys.gettrace()
    sys.settrace(None)
    try:
        labels = arr('I')
        for i in _range(len(data)):
            a = i << 4
            b = data[i]
            if b > 0:
                labels.append(a + 1)
            if b > 1:
                labels.append(a + 2)
            if b > 2:
                labels.append(a + 3)
            if b > 3:
                labels.append(a + 4)
            if b > 4:
                labels.append(a + 5)
            if b > 8:
                labels.append(b + 6)
            if b > 16:
                labels.append(b + 7)
            if b > 32:
                labels.append(b + 8)
            if b > 64:
                labels.append(b + 9)
            if b > 128:
                labels.append(b + 10)
        return labels
    finally:
        sys.settrace(orig)
