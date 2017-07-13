from types import FunctionType
from simplewidgets.observable.weakmethod import WeakMethod


class Observable(object):
    """
    Implementation of Observer pattern based on recipes published at

        * http://code.activestate.com/recipes/131499-observer-pattern/
        * http://en.wikipedia.org/wiki/Observer_pattern

    """



    def __init__(self):
        self._observers = []


    def attach(self, observer):
        if isinstance(observer, FunctionType):
            self._observers.append(observer)
        else:
            self._observers.append(WeakMethod(observer))


    def detach(self, observer):
        for attached in self._observers:
            if isinstance(attached, WeakMethod):
                attached = attached.ref()
            if attached is observer:
                    break
        else:
            raise ValueError("Callable not attached")
        self._observers.remove(attached)


    def notify(self, *args, **kw):
        for observer in self._observers:
            observer(*args, **kw)
