import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt
import datetime as dt
import pandas as pd
from item import Item

class MainWindow(widgets.QWidget):
    STOCK_FILEPATH = "stock.csv"    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        #load the stock csv file
        self.stock = pd.read_csv(self.STOCK_FILEPATH)
        self.stock = self.stock.set_index('item_num')
        print(self.stock)
        
        #top bar title
        self.setWindowTitle("Stock Control")
    
        #Set the main layout for the app
        topLayout = widgets.QVBoxLayout()
        self.setLayout(topLayout)

        topLayout.addWidget(widgets.QLabel("<b>Add an order</b>"))

        #Add the order adding form
        top_form = self.create_top_form()      
        topLayout.addLayout(top_form)
        
        self.itemLayout = widgets.QVBoxLayout()
        
        #add the first item form
        self.items = [Item(1)]
        self.items[0].get_item_signal.connect(self.get_item)
        self.itemLayout.addLayout(self.items[0].layout)
        
        topLayout.addLayout(self.itemLayout)
        
        #Add a commit button
        commit_button = widgets.QPushButton("Done")
        commit_button.clicked.connect(self.order_done)
        commit_button.setFocusPolicy(Qt.ClickFocus)
        topLayout.addWidget(commit_button)
        
    def create_top_form(self):
        form = widgets.QFormLayout()
        
        #date input
        self.dateEdit = widgets.QLineEdit()
        form.addRow(widgets.QLabel("Date"), self.dateEdit)
        
        #postcode input
        self.postcodeEdit = widgets.QLineEdit()
        form.addRow(widgets.QLabel("Postcode"), self.postcodeEdit)
        
        return form
        
    def get_item(self, edit_num, item_num):
        try:
            item = self.stock.loc[item_num]
            description = '{0} \nPrice: £{1:.2f}'.format(item.loc['description'], item.loc['price'])
        except KeyError:
            description = 'Not found'
        
        #Set the text in the item's description
        self.items[edit_num].set_description(description)
        
        #Add the next item input to the form if it is full
        if len(self.items) == edit_num+1:
            self.items.append(Item(edit_num+2))
            self.items[-1].get_item_signal.connect(self.get_item)
            self.itemLayout.addLayout(self.items[-1].layout)
        
    
    def order_done(self):
        for item in self.items:
            print(item.item_number)
    