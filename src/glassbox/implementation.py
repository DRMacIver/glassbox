import os

__all__ = ['native', '_begin', '_collect']

native = False

if os.getenv('GLASSBOX_FORCE_PURE') == 'true':
    from glassbox.pure import _begin, _collect
else:
    try:
        from glassbox.extension import _begin, _collect
        native = True
    except ImportError:
        from glassbox.pure import _begin, _collect
