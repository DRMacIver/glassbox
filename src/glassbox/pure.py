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
                labels.append(a + 6)
            if b > 16:
                labels.append(a + 7)
            if b > 32:
                labels.append(a + 8)
            if b > 64:
                labels.append(a + 9)
            if b > 128:
                labels.append(a + 10)
        return labels
    finally:
        sys.settrace(orig)


def merge_arrays(x, y):
    result = arr('I')
    xi = 0
    yi = 0
    while xi < len(x) and yi < len(y):
        xv = x[xi]
        yv = y[yi]
        if xv < yv:
            result.append(xv)
            xi += 1
        elif xv > yv:
            result.append(yv)
            yi += 1
        else:
            result.append(xv)
            xi += 1
            yi += 1
    while xi < len(x):
        result.append(x[xi])
        xi += 1
    while yi < len(y):
        result.append(y[yi])
        yi += 1
    return result


def array_contained(x, y):
    if len(x) > len(y):
        return False
    if not x:
        return True
    assert y
    if x[0] < y[0]:
        return False
    if x[-1] > y[-1]:
        return False
    probe = 0
    for v in x:
        o = y[probe]
        if v == o:
            probe += 1
            continue
        elif v < o:
            return False
        assert v > o

        lo = probe
        i = 0
        while True:
            hi = probe + 2 ** i
            i += 1
            if hi >= len(y):
                hi = len(y) - 1
                break
            if y[hi] >= v:
                break
            else:
                lo = hi
        # Invariant: y[lo] < v <= y[hi]
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            o = y[mid]
            if v <= o:
                hi = mid
            else:
                lo = mid
        if v == y[hi]:
            probe = hi + 1
            continue
        else:
            return False
    return True


def merge_into(x, y, scratch):
    del scratch[:]
    xi = 0
    yi = 0
    while xi < len(x) and yi < len(y):
        xv = x[xi]
        yv = y[yi]
        if xv < yv:
            scratch.append(xv)
            xi += 1
        elif xv > yv:
            scratch.append(yv)
            yi += 1
        else:
            scratch.append(xv)
            xi += 1
            yi += 1
    while xi < len(x):
        scratch.append(x[xi])
        xi += 1
    while yi < len(y):
        scratch.append(y[yi])
        yi += 1
