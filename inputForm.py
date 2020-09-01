import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import Qt
# from PyQt5.QtGui import QIntValidator
import pandas as pd
# import numpy as np
from item import Item

class InputForm(widgets.QWidget):
    undo_signal = Signal()
    commit_signal = Signal()
    def __init__(self, stock_filepath, stock_input_form):
        super().__init__()
        
        self.STOCK_FILEPATH = stock_filepath
        self.STOCK_INPUT_FORM = stock_input_form
        
        #Main layout
        self.layout = widgets.QVBoxLayout()
        self.setLayout(self.layout)
        
        #undo button
        undo_button = widgets.QPushButton("Undo")
        undo_button.clicked.connect(self.emit_undo_signal)
        undo_button.setFocusPolicy(Qt.ClickFocus)
        self.layout.addWidget(undo_button)

    def addItemLayout(self):
        self.itemLayout = widgets.QVBoxLayout()
        
        self.items = [Item(1, self.STOCK_INPUT_FORM)]
        self.items[0].get_item_signal.connect(self.fill_item)
        self.itemLayout.addWidget(self.items[0].widget)
        
        self.layout.addLayout(self.itemLayout)
        self.layout.addStretch(1)
        
    def addCommitButton(self, text="Done"):
        commit_button = widgets.QPushButton(text)
        commit_button.clicked.connect(self.emit_commit_signal)
        commit_button.setFocusPolicy(Qt.ClickFocus)
        self.layout.addWidget(commit_button)
        
    def load_stock_database(self):
        """
        Load the stock database using the filepath defined in self.__init__() from parent
        """
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock.item_id = stock.item_id.astype(str)
        stock.item_id = stock.item_id.apply(str.upper)
        stock = stock.set_index('item_id')
        
        return stock
        
    def fill_item(self, edit_num, item_id):
        """
        Find the item in the stock database with the given item_id
        """
        stock = self.load_stock_database()
    
        try:
            item = stock.loc[item_id]
        except KeyError:
            item = pd.Series()
            
        #more than one item with the same id
        if type(item) == pd.DataFrame:
            self.show_not_unique_message(item_id)
            item = item.iloc[0]
            
        self.items[edit_num].set_item(item)
        
        if len(self.items) == edit_num+1:
            if (self.STOCK_INPUT_FORM and self.items[edit_num].item_id != self.items[edit_num].NO_ITEM) or (not self.STOCK_INPUT_FORM and len(item) > 0):
                self.items.append(Item(edit_num+2, self.STOCK_INPUT_FORM))
                self.items[-1].get_item_signal.connect(self.fill_item)
                self.itemLayout.addWidget(self.items[-1].widget)
        
        
    def show_not_unique_message(self, item_id):
        """
        More than one item was found in the database with the same ID
        
        Arguments:
            item_ID: str, the ID with which multiple items were found
        """
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Warning)
        msg.setText("ID not unique")
        msg.setInformativeText("More than one item was found in the stock database with the id: {}.\nThe form cannot be submitted.".format(item_id))
        msg.setWindowTitle("ID not unique")
        msg.setStandardButtons(widgets.QMessageBox.Ok)
        msg.exec_()
        
    def clear_items(self):
        for item in self.items:
            item.clear_form()
    
    def emit_undo_signal(self):
        self.undo_signal.emit()
        
    def emit_commit_signal(self):
        self.commit_signal.emit()
        