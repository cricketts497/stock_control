import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIntValidator
import pandas as pd

class SearchTable(widgets.QWidget):
    LOW_STOCK_LIMIT = 15 # limit for including in low stock get
    NO_FILENAME = ""
    save_error = Signal(str, PermissionError)
    def __init__(self, stock_filepath):
        super().__init__()
        
        self.STOCK_FILEPATH = stock_filepath
        self.frame = pd.DataFrame()
        
        layout = widgets.QVBoxLayout()
        self.setLayout(layout)
        
        #Create the top bar
        ###
        topBar = widgets.QHBoxLayout()
        topBar.addWidget(widgets.QLabel("Search"))
        self.searchEdit = widgets.QLineEdit()
        self.searchEdit.editingFinished.connect(self.search)
        topBar.addWidget(self.searchEdit)
        
        topBar.addStretch(1)
        
        lowStockButton = widgets.QPushButton("Find low stock items")
        lowStockButton.clicked.connect(self.get_low_stock)
        topBar.addWidget(lowStockButton)
        
        layout.addLayout(topBar)
        ###
        
        #add the table
        ###
        self.table = widgets.QTableWidget(50,4)
        self.table.setHorizontalHeaderItem(0, widgets.QTableWidgetItem("Item ID"))
        self.table.setHorizontalHeaderItem(1, widgets.QTableWidgetItem("Manufacturer"))
        self.table.setHorizontalHeaderItem(2, widgets.QTableWidgetItem("Category"))
        self.table.setHorizontalHeaderItem(3, widgets.QTableWidgetItem("Stock"))
        layout.addWidget(self.table)
        ###
        
        #add the bottom toolbar
        ###
        bottomBar = widgets.QHBoxLayout()
        bottomBar.addStretch(1)
        saveButton = widgets.QPushButton("Save")
        saveButton.clicked.connect(self.save_to_file)
        bottomBar.addWidget(saveButton)
        layout.addLayout(bottomBar)
        ###
        
    def load_stock_database(self):
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock.item_id = stock.item_id.astype(str)
        stock.item_id = stock.item_id.apply(str.upper)
        stock = stock.set_index('item_id')
        
        return stock
        
    def search(self):
        pass
        
    def get_low_stock(self):
        stock = self.load_stock_database()
        
        stock = stock[stock.stock < self.LOW_STOCK_LIMIT]
        
        self.populate_table(stock)

    def populate_table(self, frame):
        self.frame = frame
        for index, row in enumerate(frame.iterrows()):
            self.table.setItem(index,0,widgets.QTableWidgetItem(row[0]))
            self.table.setItem(index,1,widgets.QTableWidgetItem(str(row[1]['manufacturer'])))
            self.table.setItem(index,2,widgets.QTableWidgetItem(str(row[1]['category'])))
            self.table.setItem(index,3,widgets.QTableWidgetItem(str(row[1]['stock'])))
        
        
    def save_to_file(self):
        """
        Save the data contained in the table to a user-named csv file
        """
        if len(self.frame) > 0:
            (name, type) = widgets.QFileDialog.getSaveFileName(self, caption="Save stock data", filter="*.csv")
            
            if name == self.NO_FILENAME:
                return
            
            try:
                self.frame.to_csv(name)
            except PermissionError as err:
                self.save_error.emit(name, err)
        
        
        
        
        
        