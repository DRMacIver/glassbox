import hashlib
import sys
from glassbox.implementation import merge_arrays


class Record(object):
    """A record is a structured representation of a program's execution path.

    It maintains a set of counts for each (bucketed) branch executed.

    Records can be compared for equality and ordered. One record being <=
    another has no particular significance, but is a total ordering compatible
    with the partial ordering defined by the branches of one record being a
    subset of the other.
    """
    def __init__(self, labels):
        self.labels = labels
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
                for l in self.labels:
                    hasher.update(str(l))
                self.__identifier = hasher.hexdigest()
            finally:
                sys.settrace(orig)
        return self.__identifier

    def __repr__(self):
        return "Record:%s%r" % (self.identifier, list(self.labels))

    def __eq__(self, other):
        return isinstance(other, Record) and (
            self.identifier == other.identifier
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.identifier)

    def contained_in(self, other):
        if len(self.labels) > len(other.labels):
            return False
        if not self.labels:
            return True
        assert other.labels
        if self.labels[0] < other.labels[0]:
            return False
        if self.labels[-1] > other.labels[-1]:
            return False
        probe = 0
        for v in self.labels:
            o = other.labels[probe]
            if v == o:
                probe += 1
                continue
            elif v < o:
                return False
            assert v > o

            lo = probe
            hi = len(other.labels) - 1
            # Invariant: other.labels[lo] < v <= other.labels[hi]
            while lo + 1 < hi:
                mid = (lo + hi) // 2
                o = other.labels[mid]
                if v <= o:
                    hi = mid
                else:
                    lo = mid
            if v == other.labels[hi]:
                probe = hi + 1
                continue
            else:
                return False
        return True

    def __or__(self, other):
        if not isinstance(other, Record):
            raise TypeError("Cannot union Record with %r of type %s" % (
                other, other.__name__
            ))

        if len(other.labels) > len(self.labels):
            self, other = other, self
        if other.contained_in(self):
            return self

        return Record(
            merge_arrays(self.labels, other.labels)
        )
