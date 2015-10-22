from glassbox.implementation import merge_arrays, array_contained


class Record(object):
    """A record is a structured representation of a program's execution path.

    A record has a set of labels, which may be accessed as record.labels and
    are a sorted array of unsigned 32-bit integers. Each one corresponds to
    some interesting observed behaviour.
    """
    def __init__(self, labels):
        self.labels = labels

    def __repr__(self):
        return "Record(%r)" % (list(self.labels),)

    def __eq__(self, other):
        return isinstance(other, Record) and (
            self.labels == other.labels
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if not self.labels:
            return 0
        return hash((
            self.labels[0], self.labels[-1],
            self.labels[len(self.labels) // 2],
            len(self.labels),
        ))

    def contained_in(self, other):
        """Return True if every behaviour observed by this record is also
        observed in the other"""

        return array_contained(self.labels, other.labels)

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
