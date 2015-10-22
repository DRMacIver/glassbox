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


def _labels(_data):
    cdef array.array data = <array.array>_data
    cdef array.array labels = arr('I')
    cdef unsigned int b
    cdef unsigned int a
    cdef unsigned int i
    cdef unsigned int count = 0
    cdef unsigned int datalen = len(data)
    for i in xrange(datalen):
        if data.data.as_uints[i] > 0:
            count += 1
    for i in xrange(datalen):
        b = data.data.as_uints[i]
        if b == 0:
            continue
        a = i << 4
        if b > 0:
            append_uint(labels, a + 1)
        if b > 1:
            append_uint(labels, a + 2)
        if b > 2:
            append_uint(labels, a + 3)
        if b > 3:
            append_uint(labels, a + 4)
        if b > 4:
            append_uint(labels, a + 5)
        if b > 8:
            append_uint(labels, a + 6)
        if b > 16:
            append_uint(labels, a + 7)
        if b > 32:
            append_uint(labels, a + 8)
        if b > 64:
            append_uint(labels, a + 9)
        if b > 128:
            append_uint(labels, a + 10)
    return labels


cdef append_uint(array.array x, unsigned int i):
    x.append(i)


def merge_arrays(_x, _y):
    cdef array.array x = _x
    cdef array.array y = _y
    cdef array.array result = arr('I')
    cdef unsigned int xi = 0
    cdef unsigned int yi = 0
    cdef unsigned int lx = len(x)
    cdef unsigned int ly = len(y)
    cdef unsigned int xv
    cdef unsigned int yv
    while xi < lx and yi < ly:
        xv = x.data.as_uints[xi]
        yv = y.data.as_uints[yi]
        if xv < yv:
            append_uint(result, xv)
            xi += 1
        elif xv > yv:
            append_uint(result, yv)
            yi += 1
        else:
            append_uint(result, xv)
            xi += 1
            yi += 1
    while xi < lx:
        append_uint(result, x.data.as_uints[xi])
        xi += 1
    while yi < ly:
        append_uint(result, y.data.as_uints[yi])
        yi += 1
    return result

cdef object _array_contained(array.array x, array.array y):
    cdef unsigned int lx = len(x)
    cdef unsigned int ly = len(y)
    if lx > ly:
        return False
    if lx == 0:
        return True
    if x.data.as_uints[0] < y.data.as_uints[0]:
        return False
    if x.data.as_uints[lx - 1] > y.data.as_uints[ly - 1]:
        return False
    cdef unsigned int probe = 0
    cdef unsigned int v
    cdef unsigned int o
    cdef unsigned int lo
    cdef unsigned int hi
    cdef unsigned int mid
    cdef unsigned int i
    cdef unsigned int k
    for k in xrange(lx):
        v = x.data.as_uints[k]
        o = y.data.as_uints[probe]
        if v == o:
            probe += 1
            continue
        elif v < o:
            return False

        lo = probe
        i = 0
        while True:
            hi = probe + 2 ** i
            i += 1
            if hi >= ly:
                hi = ly - 1
                break
            if y.data.as_uints[hi] >= v:
                break
            else:
                lo = hi
        # Invariant: y[lo] < v <= y[hi]
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            o = y.data.as_uints[mid]
            if v <= o:
                hi = mid
            else:
                lo = mid
        if v == y.data.as_uints[hi]:
            probe = hi + 1
            continue
        else:
            return False
    return True

def array_contained(x, y):
    return _array_contained(<array.array>x, <array.array>y)

def merge_into(_x, _y, _scratch):
    del _scratch[:]
    cdef array.array x = _x;
    cdef array.array y = _y;
    cdef array.array scratch = _scratch;
    cdef unsigned int xi = 0
    cdef unsigned int yi = 0
    cdef unsigned int lx = len(x)
    cdef unsigned int ly = len(y)
    cdef unsigned int xv;
    cdef unsigned int yv;
    while xi < lx and yi < ly:
        xv = x.data.as_uints[xi]
        yv = y.data.as_uints[yi]
        if xv < yv:
            append_uint(scratch, xv)
            xi += 1
        elif xv > yv:
            append_uint(scratch, yv)
            yi += 1
        else:
            append_uint(scratch, xv)
            xi += 1
            yi += 1
    while xi < lx:
        append_uint(scratch, x.data.as_uints[xi])
        xi += 1
    while yi < len(y):
        append_uint(scratch, y.data.as_uints[yi])
        yi += 1
