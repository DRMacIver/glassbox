"""
This module exports an API that is intended to support glass box testing and
other tools that must introspect program state.

It is deliberately quite a low level API. You will probably want to build
better abstractions on top of it.

It exposes only two functions: begin and collect. begin starts gathering labels
and collect returns a set of string labels that indicate what has happened
since the previous calls.

Note: This is incompatible with running other tracing based APIs at the time.
Any tracer that was previously running will be restored at the end of the last
collect() call, but it will be suspended until then.
"""

import sys
from array import array as arr


__all__ = ['begin', 'collect']


def begin():
    """Start tracking program state.

    If begin() has previously been called, any labels that occur during this
    execution will also be made visible to previous begin calls.
    """
    prev_tracers.append(sys.gettrace())
    sys.settrace(None)
    global prev_state
    prev_state = 0
    push_array()
    sys.settrace(tracer)


def collect():
    """Return a set of string labels corresponding to events that have been
    seen since the last begin() call"""
    restore = prev_tracers.pop()
    sys.settrace(None)
    result = set()
    array_state = arrays.pop()
    for a in arrays:
        for i in range(len(array_state)):
            a[i] += array_state[i]
    for i in range(len(array_state)):
        if array_state[i]:
            for t, l in enumerate(levels, 1):
                if array_state[i] <= l:
                    result.add(label(i, t))
                    break
            else:
                result.add(label(i, 1 + len(levels)))
    sys.settrace(restore)
    return result


STATE_SIZE = 2 ** 16
STATE_MASK = STATE_SIZE - 1


arrays = []
prev_state = 0
prev_tracers = []


def push_array():
    array_state = arr('I')
    while len(array_state) < STATE_SIZE:
        array_state.append(0)
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
    arrays[-1][transition & STATE_MASK] += 1
    prev_state = curr_state >> 1


def tracer(frame, event, arg):
    record_state(frame.f_code.co_filename, frame.f_lineno)
    return tracer


levels = [1, 2, 3, 4, 8, 16, 32, 128]


def label(a, b):
    return "%d:%d" % (a, b)
