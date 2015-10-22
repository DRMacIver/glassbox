import os
from glassbox import begin, collect
import sys
import pytest
import platform


@pytest.fixture(autouse=True, scope='function')
def needs_cleanup(request):
    original_trace = sys.gettrace()

    def cleanup():
        sys.settrace(original_trace)
    request.addfinalizer(cleanup)

counter = 0


def countingtrace(frame, event, arg):
    global counter
    counter += 1
    return countingtrace


def run_for_labels(f, *args):
    begin()
    f(*args)
    return collect()


def run_multiple_for_labels(n, f, *args):
    return [
        run_for_labels(f, *args) for _ in range(n)
    ]


def onebranch(x):
    if x:
        return 1


def test_unsets_trace():
    orig = sys.gettrace()
    begin()
    collect()
    assert sys.gettrace() == orig


def test_is_stable():
    assert run_for_labels(onebranch, False) == run_for_labels(onebranch, False)
    assert run_for_labels(onebranch, True) == run_for_labels(onebranch, True)


def test_distinct_reprs():
    assert repr(run_for_labels(onebranch, False)) == repr(
        run_for_labels(onebranch, False))
    assert repr(run_for_labels(onebranch, False)) != repr(
        run_for_labels(onebranch, True))


def test_detects_branches():
    assert run_for_labels(onebranch, False) != run_for_labels(onebranch, True)


testfns = [test_unsets_trace, test_is_stable, test_detects_branches]


@pytest.mark.parametrize('f', testfns, ids=[f.__name__ for f in testfns])
def test_can_be_nested(f):
    begin()
    f()
    collect()


@pytest.mark.parametrize('f', testfns, ids=[f.__name__ for f in testfns])
def test_can_be_nested_arbitrarily(f):
    begin()
    begin()
    f()
    collect()
    collect()


def test_subsumes_child_labels():
    begin()
    a = run_for_labels(onebranch, False)
    b = run_for_labels(onebranch, True)
    assert a != b
    c = collect()
    assert a.contained_in(c)
    assert b.contained_in(c)


def twobranch(x, y):
    if x:
        if y:
            return 1
        else:
            return 2
    elif y:
        return 3
    else:
        return 4


def test_containment():
    bits = [
        run_for_labels(twobranch, u, v)
        for u in [False, True]
        for v in [False, True]
    ]

    for x in bits:
        for y in bits:
            if x is y:
                assert x.contained_in(y)
            else:
                assert not x.contained_in(y)


def loopy(n):
    for i in range(n):
        pass


def test_can_distinguish_number_of_times_through_a_loop():
    loops = [
        run_for_labels(loopy, 0),
        run_for_labels(loopy, 1),
        run_for_labels(loopy, 2),
        run_for_labels(loopy, 3),
        run_for_labels(loopy, 10),
        run_for_labels(loopy, 50),
        run_for_labels(loopy, 100),
    ]
    for i in range(len(loops) - 1):
        print(i)
        assert loops[i] != loops[i+1]
        assert not loops[i + 1].contained_in(loops[i])


def test_can_always_build_native_in_test_env():
    pure_forced = (
        os.getenv('GLASSBOX_FORCE_PURE') == 'true' or
        platform.python_implementation() != 'CPython'
    )
    from glassbox import native
    assert native == (not pure_forced)


def resetthenbranch(x):
    sys.settrace(sys.gettrace())
    return onebranch(x)


def test_suspending_and_resuming_coverage_does_not_break_tracking():
    assert run_for_labels(resetthenbranch, False) != \
        run_for_labels(resetthenbranch, True)
