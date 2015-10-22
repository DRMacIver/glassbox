from glassbox.implementation import merge_arrays, array_contained


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
