from __future__ import unicode_literals
from collections import namedtuple
import warnings
from simplewidgets.PyQt import QtGui, QtCore
from simplewidgets.PyQt.QtCore import Qt
from simplewidgets.PyQt.QtWidgets import QDialogButtonBox, QSizePolicy
from PyQt5 import QtWidgets
from simplewidgets.fields import BaseInputField, BaseWidgetControl


# noinspection PyAttributeOutsideInit
class BaseSimpleWidget(object):

    NUM_LAYOUT_COLS = 2

    def setup_ui(self):
        fields_order = []
        #TODO: create Fields declared in base classes
        for attr_name, value in self.__class__.__dict__.items():
            if isinstance(value, BaseWidgetControl):
                fields_order.append((value.order, attr_name, value))
                self._check_base_attributes_override(attr_name)
        # Preserve the order in which Fields were declared
        self._sorted_field_names = []
        self._layout = QtWidgets.QGridLayout(self)
        self._field_widgets = {}
        for _, field_name, field in sorted(fields_order):
            setattr(self, field_name, field.create_copy(self))
            self._create_field_line(field_name)
            if isinstance(field, BaseInputField):
                self._sorted_field_names.append(field_name)
        self._data_type = namedtuple("SimpleData", self._sorted_field_names)


    def _get_field(self, field_name):
        """
        Get the Field object for the given name.

        :param field_name: str
        :rtype: BaseInputField
        """
        return getattr(self, field_name)


    def fields(self):
        return [self._get_field(field_name) for field_name in self._sorted_field_names]


    def _create_field_line(self, field_name):
        field = self._get_field(field_name)
        row = self._layout.rowCount() + 1
        widget = field.create_widget(self)
        if hasattr(field, "label") and field.label:
            label = QtWidgets.QLabel(self)
            label.setText(field.label)
            label.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
            label.setBuddy(widget)
            setattr(self, "{0}_label".format(field_name), label)
            self._layout.addWidget(label, row, 0)
            self._layout.addWidget(widget, row, 1)
        else:
            self._layout.addWidget(widget, row, 0, 2, 1)
        setattr(self, "{0}_widget".format(field_name), widget)
        self._field_widgets[field_name] = widget


    def get_data(self):
        """
        Returns widget fields value.

        :rtype: namedtuple
        """
        field_values = {}
        for field_name in self._sorted_field_names:
            field = self._get_field(field_name)
            if isinstance(field, BaseInputField):
                field_values[field_name] = field.get_value_from()
        return self._data_type(**field_values)


    def update_view(self):
        for field in self.fields():
            field.update_view()


    def get_field_widget(self, attr_name):
        #TODO: fix protected access
        return self._get_field(attr_name).widget


    def bind_data(self, field_name, instance, attr_name):
        self._get_field(field_name).bind_attribute(instance, attr_name)


    def _check_base_attributes_override(self, attr_name):
        """
        Check if a Field declaration is overriding some base class attribute (It's common to declare a `size`
        field which override `QWidget.size` function)

        :param attr_name: the field name
        """
        for base_class in self.__class__.__bases__:
            if hasattr(base_class, attr_name):
                warnings.warn("Field {0} is overwriting attribute from {1}".format(attr_name, base_class.__name__))


class SimpleWidget(BaseSimpleWidget, QtWidgets.QWidget):


    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        BaseSimpleWidget.setup_ui(self)


class SimpleDialog(BaseSimpleWidget, QtWidgets.QDialog):


    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        BaseSimpleWidget.setup_ui(self)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self._layout.addWidget(self.button_box, self._layout.rowCount() + 1, 0, 1, self.NUM_LAYOUT_COLS)
        self.connect(self.button_box, QtCore.pyqtSignal("accepted()"), self.accept)
        self.connect(self.button_box, QtCore.pyqtSignal("rejected()"), self.reject)


    def exec_accepted(self):
        return self.exec_() == QtWidgets.QDialog.Accepted
