Welcome to Glassbox's documentation!
====================================

Glassbox is a small library for introspecting program state to detect novel
program executions when running tests. It's mostly based on American Fuzzy Lop's
branch detection algorithm.

Its main interesting feature is that it is extremely fast. Programs running under
Glassbox should generally not see more than 10-20% of a slowdown when running on
CPython (on pypy there is currently a more significant slowdown - code is about 3-5
times slower running with glassbox).

.. automodule:: glassbox
  :members: begin, collect, Record, NoveltyDetector


The intended usage pattern is something along the lines of:

.. code:: python

  def interesting_values(values, run_test):
      detector = Novelty()
      for value in my_values():
          begin()
          run_test(value)
          record = collect()
          if detector.novel(record):
              yield value

This takes a set of values and prunes it down to the subset which produced a behaviour
not in the previously seen ones.

Note: It would not be a problem if run_test itself used the glassbox API. As long as
begin/collect calls are kept balanced, it is perfectly safe to nest them.
