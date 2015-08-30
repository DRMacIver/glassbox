from tracking import begin, collect
import sys
import pytest


@pytest.fixture(autouse=True, scope='function')
def needs_cleanup(request):
    def cleanup():
        sys.settrace(None)
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
