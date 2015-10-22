import hashlib
import sys
from intset import IntSet


class Record(object):
    """A record is a structured representation of a program's execution path.

    It maintains a set of counts for each (bucketed) branch executed.

    Records can be compared for equality and ordered. One record being <=
    another has no particular significance, but is a total ordering compatible
    with the partial ordering defined by the branches of one record being a
    subset of the other.
    """
    def __init__(self, labels):
        if isinstance(labels, IntSet):
            self.labels = labels
        else:
            self.labels = IntSet(labels)
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
                for i, j in self.labels.intervals():
                    hasher.update(str(i))
                    hasher.update(str(j))
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
        return self.labels.issubset(other.labels)

    def __or__(self, other):
        if not isinstance(other, Record):
            raise TypeError("Cannot union Record with %r of type %s" % (
                other, other.__name__
            ))
        return Record(self.labels | other.labels)
