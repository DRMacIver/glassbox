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
    result = collect()
    assert sys.gettrace() is None
    return result


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


def test_can_be_nested_arbitrarily():
    base = run_for_labels(onebranch, True)
    begin()
    assert run_for_labels(onebranch, True) == base
    run_for_labels(onebranch, False)
    conclusion = collect()
    assert base != conclusion
    assert base.issubset(conclusion)
    assert run_for_labels(onebranch, False).issubset(conclusion)
