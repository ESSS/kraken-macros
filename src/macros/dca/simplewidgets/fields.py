from __future__ import unicode_literals
import weakref

import locale

from simplewidgets.PyQt.QtCore import pyqtSignal
from simplewidgets.PyQt.QtGui import QIntValidator, QDoubleValidator
from simplewidgets.PyQt.QtWidgets import QLineEdit, QComboBox, QGroupBox, QVBoxLayout, QPushButton
from simplewidgets.observable.observable import Observable
from simplewidgets.observable.weakmethod import WeakMethod


class BaseWidgetControl(object):
    # _coubter is a global counter so UI fields could be created in the same order of their declarations
    # ref: http://stackoverflow.com/a/11317693/885117
    _counter = 0

    def __init__(self):
        self.order = self._counter
        BaseWidgetControl._counter += 1
        self.simple_widget = None
        self.widget = None


    def create_widget(self, parent):
        """
        Create the widget for this Field.

        :param QWidget parent: the parent widget

        :rtype: QWidget
        """
        raise NotImplementedError("create_widget")


    def create_copy(self, simple_widget):
        """
        BaseWidgetControl are always defined in the class level. This method is called to create a unique instance of
        the BaseInputField to each instance of a SimpleWidget.

        :param SimpleWidget simple_widget: the simple widget instance

        :rtype: BaseInputField
        """
        import copy

        field_instance = copy.copy(self)
        field_instance.simple_widget = weakref.proxy(simple_widget)
        return field_instance


class BaseInputField(BaseWidgetControl):

    def __init__(self, initial="", label=""):
        super(BaseInputField, self).__init__()
        self.label = label
        self.initial = initial
        self._bindings = weakref.WeakKeyDictionary()


    def update_view(self):
        """
        Public method to update field UI based on data.
        """
        self.widget.blockpyqtSignals(True)
        try:
            self._update_view()
        finally:
            self.widget.blockpyqtSignals(False)


    def _update_view(self):
        """
        Should be overridden to specify field UI updates.
        """
        raise NotImplementedError("_update_view")


    def get_value_from(self):
        """
        Get a data value from the field widget.
        """
        raise NotImplementedError("get_value_from")


    def bind_attribute(self, instance, attr_name):
        self._bindings[instance] = attr_name


class LineTextField(BaseInputField):
    def __init__(self, initial="", label=""):
        super(LineTextField, self).__init__(initial, label)
        self.on_editing_finished = Observable()


    def create_widget(self, parent):
        assert self.widget is None, "create_widget() must be called only once"
        self.widget = QLineEdit(parent)
        self.set_value(self.initial)
        self.widget.connect(self.widget, pyqtSignal("editingFinished ()"), self._slot_editing_finished)
        return self.widget


    def set_value(self, value):
        self.widget.setText(value)


    def _update_view(self):
        pass


    def get_value_from(self):
        return self.widget.text()


    def _slot_editing_finished(self):
        for instance, attr_name in self._bindings.items():
            setattr(instance, attr_name, self.get_value_from())
        self.on_editing_finished.notify()


class NumberField(LineTextField):


    _validator = QDoubleValidator

    def __init__(self, initial="", label="", display_format="%5g"):
        super(NumberField, self).__init__(initial, label)
        self._format = display_format


    def create_widget(self, parent):
        super(NumberField, self).create_widget(parent)
        self.widget.setValidator(self._validator(self.widget))
        return self.widget


    def set_value(self, value):
        self.widget.setText(locale.format_string(self._format, value))


    def _update_view(self):
        pass


    def get_value_from(self):
        return locale.atof(self.widget.text())


class IntField(NumberField):


    _validator = QIntValidator

    def __init__(self, initial="", label=""):
        super(IntField, self).__init__(initial, label, "%d")


    def _update_view(self):
        pass


    def get_value_from(self):
        return locale.atoi(self.widget.text())


class ChoiceField(BaseInputField):
    """
    A SimpleWidget field that displays a Combo with the given choices
    """


    def __init__(self, choices, initial="", label=""):
        super(ChoiceField, self).__init__(initial, label)
        self._choices = choices
        self.on_current_index_changed = Observable()


    def create_widget(self, parent):
        self.widget = QComboBox(parent)
        self.widget.connect(self.widget, pyqtSignal("currentIndexChanged(int)"), self._slot_current_index_changed)
        self.update_view()
        return self.widget


    def _update_view(self):
        choices = self._get_choices()
        self.widget.clear()
        self.widget.addItems([choice[1] for choice in choices])
        if self.initial:
            values = [choice[0] for choice in choices]
            self.widget.setCurrentIndex(values.index(self.initial))


    def get_value_from(self):
        current_text = self.widget.currentText()
        for choice_value, text in self._get_choices():
            if current_text == text:
                return choice_value


    def _get_choices(self):
        """
        Returns the field choices as a list of tuples (choice_value, choice_text).

        :rtype: list
        """
        if isinstance(self._choices, basestring):
            choices = getattr(self.simple_widget, self._choices)
        else:
            choices = self._choices
        assert isinstance(choices, (list, tuple)), "choices has an invalid type"
        for i, choice in enumerate(choices):
            if not isinstance(choice, (list, tuple)):
                choices[i] = (choice, str(choice))
        return choices


    def _slot_current_index_changed(self, index):
        self.on_current_index_changed.notify(index)


class GroupField(BaseInputField):
    """
    Shows another SimpleWidget inside a Group Box.
    """

    def __init__(self, simple_widget_class, title=""):
        """
        Constructor

        :param type simple_widget_class: a class derived from SimpleWidget

        :param basestring title: the group box title
        """
        super(GroupField, self).__init__()
        self._child_widget_class = simple_widget_class
        self._title = title
        self.child_widget = None


    def create_widget(self, parent):
        widget = QGroupBox(self._title, parent)
        self.child_widget = self._child_widget_class(parent)
        layout = QVBoxLayout()
        layout.setMargin(4)
        layout.addWidget(self.child_widget)
        widget.setLayout(layout)
        return widget


    def get_value_from(self):
        return self.child_widget.get_data()


class Button(BaseWidgetControl):

    def __init__(self, title, slot):
        """
        Constructor

        :param unicode title: the button title

        :param unicode slot: a call

        :return:
        """
        super(Button, self).__init__()
        self._title = title
        self._slot = slot
        self._slot_callable = None


    def create_widget(self, parent):
        widget = QPushButton(self._title, parent)
        if isinstance(self._slot, basestring):
            self._slot_callable = WeakMethod(getattr(parent, self._slot))
        else:
            self._slot_callable = self._slot
        widget.connect(widget, pyqtSignal("clicked()"), self._slot_clicked)
        return widget


    def _slot_clicked(self):
        if isinstance(self._slot_callable, WeakMethod):
            slot = self._slot_callable.ref()
        else:
            slot = self._slot_callable
        slot()