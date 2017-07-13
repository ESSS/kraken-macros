try:
    from PySide.QtWidgets import *
except ImportError:
    try:
        from PyQt5.QtWidgets import *
    except ImportError:
        raise RuntimeError("No Python-Qt bindings found")
