import sys
from array import array as arr
from cpython cimport array
from cpython.ref cimport PyObject

cdef extern from "Python.h":

    # We make these an opague types. If the user wants specific attributes,
    # they can be declared manually.

    ctypedef struct PyInterpreterState:
        pass

    ctypedef struct PyThreadState:
        pass

    ctypedef struct PyCodeObject:
        PyObject *co_filename;

    ctypedef struct PyFrameObject:
        PyCodeObject *f_code;
        int f_lineno;

    # This is not actually a struct, but make sure it can never be coerced to
    # an int or used in arithmetic expressions
    ctypedef struct PyGILState_STATE

    # The type of the trace function registered using PyEval_SetProfile() and
    # PyEval_SetTrace().
    # Py_tracefunc return -1 when raising an exception, or 0 for success.
    ctypedef int (*Py_tracefunc)(PyObject *, PyFrameObject *, int, PyObject *)

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


cdef void record_state(object filename, int line):
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
    record_state(<object>(_frame.f_code.co_filename), _frame.f_lineno)
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
    return _labels(data)

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
    cdef array.array labels = arr('I')
    cdef unsigned int v = 0
    for i in xrange(len(data)):
        v = data.data.as_uints[i]
        if v > 0:
            labels.append(label(i, v))
    return labels

def _labels(_data):
    cdef array.array data = <array.array>_data
    cdef array.array labels = arr('I')
    for i in xrange(len(data)):
        a = i << 4
        b = data[i]
        if b > 0:
            labels.append(a + 1)
        if b > 1:
            labels.append(a + 2)
        if b > 2:
            labels.append(a + 3)
        if b > 3:
            labels.append(a + 4)
        if b > 4:
            labels.append(a + 5)
        if b > 8:
            labels.append(b + 6)
        if b > 16:
            labels.append(b + 7)
        if b > 32:
            labels.append(b + 8)
        if b > 64:
            labels.append(b + 9)
        if b > 128:
            labels.append(b + 10)
    return labels


def merge_arrays(x, y):
    result = arr('I')
    xi = 0
    yi = 0
    while xi < len(x) and yi < len(y):
        xv = x[xi]
        yv = y[yi]
        if xv < yv:
            result.append(xv)
            xi += 1
        elif xv > yv:
            result.append(yv)
            yi += 1
        else:
            result.append(xv)
            xi += 1
            yi += 1
    while xi < len(x):
        result.append(x[xi])
        xi += 1
    while yi < len(y):
        result.append(y[yi])
        yi += 1
    return result
