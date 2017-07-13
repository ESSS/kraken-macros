try:
    from PySide.QtGui import *
except ImportError:
    try:
        from PyQt5.QtGui import *
    except ImportError:
        raise RuntimeError("No Python-Qt bindings found")
