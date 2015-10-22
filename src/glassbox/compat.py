import sys

if sys.version_info[0] == 2:
    _range = xrange
else:
    _range = range
