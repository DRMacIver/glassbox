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
import hashlib
from array import array as arr
import os
from glassbox.compat import _range


__all__ = ['begin', 'collect', 'Record']

native = False

if os.getenv('GLASSBOX_FORCE_PURE') == 'true':
    from glassbox.pure import _begin, _collect
else:
    try:
        from glassbox.extension import _begin, _collect, _labels
        native = True
    except ImportError:
        from glassbox.pure import _begin, _collect, _labels


prev_tracers = []


def begin():
    prev_tracers.append(sys.gettrace())
    sys.settrace(None)
    return _begin()


def collect():
    result = Record(_collect())
    sys.settrace(prev_tracers.pop())
    return result


class Record(object):
    """A record is a structured representation of a program's execution path.

    It maintains a set of counts for each (bucketed) branch executed.

    Records can be compared for equality and ordered. One record being <=
    another has no particular significance, but is a total ordering compatible
    with the partial ordering defined by the branches of one record being a
    subset of the other.
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
                for i in _range(len(self.data)):
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
            self.__labels = frozenset(_labels(self.data))
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
        """Returns True if every branch executed in this record is executed at
        least that many times in the other"""
        return all(
            self.data[i] <= other.data[i] for i in _range(len(self.data)))
