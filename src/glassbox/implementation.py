import os

__all__ = ['native', '_begin', '_collect', 'merge_arrays']

native = False

if os.getenv('GLASSBOX_FORCE_PURE') == 'true':
    from glassbox.pure import _begin, _collect, merge_arrays
else:
    try:
        from glassbox.extension import _begin, _collect, merge_arrays
        native = True
    except ImportError:
        from glassbox.pure import _begin, _collect, merge_arrays
