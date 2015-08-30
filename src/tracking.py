import sys
from array import array as arr

STATE_SIZE = 2 ** 16
STATE_MASK = STATE_SIZE - 1


arrays = []
prev_state = 0
prev_tracers = []


def push_array():
    array_state = arr('Q')
    while len(array_state) < STATE_SIZE:
        array_state.append(0)
    arrays.append(array_state)


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
    arrays[-1][transition & STATE_MASK] += 1
    prev_state = curr_state >> 1


def tracer(frame, event, arg):
    record_state(frame.f_code.co_filename, frame.f_lineno)
    return tracer


levels = [1, 2, 3, 4, 8, 16, 32, 128]


def begin():
    global prev_state
    prev_state = 0
    push_array()
    prev_tracers.append(sys.gettrace())
    sys.settrace(tracer)


def collect():
    restore = prev_tracers.pop()
    sys.settrace(None)
    result = set()
    array_state = arrays.pop()
    for i in range(len(array_state)):
        if array_state[i]:
            for t, l in enumerate(levels, 1):
                if array_state[i] <= l:
                    result.add((i, t))
                    break
            else:
                result.add((i, 1 + len(levels)))
    sys.settrace(restore)
    return result
