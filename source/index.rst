Welcome to Glassbox's documentation!
====================================

Glassbox is a small library for introspecting program state to detect novel
program executions when running tests. It's mostly based on American Fuzzy Lop's
branch detection algorithm.

Its main interesting feature is that it is extremely fast. Programs running under
Glassbox should generally not see more than 10-30% of a slowdown when running on
CPython (on pypy there is currently a significantly more substantial slow down
because tracing can prevent the JIT from working well).

.. automodule:: glassbox
  :members: begin, collect, Record, NoveltyDetector


The intended usage pattern is something along the lines of:

.. code:: python

  def interesting_values(values, run_test):
      detector = NoveltyDetector()
      for value in my_values():
          begin()
          run_test(value)
          record = collect()
          if detector.novel(record):
              yield value

This takes a set of values and prunes it down to the subset which produced a behaviour
not in the previously seen ones.

You could also do something like this:

.. code:: python

  def interesting_values(values, run_test):
      seen = {}
      for value in my_values():
          begin()
          run_test(value)
          record = collect()
          for label in record.labels:
              if label not in seen or better(value, seen[label]):
                  seen[label] = value
      return seen

This maintains a current "best" value that exhibits each label.

Note: It would not be a problem if run_test itself used the glassbox API. As long as
begin/collect calls are kept balanced, it is perfectly safe to nest them.

Warning: Glassbox is not currently thread safe. Your results will be very confusing
if you try to use it in threaded code. In the long-term it will probably simply
refuse to run on more than one thread, but right now it will just break weirdly.
