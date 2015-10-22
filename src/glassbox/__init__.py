import sys
from glassbox.record import Record
from glassbox.implementation import native, _collect, _begin
from glassbox.novelty import NoveltyDetector

__all__ = ['begin', 'collect', 'Record', 'native', 'NoveltyDetector']

prev_tracers = []


def begin():
    """Start collecting data until a matching call to collect occurs"""
    prev_tracers.append(sys.gettrace())
    sys.settrace(None)
    return _begin()


def collect():
    """Stop collecting data and return a Record containing the program
    execution since the matching begin call"""
    result = Record(_collect())
    sys.settrace(prev_tracers.pop())
    return result
