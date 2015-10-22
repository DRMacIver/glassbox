from array import array
from glassbox.implementation import merge_into, array_contained


class NoveltyDetector(object):
    def __init__(self):
        self.data = array('I')
        self.scratch = array('I')

    def novel(self, record):
        if array_contained(record.labels, self.data):
            return False
        self.merge_record(record)
        return True

    def merge_record(self, record):
        merge_into(self.data, record.labels, self.scratch)
        assert len(self.scratch) > len(self.data)
        self.data, self.scratch = self.scratch, self.data
