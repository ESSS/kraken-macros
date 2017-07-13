import mock
from simplewidgets.observable.observable import Observable



def test_observable():
    observer_mock = mock.Mock()

    def observer():
        observer_mock()

    observable = Observable()
    observable.attach(observer)
    observable.notify()
    observer_mock.assert_any_call()
    observable.detach(observer)
    observable.notify()
    observer_mock.assert_called_once_with()

