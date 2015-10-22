import os

__all__ = ['native', '_begin', '_collect', 'merge_arrays', 'array_contained']

native = False

if os.getenv('GLASSBOX_FORCE_PURE') != 'true':
    try:
        from glassbox.extension import _begin, _collect, merge_arrays, \
            array_contained, merge_into
        native = True
    except ImportError:
        pass

if not native:
    from glassbox.pure import (  # noqa
        _begin, _collect, merge_arrays, array_contained, merge_into)
