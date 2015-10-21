import sys
from array import array as arr
from cpython cimport array
from cpython.ref cimport PyObject

from cpython.pystate cimport (
    Py_tracefunc, PyFrameObject,
    PyTrace_CALL, PyTrace_EXCEPTION, PyTrace_LINE, PyTrace_RETURN,
    PyTrace_C_CALL, PyTrace_C_EXCEPTION, PyTrace_C_RETURN)

cdef extern from *:
    void PyEval_SetTrace(Py_tracefunc cfunc, object obj)

cdef extern from "frameobject.h":
    pass


cdef list arrays = []

cdef int prev_state = 0


cdef int STATE_SIZE = 2 ** 16
cdef int STATE_MASK = STATE_SIZE - 1

cdef push_array():
    cdef array.array array_state = arr('I')
    array.resize(array_state, STATE_SIZE)
    array.zero(array_state)
    arrays.append(array_state)


cdef int inthash(int a):
    a = (a ^ 61) ^ (a >> 16)
    a = a + (a << 3)
    a = a ^ (a >> 4)
    a = a * 0x27d4eb2d
    a = a ^ (a >> 15)
    return a


cdef void record_state(str filename, int line):
    cdef int curr_state = hash(filename) * 3 + inthash(line)
    global prev_state
    cdef int transition = curr_state ^ prev_state
    # This tracer should never be active when we have an empty stack of
    # arrays but it seems sometimes CPython gets itself a bit confused and
    # does it anyway. This is a workaround to that problem.
    if not arrays:
        return
    cdef array.array target = arrays[-1]
    target.data.as_uints[transition & STATE_MASK] += 1
    prev_state = curr_state >> 1


cdef int tracer(
    PyObject* _traceobj, PyFrameObject* _frame, int what, PyObject* arg
) except -1:
    frame, traceobj = <object>_frame, <object>_traceobj
    record_state(frame.f_code.co_filename, frame.f_lineno)
    return 0


class ProxyTracer(object):
    def __call__(self, frame, event, arg):
        if sys.gettrace() is self:
            record_state(frame.f_code.co_filename, frame.f_lineno)
            install_tracer()
            return self

cdef object proxy_tracer = ProxyTracer()
                

cdef void install_tracer():
    PyEval_SetTrace(<Py_tracefunc>tracer, proxy_tracer)

def _begin():
    """Start tracking program state.

    If begin() has previously been called, any labels that occur during this
    execution will also be made visible to previous begin calls.
    """
    global prev_state
    prev_state = 0
    push_array()
    install_tracer()


def _collect():
    """Return a set of string labels corresponding to events that have been
    seen since the last begin() call"""
    cdef array.array data = arrays.pop()
    cdef array.array a
    for _a in arrays:
        a = _a
        for i in xrange(STATE_SIZE):
            a.data.as_uints[i] += data.data.as_uints[i]
    PyEval_SetTrace(NULL, None)
    return data

cdef unsigned int label(unsigned int a, unsigned int b):
    if b > 4:
        if b <= 8:
            b = 5
        elif b <= 16:
            b = 6
        elif b <= 32:
            b = 7
        elif b <= 128:
            b = 8
        else:
            b = 9
    return (a << 4) + b


def _labels(_data):
    cdef array.array data = <array.array>_data
    cdef set labels = set()
    cdef unsigned int v = 0
    for i in xrange(len(data)):
        v = data.data.as_uints[i]
        if v > 0:
            labels.add(label(i, v))
    return frozenset(labels)
