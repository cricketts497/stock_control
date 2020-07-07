import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
import datetime as dt
import pandas as pd
from item import Item

class MainWindow(widgets.QWidget):
    STOCK_FILEPATH = "stock.csv" # path to the csv file containing the stock details
    EBAY_CUT = 0.1 # proportion of the order taken by ebay
    PAYPAL_PERCENT_CUT = 0.029 # proportion of the order taken by paypal
    PAYPAL_PER_ORDER_ABSOLUTE_CUT = 0.3 # absolute amount in gbp taken by paypal per order
    EBAY_INTERNATIONAL_PROGRAMME_POSTCODES = ["WS13 8UR", "WS138UR"]
    POSTAGE_COST = 0.88 # default absolute gbp cost of postage per order
    PACKING_COST = 0.09 # default absolute gbp cost of packing per order
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # #load the stock csv file
        # self.stock = pd.read_csv(self.STOCK_FILEPATH)
        # self.stock = self.stock.set_index('item_num')
        # print(self.stock)
        
        #if the order is international, we don't set the paypal default
        self.international_order = False
        
        #top bar title
        self.setWindowTitle("Stock Control")
    
        #Set the main layout for the app
        self.topLayout = widgets.QVBoxLayout()
        self.setLayout(self.topLayout)

        self.topLayout.addWidget(widgets.QLabel("<b>Add an order</b>"))

        #Add the order adding form
        self.top_form = self.create_top_form()      
        self.topLayout.addLayout(self.top_form)
        
        #add the first item form
        self.itemLayout = widgets.QVBoxLayout()
        
        self.items = [Item(1)]
        self.items[0].get_item_signal.connect(self.get_item)
        self.itemLayout.addLayout(self.items[0].layout)
        
        self.topLayout.addLayout(self.itemLayout)
        
        #Add a commit button
        commit_button = widgets.QPushButton("Done")
        commit_button.clicked.connect(self.order_done)
        commit_button.setFocusPolicy(Qt.ClickFocus)
        self.topLayout.addWidget(commit_button)
        
    def create_top_form(self):
        form = widgets.QFormLayout()
        
        #date input
        today = dt.date.today()
        yesterday = dt.date(today.year,  today.month, today.day-1 )
        self.dateEdit = widgets.QLineEdit("{:%d/%m/%Y}".format(yesterday))
        form.addRow(widgets.QLabel("Date"), self.dateEdit)
        
        #postcode input
        self.postcodeEdit = widgets.QLineEdit()
        self.postcodeEdit.editingFinished.connect(self.check_postcode)
        form.addRow(widgets.QLabel("Postcode"), self.postcodeEdit)
        
        #order amount input
        cost_val = QDoubleValidator(0,999999,2)
        self.orderAmountEdit = widgets.QLineEdit()
        self.orderAmountEdit.setValidator(cost_val)
        self.orderAmountEdit.editingFinished.connect(self.set_outlays)
        form.addRow(widgets.QLabel("Total amount, £"), self.orderAmountEdit)
        
        #ebay cut
        self.ebayCutEdit = widgets.QLineEdit()
        self.ebayCutEdit.setValidator(cost_val)
        form.addRow(widgets.QLabel("Ebay cut, £"), self.ebayCutEdit)
        
        #paypal cut
        self.paypalCutEdit = widgets.QLineEdit()
        self.paypalCutEdit.setValidator(cost_val)
        form.addRow(widgets.QLabel("Paypal cut, £"), self.paypalCutEdit)
        
        #Postage and packing
        post_and_pack_cost_default = self.POSTAGE_COST + self.PACKING_COST
        self.ppEdit = widgets.QLineEdit("{:.2f}".format(post_and_pack_cost_default))
        self.ppEdit.setValidator(cost_val)
        form.addRow(widgets.QLabel("P&P cost, £"), self.ppEdit)
        
        return form
        

        
    def check_postcode(self):
        """
        Change the text in the postcode to upper case
        Check if sending international by looking if the postcode is in the ebay international programme list of postcodes
        SLOT connected to self.postcodeEdit.editingFinished() SIGNAL        
        """
        postcode = self.postcodeEdit.text()
        
        #change to all upper case
        postcode = str.upper(postcode)
        
        #check if sending to ebay international program address
        if postcode in self.EBAY_INTERNATIONAL_PROGRAMME_POSTCODES:
            self.international_order = True
            self.show_international_order_message()
        else:
            self.international_order = False
        
        self.postcodeEdit.setText(postcode)
        
    def show_international_order_message(self):
        #Message box pop-up informing this appears to be an international order
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Information)
        msg.setText("International order")
        msg.setInformativeText("From the postcode it appears this order is going to the Ebay international programme address, so the paypal cut will not be set automatically, please set this manually.")
        msg.setWindowTitle("International order")
        msg.setStandardButtons(widgets.QMessageBox.Ok)
        msg.exec_()
        
    def set_outlays(self):
        """
        Set default values for the order cuts taken by Ebay and Paypal based on the order amount
        SLOT connected to self.orderAmountEdit.editingFinished() SIGNAL
        """
        try:
            order_amount = float(self.orderAmountEdit.text())
        except ValueError:
            order_amount = 0
        
        #set the ebay cut
        ebay_cut = order_amount * self.EBAY_CUT
        self.ebayCutEdit.setText('{:.2f}'.format(ebay_cut))
        
        #set the default paypal cut
        if not self.international_order:
            paypal_cut = order_amount * self.PAYPAL_PERCENT_CUT + self.PAYPAL_PER_ORDER_ABSOLUTE_CUT
            self.paypalCutEdit.setText('{:.2f}'.format(paypal_cut))
        
            
    def get_item(self, edit_num, item_num):
        """
        Get the item series from the dataframe, then set the Item class's item object via Item.set_item()
        Add another item input to the form if this is the last
        SLOT connected to item objects Item.get_item_signal() SIGNAL
        
        Arguments:
            edit_num: int, the zero-indexed index of the form item
            item_num: str, the alpha-numeric unique identifier of the item to be sold in the self.STOCK_FILEPATH database
        """
        item = self.get_item_from_df(item_num)
        
        #Set the item's item pandas series containing the description, price, stock etc
        self.items[edit_num].set_item(item)
        
        #Add the next item input to the form if it is full
        if len(self.items) == edit_num+1 and len(item) > 0:
            self.items.append(Item(edit_num+2))
            self.items[-1].get_item_signal.connect(self.get_item)
            self.itemLayout.addLayout(self.items[-1].layout)
            
    def get_item_from_df(self, item_num):
        """
        Load the stock csv file and look for the item with a given ID number
        
        Arguments:
            item_num: str, the alpha-numeric unique identifier of the item to be sold in the self.STOCK_FILEPATH database
        """
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock = stock.set_index('item_id')
    
        try:
            item = stock.loc[item_num]
        except KeyError:
            item = pd.Series()
            
        return item
        
    
    def order_done(self):
        """
        Apply the order details to the stock csv file
        SLOT connected to commit_button.clicked() SIGNAL in __init__()
        """
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock = stock.set_index('item_id')
        
        order_ok = False
        for item in self.items:
            if item.item_id != item.NO_ITEM:#item ID has been input
                #check the quantity
                try:
                    quantity = int(item.quantityEdit.text())
                except ValueError:
                    order_ok = False
                    break
                    
                #check for the index
                try:
                    stock.loc[item.item_id, 'stock']
                except KeyError:
                    order_ok = False
                    break
                
                #check the requested quantity is available
                if quantity > stock.loc[item.item_id, 'stock']:
                    item.show_not_enough_stock_message()
                    order_ok = False
                    break
                elif quantity == 0:
                    order_ok = False
                    break

                order_ok = True
        
        msg = widgets.QMessageBox()
        if order_ok:
            for item in self.items:
                if item.item_id != item.NO_ITEM:#item ID has been input
                
                    # deduct the quantity from the stock line
                    quantity = int(item.quantityEdit.text())
                    stock.loc[item.item_id, 'stock'] -= quantity
                        
            print(stock)
            
            #Message box pop-up asking if you want to do another order
            msg.setIcon(widgets.QMessageBox.Question)
            msg.setText("Success!")
            msg.setInformativeText("The order has been added and the stock has been deducted from the database. \n\nAdd another?")
            msg.setWindowTitle("Order added")
            msg.setStandardButtons(widgets.QMessageBox.Yes | widgets.QMessageBox.No)
            msg.setEscapeButton(widgets.QMessageBox.No)
            
            msg.buttonClicked.connect(self.new_order)
        else:
            #Message box pop-up asking if you want to do another order
            msg.setIcon(widgets.QMessageBox.Information)
            msg.setText("No items added")
            msg.setInformativeText("Problems were found in the form")
            msg.setWindowTitle("No items added")
            msg.setStandardButtons(widgets.QMessageBox.Ok)
            
        msg.exec_()

    def new_order(self, buttonPressed):
        """
        Clear the form with self.clear_form() if the user presses 'yes' to adding another order
        
        Arguments:
            buttonPressed: The button pressed in the 'Order added' message box
        """
        if buttonPressed.text() == "&Yes":
            self.clear_form()
            
    def clear_form(self):
        """
        Removes any inputs to the form and returns it to the default state
        run conditionally on 'yes' button being clicked in the order complete message box, in self.new_order()
        """
        print("Clearing form")
        
        #date edit
        today = dt.date.today()
        yesterday = dt.date(today.year,today.month,today.day-1)
        self.dateEdit.setText("{:%d/%m/%Y}".format(yesterday))
        
        self.postcodeEdit.setText("")
        self.orderAmountEdit.setText("")
        self.ebayCutEdit.setText("")
        self.paypalCutEdit.setText("")
        
        self.ppEdit.setText("{:.2f}".format(self.POSTAGE_COST+self.PACKING_COST))
        
        #items
        for item in self.items:
            item.clear_form()
        
        
    