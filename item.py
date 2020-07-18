import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIntValidator
import pandas as pd

class Item(QObject):
    NO_ITEM = ""
    NO_MANUFACTURER = ""
    NO_CATEGORY = ""
    BOX_HEIGHT = 100
    NEW_ITEM_BOX_HEIGHT = 200

    get_item_signal = Signal(int, str)
    def __init__(self, item_number, stock_item):
        """
        Arguments:
            item_number: the item index in the list, starting from 1
            stock_item: bool, is this for the stock input form?
        """
        super().__init__()
        
        #Zero indexed item number
        self.item_index = item_number-1
        
        self.stock_item = stock_item
        
        self.form_expanded = False
        
        #set the default info about the item
        self.item_id = self.NO_ITEM
        # self.quantity = self.NO_QUANTITY
        self.item = pd.Series()
        
        #line edits only visible when putting new items into the stock database
        self.manufacturerEdit = widgets.QLineEdit()
        self.categoryEdit = widgets.QLineEdit()
        self.manufacturerEdit.editingFinished.connect(self.setLower)
        self.categoryEdit.editingFinished.connect(self.setLower)
        
        #GUI
        self.widget = widgets.QGroupBox("Item {}".format(item_number))
        self.widget.setFixedHeight(self.BOX_HEIGHT)
        layout = widgets.QHBoxLayout()
        self.widget.setLayout(layout)
        
        self.form = widgets.QFormLayout()
        
        onlyInt = QIntValidator(0,999999)
        
        #item id
        self.item_id_edit = widgets.QLineEdit()
        #when the editing is finished, emit a signal from self to get the parent to find and set the item
        self.item_id_edit.editingFinished.connect(self.get_item)
        
        #quantity
        self.quantityEdit = widgets.QLineEdit()
        self.quantityEdit.setValidator(onlyInt)
        self.quantityEdit.editingFinished.connect(self.check_stock)
        
        self.form.addRow(widgets.QLabel("Item ID"), self.item_id_edit)
        self.form.addRow(widgets.QLabel("Quantity"), self.quantityEdit)
        
        layout.addLayout(self.form)
        
        self.describe_label = widgets.QLabel()
        layout.addWidget(self.describe_label)
        
    def setLower(self):
        """
        Set the text in the manufacturer and category inputs to lower case
        """
        cat = str.lower(self.categoryEdit.text())
        man = str.lower(self.manufacturerEdit.text())
        
        self.categoryEdit.setText(cat)
        self.manufacturerEdit.setText(man)
        
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
            # description = '{0} \nPrice: £{1:.2f}'.format(item.loc['description'], item.loc['price'])
            description = '{0}, {1}'.format(item.loc['manufacturer'], item.loc['category'])
        elif self.item_id == self.NO_ITEM:
            description = ''
        else:
            #add options for adding a new item
            description = 'Not found'
            
            if self.stock_item:
                self.set_new_item()
            
        self.describe_label.setText(description)
    
    def set_new_item(self):
        """
        Expand the form to allow the input of a new item to the stock database
        """
        if not self.form_expanded:
            self.form.addRow(widgets.QLabel('Manufacturer'), self.manufacturerEdit)
            self.form.addRow(widgets.QLabel('Category'), self.categoryEdit)
            self.widget.setFixedHeight(self.NEW_ITEM_BOX_HEIGHT)
            self.form_expanded = True
   
    
    def check_stock(self):
        """
        Check there is enough stock available to fulfill the order
        
        If not, open a message window warning that there is not enough stock
        """
        quantity = int(self.quantityEdit.text())
                
        if len(self.item) > 0 and not self.stock_item:#item pd.Series() is set and not adding stock
            if quantity > self.item.loc['stock']:
                self.show_not_enough_stock_message(quantity)
            
    def show_not_enough_stock_message(self, quantity):
        """
        Show a message window that not enough of the item is available in stock
        Only for order items
        
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
        
        self.manufacturerEdit.setText(self.NO_MANUFACTURER)
        self.categoryEdit.setText(self.NO_CATEGORY)
        
        self.describe_label.setText("")
        
        
        
        
        