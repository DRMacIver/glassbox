
import sys
from array import array as arr
import random
import os
import hashlib

STATE_SIZE = 2 ** 16
STATE_MASK = STATE_SIZE - 1
array_state = arr('Q')
while len(array_state) < STATE_SIZE:
    array_state.append(0)

# Reloading support only
while len(array_state) > STATE_SIZE:
    array_state.pop()

prev_state = 0


def zero_array():
    assert len(array_state) == STATE_SIZE
    for i in range(len(array_state)):
        array_state[i] = 0


def inthash(a):
    a = (a ^ 61) ^ (a >> 16)
    a = a + (a << 3)
    a = a ^ (a >> 4)
    a = a * 0x27d4eb2d
    a = a ^ (a >> 15)
    return a


def record_state(filename, line):
    curr_state = hash(filename) * 3 + inthash(line)
    global prev_state
    transition = curr_state ^ prev_state
    array_state[transition & STATE_MASK] += 1
    prev_state = curr_state >> 1


def tracer(frame, event, arg):
    record_state(frame.f_code.co_filename, frame.f_lineno)
    return tracer


def high_bit(n):
    i = 0
    while n:
        i += 1
        n >>= 1
    return i


levels = [1, 2, 3, 4, 8, 16, 32, 128]


def extract_labels():
    for i in range(len(array_state)):
        if array_state[i]:
            for t, l in enumerate(levels, 1):
                if array_state[i] <= l:
                    yield (i, t)
                    break
            else:
                yield (i, 1 + len(levels))
    zero_array()


def begin():
    assert sys.gettrace() is None
    global prev_state
    prev_state = 0
    zero_array()
    sys.settrace(tracer)


def collect():
    sys.settrace(None)
    return set("%d:%d" % kv for kv in extract_labels())
