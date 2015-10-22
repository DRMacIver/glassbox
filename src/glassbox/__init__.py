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
from glassbox.record import Record
from glassbox.implementation import native, _collect, _begin

__all__ = ['begin', 'collect', 'Record', 'native']

prev_tracers = []


def begin():
    prev_tracers.append(sys.gettrace())
    sys.settrace(None)
    return _begin()


def collect():
    result = Record(_collect())
    sys.settrace(prev_tracers.pop())
    return result
