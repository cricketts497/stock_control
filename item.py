import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIntValidator
import pandas as pd

class Item(QObject):
    NO_ITEM = 0
    get_item_signal = Signal(int, int)
    def __init__(self, item_number):
        super().__init__()
    
        self.item_number = self.NO_ITEM
        self.item = pd.Series()
    
        self.layout = widgets.QHBoxLayout()
        
        form = widgets.QFormLayout()
        
        onlyInt = QIntValidator(0,99999999999)
        
        self.item_number_edit = widgets.QLineEdit()
        self.item_number_edit.setValidator(onlyInt)
        #when the editing is finished, emit a signal from self to get the parent to find and set the item
        self.item_number_edit.editingFinished.connect(self.get_item)
        
        self.quantityEdit = widgets.QLineEdit()
        self.quantityEdit.setValidator(onlyInt)
        
        form.addRow(widgets.QLabel("Item {}".format(item_number)))
        form.addRow(widgets.QLabel("Item number"), self.item_number_edit)
        form.addRow(widgets.QLabel("Quantity"), self.quantityEdit)
        
        self.layout.addLayout(form)
        
        self.describe_label = widgets.QLabel()
        self.layout.addWidget(self.describe_label)
        
        #Zero indexed item number
        self.item_index = item_number-1
        
    def get_item(self):
        try:
            item_number = int(self.item_number_edit.text())
        except ValueError:
            return#if left empty
        self.item_number = item_number
        self.get_item_signal.emit(self.item_index, item_number)
    
    def set_item(self, item):
        self.item = item

        #set the description QLabel
        if len(item) > 0:
            description = '{0} \nPrice: £{1:.2f}'.format(item.loc['description'], item.loc['price'])
        else:
            description = 'Not found'
        self.describe_label.setText(description)
        
        
        
        
        
        
        
        
        
        