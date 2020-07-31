import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIntValidator
import pandas as pd
import numpy as np

class SearchTable(widgets.QWidget):
    LOW_STOCK_LIMIT = 15 # limit for including in low stock get
    NUM_ROWS = 500 # the number of rows in the table, note: this doesn't affect what is saved (as this is taken from self.frame), just what is shown in the table
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
        self.table = widgets.QTableWidget(self.NUM_ROWS,5)
        self.table.setHorizontalHeaderItem(0, widgets.QTableWidgetItem("Item ID"))
        self.table.setHorizontalHeaderItem(1, widgets.QTableWidgetItem("Manufacturer"))
        self.table.setHorizontalHeaderItem(2, widgets.QTableWidgetItem("Category"))
        self.table.setHorizontalHeaderItem(3, widgets.QTableWidgetItem("Stock"))
        self.table.setHorizontalHeaderItem(4, widgets.QTableWidgetItem("Description"))
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
        """
        Load the stock database using the filepath defined in self.__init__() from parent
        """
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock.item_id = stock.item_id.astype(str)
        stock.item_id = stock.item_id.apply(str.upper)
        stock = stock.set_index('item_id')
        
        return stock
        
    def search(self):
        """
        Search for a number of terms separated by spaces
        uses the pandas series.str.contains() function
        fills the table with the returned values
        
        SLOT connected to self.searchEdit.editingFinished() SIGNAL in self.__init__()
        """
        stock = self.load_stock_database()
        
        term = self.searchEdit.text()
        
        terms = term.split(' ')
        
        output = pd.DataFrame()
        for t in terms:
            stock['term_in'] = stock.index.str.contains(t, na=False, case=False)
            output = output.append(stock[stock.term_in == True])
            for col in stock.columns:
                try:
                    stock['term_in'] = stock[col].str.contains(t, na=False, case=False)
                except AttributeError:
                    continue
                output = output.append(stock[stock.term_in == True])
        output = output.drop_duplicates()
        output = output.drop('term_in', axis=1)
        
        self.populate_table(output)
        
    def get_low_stock(self):
        """
        Fill the table with items with stock less than self.LOW_STOCK_LIMIT
        SLOT connected to lowStockButton.clicked() SIGNAL in self.__init__()
        """
        stock = self.load_stock_database()
        
        stock = stock[stock.stock < self.LOW_STOCK_LIMIT]
        
        self.populate_table(stock)

    def populate_table(self, frame):
        """
        Fill the self.table QTableWidget with data
        
        Arguments:
            frame: pd.DataFrame, the data to fill the table with, containing keys 'manufacturer', 'category' and 'stock'
        """
        frame = frame.replace(np.nan, '') # empty cells for np.nan in the dataframe
        self.frame = frame
        self.table.clearContents() # empty the table data but not the headers
        for index, row in enumerate(frame.iterrows()):
            self.table.setItem(index,0,widgets.QTableWidgetItem(row[0]))
            self.table.setItem(index,1,widgets.QTableWidgetItem(str(row[1]['manufacturer'])))
            self.table.setItem(index,2,widgets.QTableWidgetItem(str(row[1]['category'])))
            self.table.setItem(index,3,widgets.QTableWidgetItem(str(row[1]['stock'])))
            self.table.setItem(index,4,widgets.QTableWidgetItem(str(row[1]['description'])))
        
        
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
        
        
        
        
        
        