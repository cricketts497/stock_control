import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QDoubleValidator
import datetime as dt
import pandas as pd
from item import Item

class MainWindow(widgets.QTabWidget):
    STOCK_FILEPATH = "stock.csv" # path to the csv file containing the stock details: amounts prices descriptions etc.
    ORDERS_FILEPATH = "orders.csv" # path to the csv file containing the orders: order dates, order amounts etc.
    EBAY_CUT = 0.1 # proportion of the order taken by ebay
    PAYPAL_PERCENT_CUT = 0.029 # proportion of the order taken by paypal
    PAYPAL_PER_ORDER_ABSOLUTE_CUT = 0.3 # absolute amount in gbp taken by paypal per order
    EBAY_INTERNATIONAL_PROGRAMME_POSTCODES = ["WS13 8UR", "WS138UR"] # Postcodes of the ebay international programme address
    POSTAGE_COST = 0.88 # default absolute gbp cost of postage per order
    PACKING_COST = 0.09 # default absolute gbp cost of packing per order
    def __init__(self):
        """
        Initialise the main GUI with the form for the order details, the first item form object and the order commiting button
        """
        super().__init__()

        #if the order is international, we don't set the paypal default
        self.international_order = False
        
        #top bar title
        self.setWindowTitle("Stock Control")
    
        #create the order adding form
        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        orderWidget = widgets.QWidget()
        self.orderLayout = widgets.QVBoxLayout()
        orderWidget.setLayout(self.orderLayout)

        self.addTab(orderWidget, "Add an order")

        #Add the order adding form
        self.top_form = self.create_top_order_form()      
        self.orderLayout.addLayout(self.top_form)
        
        #add the first item form
        self.itemLayout = widgets.QVBoxLayout()
        
        self.items = [Item(1, False)]
        self.items[0].get_item_signal.connect(self.get_order_item)
        self.itemLayout.addWidget(self.items[0].widget)
        
        self.orderLayout.addLayout(self.itemLayout)
        
        self.orderLayout.addStretch(1)
        
        #Add a commit button
        commit_button = widgets.QPushButton("Done")
        commit_button.clicked.connect(self.order_done)
        commit_button.setFocusPolicy(Qt.ClickFocus)
        self.orderLayout.addWidget(commit_button)
        
        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
        #create the stock adding form
        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        stockWidget = widgets.QWidget()
        self.stockLayout = widgets.QVBoxLayout()
        stockWidget.setLayout(self.stockLayout)
        
        self.addTab(stockWidget, "Add new stock")
        
        #Add an item object
        self.stockItemLayout = widgets.QVBoxLayout()
        
        self.stockItems = [Item(1, True)]
        self.stockItems[0].get_item_signal.connect(self.get_stock_item)
        self.stockItemLayout.addWidget(self.stockItems[0].widget)
        
        self.stockLayout.addLayout(self.stockItemLayout)
        
        self.stockLayout.addStretch(1)
        
        #add a commit button
        stock_commit_button = widgets.QPushButton("Done")
        stock_commit_button.clicked.connect(self.stock_done)
        stock_commit_button.setFocusPolicy(Qt.ClickFocus)
        self.stockLayout.addWidget(stock_commit_button)        
        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
    def create_top_order_form(self):
        """
        Create the QFormLayout object containing the static form entries at the top
        Entries: Date, postcode, order amount, ebay amount, paypal amount and the postage and packing amount
        
        Called in self.__init__() above
        
        Returns:
            QFormLayout object
        """
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
        """
        Message box pop-up informing this appears to be an international order
        
        used in self.check_postcode() above
        """
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
        except ValueError:#no value
            order_amount = 0
        
        #set the ebay cut
        ebay_cut = order_amount * self.EBAY_CUT
        self.ebayCutEdit.setText('{:.2f}'.format(ebay_cut))
        
        #set the default paypal cut
        if not self.international_order:
            paypal_cut = order_amount * self.PAYPAL_PERCENT_CUT + self.PAYPAL_PER_ORDER_ABSOLUTE_CUT
            self.paypalCutEdit.setText('{:.2f}'.format(paypal_cut))
        
        
    def get_order_item(self, edit_num, item_id):
        """
        Get the item series from the dataframe, then set the Item class's item object via Item.set_item()
        Add another item input to the form if this is the last
        
        SLOT connected to item objects Item.get_item_signal() SIGNAL for order items
        
        Arguments:
            edit_num: int, the zero-indexed index of the form item
            item_num: str, the alpha-numeric unique identifier of the item to be sold in the self.STOCK_FILEPATH database
        """
        item = self.get_item_from_df(item_id)
        
        #Set the item's item pandas series containing the description, price, stock etc
        self.items[edit_num].set_item(item)
        
        #Add the next item input to the form if it is full
        if len(self.items) == edit_num+1 and len(item) > 0:
            self.items.append(Item(edit_num+2, False))
            self.items[-1].get_item_signal.connect(self.get_order_item)
            self.itemLayout.addWidget(self.items[-1].widget)
                
    def get_stock_item(self, edit_num, item_id):
        """
        Get the item series from the dataframe, then set the Item class's item object via Item.set_item()
        Add another item input to the form if this is the last
        
        SLOT connected to item objects Item.get_item_signal() SIGNAL for stock items
        
        Arguments:
            edit_num: int, the zero-indexed index of the form item
            item_num: str, the alpha-numeric unique identifier of the item to be sold in the self.STOCK_FILEPATH database
        """
    
        item = self.get_item_from_df(item_id)   
        
        #Set the item's item pandas series containing the description, price, stock etc
        self.stockItems[edit_num].set_item(item)
        
        #Add the next item input to the form if it is full
        if len(self.stockItems) == edit_num+1 and len(item) > 0:
            self.stockItems.append(Item(edit_num+2, True))
            self.stockItems[-1].get_item_signal.connect(self.get_stock_item)
            self.stockItemLayout.addWidget(self.stockItems[-1].widget)
        
            
    def get_item_from_df(self, item_ID):
        """
        Load the stock csv file and look for the item with a given ID number
        
        Arguments:
            item_num: str, the alpha-numeric unique identifier of the item to be sold in the self.STOCK_FILEPATH database
        """
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock = stock.set_index('item_id')
    
        try:
            item = stock.loc[item_ID]
        except KeyError:
            item = pd.Series()
            
        return item
        
    
    def order_done(self):
        """
        Load the stock file
        Create a new order dict with all the details to save to the orders file
        Reduce the stock of the ordered items and re-save to the stock file
        
        SLOT connected to commit_button.clicked() SIGNAL in __init__()
        """
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock = stock.set_index('item_id')
        
        #check the order is valid
        order_ok = False
        for item in self.items:
            if item.item_id != item.NO_ITEM:#item ID has been input
                #check the quantity is set
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
                    item.show_not_enough_stock_message(quantity)
                    order_ok = False
                    break
                #and that the order has a quantity
                elif quantity == 0:
                    order_ok = False
                    break

                order_ok = True
        
        
        if order_ok:
            #create the new order object
            order = {
                    'date':self.dateEdit.text(),
                    'postcode':self.postcodeEdit.text(),
                    'order_amount':self.orderAmountEdit.text(),
                    'ebay_amount':self.ebayCutEdit.text(),
                    'paypal_amount':self.paypalCutEdit.text(),
                    'postpack_amount':self.ppEdit.text()
                    }
                    
            order['profit'] = float(order['order_amount']) - float(order['ebay_amount']) - float(order['paypal_amount']) - float(order['postpack_amount'])
            
            i = 1 # item number in order
            for item in self.items:
                if item.item_id != item.NO_ITEM:#item ID has been input
                    # deduct the quantity from the stock line
                    quantity = int(item.quantityEdit.text())
                    stock.loc[item.item_id, 'stock'] -= quantity

                    #add the items to the order dict
                    order['item{}_num'.format(i)] = item.item_id
                    order['item{}_quantity'.format(i)] = quantity
                    
                    #calculate the outlay for the items and deduct from the profit
                    out = quantity * float(stock.loc[item.item_id, 'price'])                
                    order['profit'] -= out
                    
                    i+=1

            #load the order saving file and append the new order
            saved_orders = pd.read_csv(self.ORDERS_FILEPATH)
            saved_orders = saved_orders.append(order, ignore_index=True)
            saved_orders = saved_orders.set_index('postcode')

            ###
            print(saved_orders)
            ###

            #save the orders file
            try:
                saved_orders.to_csv(self.ORDERS_FILEPATH)
            except PermissionError as err:
                self.show_save_failed_message('orders database', err)
                order_ok = False
                  
            ####
            print(stock)
            ####
            
            #save the new stock database to file if everything above is ok
            if order_ok:
                try:
                    stock.to_csv(self.STOCK_FILEPATH)
                except PermissionError as err:
                    self.show_save_failed_message('stock database', err)
                    order_ok = False
                
            #Message box pop-up asking if you want to do another order
            if order_ok:
                msg = widgets.QMessageBox()
                msg.setIcon(widgets.QMessageBox.Question)
                msg.setText("Success!")
                msg.setInformativeText("The order has been added and the stock has been deducted from the database. \n\nAdd another?")
                msg.setWindowTitle("Order added")
                msg.setStandardButtons(widgets.QMessageBox.Yes | widgets.QMessageBox.No)
                msg.setEscapeButton(widgets.QMessageBox.No)
                msg.buttonClicked.connect(self.new_order)
                msg.exec_()
        else:
            #Message box pop-up asking if you want to do another order
            msg = widgets.QMessageBox()
            msg.setIcon(widgets.QMessageBox.Information)
            msg.setText("No items added")
            msg.setInformativeText("Problems were found in the form")
            msg.setWindowTitle("No items added")
            msg.setStandardButtons(widgets.QMessageBox.Ok)
            msg.exec_()
            
    def stock_done(self):
        """
        For adding stock
        """
        stock = pd.read_csv(self.STOCK_FILEPATH)
        stock = stock.set_index('item_id')
        
        stock_ok = False
        for item in self.stockItems:
            if item.item_id != item.NO_ITEM:#item ID has been input
                #check the quantity is set
                try:
                    quantity = int(item.quantityEdit.text())
                except ValueError:
                    stock_ok = False
                    break
                    
                #check for the index
                try:
                    stock.loc[item.item_id, 'stock']
                except KeyError:
                    stock_ok = False
                    break
                
                #check that the order has a quantity
                if quantity == 0:
                    stock_ok = False
                    break

                stock_ok = True
                
        if stock_ok:
            for item in self.stockItems:
                if item.item_id != item.NO_ITEM:#item ID has been input
                    # add the quantity from the stock line
                    quantity = int(item.quantityEdit.text())
                    stock.loc[item.item_id, 'stock'] += quantity
                
            ###
            print(stock)
            ###
                
            #save back to file
            try:
                stock.to_csv(self.STOCK_FILEPATH)
            except PermissionError as err:
                self.show_save_failed_message('stock database', err)
                stock_ok = False
            
            #Message box pop-up asking if you want to do another order
            if stock_ok:
                msg = widgets.QMessageBox()
                msg.setIcon(widgets.QMessageBox.Question)
                msg.setText("Success!")
                msg.setInformativeText("The stock has been added to the database. \n\nAdd another?")
                msg.setWindowTitle("Stock added")
                msg.setStandardButtons(widgets.QMessageBox.Yes | widgets.QMessageBox.No)
                msg.setEscapeButton(widgets.QMessageBox.No)
                msg.buttonClicked.connect(self.new_stock_input)
                msg.exec_()
        else:
            #Message box pop-up asking if you want to do another order
            msg = widgets.QMessageBox()
            msg.setIcon(widgets.QMessageBox.Information)
            msg.setText("No stock added")
            msg.setInformativeText("Problems were found in the form")
            msg.setWindowTitle("No stock added")
            msg.setStandardButtons(widgets.QMessageBox.Ok)
            msg.exec_()
        
        
        
    def show_save_failed_message(self, file, error):
        """
        Show a message box when saving to a file fails, e.g. the self.STOCK_FILEPATH or self.ORDERS_FILEPATH
        
        Arguments:
            file: str, Short description of the file causing the problem
            error: PermissionError or str, the error captured by the except statement
        """
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Warning)
        msg.setText("Save failed")
        msg.setInformativeText("The order could not be saved to the {} file, check the file is not open elsewhere.".format(file))
        msg.setDetailedText("{}".format(error))
        msg.setWindowTitle("Save failed")
        msg.setStandardButtons(widgets.QMessageBox.Ok)
        msg.exec_()

    def new_order(self, buttonPressed):
        """
        Clear the order form if the user presses 'yes' to adding another order
        Removes any inputs to the order form and returns it to the default state
        Arguments:
            buttonPressed: The button pressed in the 'Order added' message box
        """
        if buttonPressed.text() == "&Yes":
            print("Clearing order form")
            
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
            
    def new_stock_input(self, buttonPressed):
        """
        Clears the stock input form if the user presses 'yes' to adding another stock input
        
        Arguments:
            buttonPressed: The button pressed in the 'Stock added' message box
        """
        if buttonPressed.text() == "&Yes":
            print("Clearing stock adding form")
            
            for item in self.stockItems:
                item.clear_form()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    