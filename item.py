import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIntValidator
import pandas as pd

class Item(QObject):
    NO_ITEM = ""
    # NO_QUANTITY = 0
    get_item_signal = Signal(int, str)
    def __init__(self, item_number):
        """
        Arguments:
            item_number: the item index in the list, starting from 1
        """
        super().__init__()
        
        #set the default info about the item
        self.item_id = self.NO_ITEM
        # self.quantity = self.NO_QUANTITY
        self.item = pd.Series()
        
        #Zero indexed item number
        self.item_index = item_number-1
    
        #GUI
        self.widget = widgets.QGroupBox("Item {}".format(item_number))
        layout = widgets.QHBoxLayout()
        self.widget.setLayout(layout)
        
        form = widgets.QFormLayout()
        
        onlyInt = QIntValidator(0,99999999999)
        
        #item id
        self.item_id_edit = widgets.QLineEdit()
        # self.item_id_edit.setValidator(onlyInt)
        #when the editing is finished, emit a signal from self to get the parent to find and set the item
        self.item_id_edit.editingFinished.connect(self.get_item)
        
        #quantity
        self.quantityEdit = widgets.QLineEdit()
        self.quantityEdit.setValidator(onlyInt)
        self.quantityEdit.editingFinished.connect(self.check_stock)
        
        # form.addRow(widgets.QLabel("Item {}".format(item_number)))
        form.addRow(widgets.QLabel("Item ID"), self.item_id_edit)
        form.addRow(widgets.QLabel("Quantity"), self.quantityEdit)
        
        layout.addLayout(form)
        
        self.describe_label = widgets.QLabel()
        layout.addWidget(self.describe_label)
        
    def get_item(self):
        """
        Emit a signal to the parent MainWindow to get the item with the given ID from the database
        SLOT connected to self.item_id_edit.editingFinished() SIGNAL
        """
        self.item_id = self.item_id_edit.text()
        
        self.get_item_signal.emit(self.item_index, self.item_id)
    
    def set_item(self, item):
        """
        Run in MainWindow.get_item() after the item pd.Series() has been found in the database
        Sets the description label in the form
        
        Arguments:
            item: pd.Series(), Contains the items attributes, price, stock, description etc.
        """
        self.item = item

        #set the description QLabel
        if len(item) > 0:
            description = '{0} \nPrice: £{1:.2f}'.format(item.loc['description'], item.loc['price'])
        elif self.item_id == self.NO_ITEM:
            description = ''
        else:
            description = 'Not found'
        self.describe_label.setText(description)
        
    def check_stock(self):
        """
        Check there is enough stock available to fulfill the order
        
        If not, open a message window warning that there is not enough stock
        """
        quantity = int(self.quantityEdit.text())
                
        if len(self.item) > 0:#item pd.Series() is set
            if quantity > self.item.loc['stock']:
                self.show_not_enough_stock_message(quantity)
            
    def show_not_enough_stock_message(self, quantity):
        """
        Show a message window that not enough of the item is available in stock
        
        Arguments:
            quantity: the requested quantity of the item
        """
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Warning)
        msg.setText("Not enough stock available")
        msg.setInformativeText("You have requested {0} of item {1} and only {2} are available in stock so the order cannot be fulfilled.".format(quantity, self.item.name, self.item.loc['stock']))
        msg.setWindowTitle("Stock issue")
        msg.setStandardButtons(widgets.QMessageBox.Ok)
        msg.exec_()
            
        
    def clear_form(self):
        """
        Clear all the info and the items from the form
        """
        self.item_id = self.NO_ITEM
        self.item = pd.Series()
        
        self.item_id_edit.setText(self.NO_ITEM)
        self.quantityEdit.setText("")
        self.describe_label.setText("")
        
        
        
        