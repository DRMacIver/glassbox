import os
from glassbox import begin, collect


def to_int(x):
    if isinstance(x, str):
        return ord(x)
    else:
        return int(x)


def do_hash(data):
    x = 0
    for c in data:
        x *= 31
        x += to_int(c)
    return x

HASHING_DATA = os.urandom(1024 * 10)


def test_hashing_while_glassboxed(benchmark):
    @benchmark
    def result():
        begin()
        try:
            do_hash(HASHING_DATA)
        finally:
            collect()
    assert result is None


def test_hashing_while_not_glassboxed(benchmark):
    @benchmark
    def result():
        do_hash(HASHING_DATA)
    assert result is None
