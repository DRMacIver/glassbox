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
import hashlib

__all__ = ['begin', 'collect', 'Record']


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
    data = arrays.pop()
    for a in arrays:
        for i in range(len(data)):
            a[i] += data[i]
    result = Record(data)
    sys.settrace(restore)
    return result


levels = [1, 2, 3, 4, 8, 16, 32, 128]


def label(a, b):
    for t, l in enumerate(levels, 1):
        if b <= l:
            b = t
            break
    else:
        b = 1 + len(levels)
    return "%d:%d" % (a, b)


class Record(object):
    """A record is a structured representation of a program's execution path.
    """
    def __init__(self, data):
        self.data = arr('I', data)
        self.counts = {}
        self.__labels = None
        self.__identifier = None

    @property
    def identifier(self):
        """A unique string identifier that distinguishes two records. Two
        records are equal if and only if their string identifier is equal.

        There is no other significant meaning assigned to the identifier"""
        if self.__identifier is None:
            orig = sys.gettrace()
            sys.settrace(None)
            try:
                hasher = hashlib.sha1()
                for i in range(len(self.data)):
                    if self.data[i] > 0:
                        hasher.update(
                            ("%d:%d" % (i, self.data[i])).encode('ascii'))
                self.__identifier = hasher.hexdigest()
            finally:
                sys.settrace(orig)
        return self.__identifier

    @property
    def labels(self):
        """
        Returns a frozenset containing a set of classification labels for this
        Record. Each label is a string but should not be interpreted as having
        a significant meaning.
        """
        if self.__labels is None:
            orig = sys.gettrace()
            sys.settrace(None)
            try:
                labels = set()
                for i in range(len(self.data)):
                    if self.data[i]:
                        labels.add(label(i, self.data[i]))
                self.__labels = frozenset(labels)
            finally:
                sys.settrace(orig)
        return self.__labels

    def __repr__(self):
        return "Record:%s%r" % (self.identifier, list(self.labels))

    def __eq__(self, other):
        return isinstance(other, Record) and (
            self.identifier == other.identifier
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return (self == other) or (self.data < other.data)

    def __ge__(self, other):
        return (self == other) or (self.data > other.data)

    def __lt__(self, other):
        return (self != other) and (self.data < other.data)

    def __gt__(self, other):
        return (self != other) and (self.data > other.data)

    def contained_in(self, other):
        return all(
            self.data[i] <= other.data[i] for i in range(len(self.data)))


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
    # This tracer should never be active when we have an empty stack of
    # arrays but it seems sometimes CPython gets itself a bit confused and
    # does it anyway. This is a workaround to that problem.
    if arrays:
        arrays[-1][transition & STATE_MASK] += 1
    prev_state = curr_state >> 1


def tracer(frame, event, arg):
    record_state(frame.f_code.co_filename, frame.f_lineno)
    return tracer
