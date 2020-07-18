import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import pyqtSignal as Signal
import datetime as dt
import pandas as pd
import os
from item import Item
from driveAccess import DriveAccess

class MainWindow(widgets.QTabWidget):
    STOCK_FILEPATH = "stock.csv" # path to the csv file containing the stock details: amounts prices descriptions etc.
    STOCK_ADDING_FILEPATH = "stock_adding.csv" # path to the csv file containing the details of the stock inputs
    ORDERS_FILEPATH = "orders.csv" # path to the csv file containing the orders: order dates, order amounts etc.
    EBAY_CUT = 0.1 # proportion of the order taken by ebay
    PAYPAL_PERCENT_CUT = 0.029 # proportion of the order taken by paypal
    PAYPAL_PER_ORDER_ABSOLUTE_CUT = 0.3 # absolute amount in gbp taken by paypal per order
    EBAY_INTERNATIONAL_PROGRAMME_POSTCODES = ["WS13 8UR", "WS138UR"] # Postcodes of the ebay international programme address
    POSTAGE_COST = 0.88 # default absolute gbp cost of postage per order
    PACKING_COST = 0.09 # default absolute gbp cost of packing per order
    
    window_quit_signal = Signal()   
    def __init__(self):
        """
        Initialise the main GUI with the form for the order details, the first item form object and the order commiting button
        """
        super().__init__()

        #init the drive file access and pull down the files
        self.da = DriveAccess()
        self.ask_pull()

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
        
        #undo button
        undo_button = widgets.QPushButton("Undo last order")
        undo_button.clicked.connect(self.undo_last_order)
        undo_button.setFocusPolicy(Qt.ClickFocus)
        self.orderLayout.addWidget(undo_button)

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
        
        #undo button
        stock_undo_button = widgets.QPushButton("Undo last stock add")
        stock_undo_button.clicked.connect(self.undo_last_stock_add)
        stock_undo_button.setFocusPolicy(Qt.ClickFocus)
        self.stockLayout.addWidget(stock_undo_button)
        
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
        
    def ask_pull(self):
        """
        Ask if the user wants to keep the local or remote file in a message window
        """
        mod_times = pd.DataFrame()
        for filename in [self.STOCK_FILEPATH, self.ORDERS_FILEPATH, self.STOCK_ADDING_FILEPATH]:
            local_mod_time = os.path.getmtime(filename)
            local_mod_time = dt.datetime.fromtimestamp(local_mod_time)
            
            exists = self.da.getID(filename)
            if exists:
                remote_mod_time = self.da.file_mod_times[filename]
            
                mod_times = mod_times.append({'local':local_mod_time, 'remote':remote_mod_time, 'filename':filename}, ignore_index=True)
            else:
                mod_times = mod_times.append({'local':local_mod_time, 'remote':None, 'filename':filename}, ignore_index=True)
        
        mod_times.remote = pd.to_datetime(mod_times.remote, errors='coerce')
        
        print(mod_times)
        
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Question)
        msg.setText("Would you like to download the database files from google drive?")
        msg.setInformativeText("Clicking 'yes' will download the database files from google drive and overwrite the local files. Clicking 'no' will keep the local files.")
        msg.setWindowTitle("Download")
        msg.setStandardButtons(widgets.QMessageBox.Yes | widgets.QMessageBox.No)
        msg.buttonClicked.connect(self.remote_pull)
        msg.exec_()
    
    def remote_pull(self, buttonPressed):
        """
        If the user agrees to downloading the remote files, get the files and overwrite the local ones.
        SLOT connected to msg.buttonClicked() SIGNAL in self.ask_pull()
        
        Arguments:
            buttonPressed: the button pressed in the download question message box
        """
        if buttonPressed.text() == "&Yes":       
            stock, orders, stock_adding = self.da.pull_fileGroup([self.STOCK_FILEPATH, self.ORDERS_FILEPATH, self.STOCK_ADDING_FILEPATH])
            stock = stock.set_index('item_id')
            try:
                stock.to_csv(self.STOCK_FILEPATH)
            except PermissionError as err:
                self.show_save_failed_message('stock database', err)
                
            orders = orders.set_index('postcode')
            try:
                orders.to_csv(self.ORDERS_FILEPATH)
            except PermissionError as err:
                self.show_save_failed_message('order database', err)

            stock_adding = stock_adding.set_index(['date', 'time'])
            try:
                stock_adding.to_csv(self.STOCK_ADDING_FILEPATH)
            except PermissionError as err:
                self.show_save_failed_message('stock input database', err)
        
        
    def closeEvent(self, event):
        """
        Override the closeEvent QWidget SLOT.
        Ask the user if they want to upload the changes to the databases to google drive
        
        Arguments:
            event: the close event to ignore
        """
        event.ignore()
        
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Question)
        msg.setText("Save to Drive?")
        msg.setInformativeText("Clicking 'yes' will upload the changes to the databases to google drive.")
        msg.setWindowTitle("Upload")
        msg.setStandardButtons(widgets.QMessageBox.Yes | widgets.QMessageBox.No)
        msg.buttonClicked.connect(self.closing_actions)
        msg.exec_()
        
    def closing_actions(self, buttonPressed):
        if buttonPressed.text() == "&Yes":
            for filename in [self.STOCK_FILEPATH, self.ORDERS_FILEPATH, self.STOCK_ADDING_FILEPATH]:
                file_exists = self.da.getID(filename)
                self.da.push(filename, new=not file_exists)

        self.window_quit_signal.emit()
        
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
        if len(self.stockItems) == edit_num+1 and self.stockItems[edit_num].item_id != self.stockItems[edit_num].NO_ITEM:
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
                    
            # order['profit'] = float(order['order_amount']) - float(order['ebay_amount']) - float(order['paypal_amount']) - float(order['postpack_amount'])
            
            i = 1 # item number in order
            for item in self.items:
                if item.item_id != item.NO_ITEM:#item ID has been input
                    # deduct the quantity from the stock line
                    quantity = int(item.quantityEdit.text())
                    stock.loc[item.item_id, 'stock'] -= quantity

                    #add the items to the order dict
                    order['item{}_id'.format(i)] = item.item_id
                    order['item{}_quantity'.format(i)] = quantity
                    order['item{}_manufacturer'.format(i)] = item.item.loc['manufacturer']
                    order['item{}_category'.format(i)] = item.item.loc['category']
                    
                    #calculate the outlay for the items and deduct from the profit
                    # out = quantity * float(stock.loc[item.item_id, 'price'])                
                    # order['profit'] -= out
                    
                    i+=1

            print(order)

            #load the order saving file and append the new order
            saved_orders = pd.read_csv(self.ORDERS_FILEPATH)
            saved_orders = saved_orders.append(order, ignore_index=True)
            saved_orders = saved_orders.set_index('postcode')

            ###
            # print(saved_orders)
            ###

            #save the orders file
            try:
                saved_orders.to_csv(self.ORDERS_FILEPATH)
            except PermissionError as err:
                self.show_save_failed_message('orders database', err)
                order_ok = False
                  
            ####
            # print(stock)
            ####
            
            #save the new stock database to file if everything above is ok
            if order_ok:
                try:
                    stock.to_csv(self.STOCK_FILEPATH)
                except PermissionError as err:
                    #remove the last order and resave
                    saved_orders = saved_orders[:-1]
                    saved_orders.to_csv(self.ORDERS_FILEPATH)
                
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
        
        new_item = {item.item_id:False for item in self.stockItems}
        stock_ok = False
        for item in self.stockItems:
            if item.item_id != item.NO_ITEM:#item ID has been input
                #check the quantity is set
                try:
                    quantity = int(item.quantityEdit.text())
                except ValueError:
                    stock_ok = False
                    break
                    
                #check for the index, if it's not found this is a new item and we need to check the manufacturer and category values are set
                try:
                    stock.loc[item.item_id, 'stock']
                except KeyError:
                    print('New item with id {}'.format(id))
                    new_item[item.item_id] = True
                    if item.manufacturerEdit.text() == item.NO_MANUFACTURER or item.categoryEdit.text() == item.NO_CATEGORY:
                        stock_ok = False
                        break
                        
                #check that the stock add has a quantity
                if quantity == 0:
                    stock_ok = False
                    break

                #Found at least one valid item
                stock_ok = True
                
        if stock_ok:
            #create the new stock add object
            stock_add = {
                        'date':"{:%d/%m/%Y}".format(dt.date.today()),
                        'time':"{0}:{1}:{2}".format(dt.datetime.now().hour, dt.datetime.now().minute, dt.datetime.now().second)
                        }
            
            item_num = 1
            for item in self.stockItems:
                if item.item_id != item.NO_ITEM:#item ID has been input
                    # add the quantity from the stock line
                    quantity = int(item.quantityEdit.text())
                    
                    if new_item[item.item_id]:
                        stock = stock.append(pd.Series({'stock':quantity, 'manufacturer':item.manufacturerEdit.text(), 'category':item.categoryEdit.text()}, name=item.item_id))
                    else:
                        stock.loc[item.item_id, 'stock'] += quantity
                    
                    stock_add['item{}_id'.format(item_num)] = item.item_id
                    stock_add['item{}_quantity'.format(item_num)] = quantity
                    item_num += 1
                
            ###
            print(stock_add)
            # print(stock)
            ###
            
            #add the new stock input to the database
            stock_adding = pd.read_csv(self.STOCK_ADDING_FILEPATH)
            stock_adding = stock_adding.append(stock_add, ignore_index=True)
            stock_adding = stock_adding.set_index(['date', 'time'])
                
            #save back to file
            try:
                stock_adding.to_csv(self.STOCK_ADDING_FILEPATH)
            except PermissionError as err:
                self.show_save_failed_message('stock input database', err)
                stock_ok = False
            
            if stock_ok:
                try:
                    stock.to_csv(self.STOCK_FILEPATH)
                except PermissionError as err:
                    #remove the stock input
                    stock_adding = stock_adding[:-1]
                    stock_adding.to_csv(self.STOCK_ADDING_FILEPATH)
                
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
        
        
    def undo_last_order(self):
        """
        Ask for confirmation about removing the last order
        
        SLOT connected to undo_button.clicked() SIGNAL in self.__init__()
        """
        orders = pd.read_csv(self.ORDERS_FILEPATH)
        
        last_order = orders.iloc[-1]
        
        #show warning
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Warning)
        msg.setText("Are you sure you want to remove the last order? This cannot be undone.")
        msg.setInformativeText("Date: {0}, Postcode: {1}, Amount: £{2:.2f}".format(last_order.loc['date'], last_order.loc['postcode'], last_order.loc['order_amount']))
        msg.setWindowTitle("Undo last order")
        msg.setStandardButtons(widgets.QMessageBox.Yes | widgets.QMessageBox.Cancel)
        msg.buttonClicked.connect(self.undo_last_order_confirmed)
        msg.exec_()

    def undo_last_order_confirmed(self, buttonPressed):
        """
        Remove the last order from the orders database and re-add the stock to the stock database
        
        SLOT connected to msg.buttonClicked() SIGNAL in self.undo_last_order()
        """
        if buttonPressed.text() == "&Yes":
            undo_ok = True
            
            orders = pd.read_csv(self.ORDERS_FILEPATH)
            stock = pd.read_csv(self.STOCK_FILEPATH)
            stock = stock.set_index('item_id')
            
            last_order = orders.iloc[-1]
            
            #remove the order
            orders = orders.drop([last_order.name])
            
            last_order = last_order.rename(last_order.loc['postcode'])
            last_order = last_order.drop('postcode')
            orders = orders.set_index('postcode')
            
            print(last_order)
            
            item_num = 1
            while True:
                try:
                    item_id = last_order.loc['item{}_id'.format(item_num)]
                    quantity = int(last_order.loc['item{}_quantity'.format(item_num)])
                except (KeyError, ValueError):
                    break
                
                #re-add the stock of the item
                try:
                    stock.loc[item_id, 'stock'] += quantity
                except KeyError as err:
                    self.show_missing_stock_item_message(item_id, err)
                    undo_ok = False
                    break
                
                item_num += 1
        
            ###
            # print(orders)
            # print(stock)
            ###
            
            if undo_ok:
                #resave the orders
                try:
                    orders.to_csv(self.ORDERS_FILEPATH)
                except PermissionError as err:
                    self.show_save_failed_message('orders database', err)
                    undo_ok = False
                    
                if undo_ok:
                    #resave the stock
                    try:
                        stock.to_csv(self.STOCK_FILEPATH)
                    except PermissionError as err:
                        #re-add the last order
                        orders = orders.append(last_order)
                        orders.to_csv(self.ORDERS_FILEPATH)
                    
                        self.show_save_failed_message('stock database', err)
                        undo_ok = False
            
    def show_missing_stock_item_message(self, item_id, error):
        """
        Show a message box when looking up a stock item fails
        
        Arguments:
            item_id: str, the id of the item that is missing
            error: KeyError or str, the key error thrown
        """
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Warning)
        msg.setText("Item look-up failed")
        msg.setInformativeText("Item {} could not be found in the database, the operation has been cancelled.".format(item_id))
        msg.setDetailedText("{}".format(error))
        msg.setWindowTitle("Item look-up failed")
        msg.setStandardButtons(widgets.QMessageBox.Ok)
        msg.exec_()
                
    def undo_last_stock_add(self):
        """
        Ask for confirmation about removing the last stock add
        
        SLOT connected to stock_undo_button.clicked() SIGNAL in self.__init__()
        """
        stock_adds = pd.read_csv(self.STOCK_ADDING_FILEPATH)
        
        last_add = stock_adds.iloc[-1]
        print(last_add)
        
        #show warning
        msg = widgets.QMessageBox()
        msg.setIcon(widgets.QMessageBox.Warning)
        msg.setText("Are you sure you want to remove the last stock input? This cannot be undone.")
        msg.setInformativeText("Date: {0}, Time: {1}, First item ID: {2}".format(last_add.loc['date'], last_add.loc['time'], last_add.loc['item1_id']))
        msg.setWindowTitle("Undo last stock add")
        msg.setStandardButtons(widgets.QMessageBox.Yes | widgets.QMessageBox.Cancel)
        msg.buttonClicked.connect(self.undo_last_stock_add_confirmed)
        msg.exec_()
        
    def undo_last_stock_add_confirmed(self, buttonPressed):
        """
        Remove the last stock add from the stock adding database and remove the stock from the stock database
        
        SLOT connected to msg.buttonClicked() SIGNAL in self.undo_last_stock_add()
        """
        if buttonPressed.text() == "&Yes":
            undo_ok = True
            stock_adds = pd.read_csv(self.STOCK_ADDING_FILEPATH)
            stock = pd.read_csv(self.STOCK_FILEPATH)
            stock = stock.set_index('item_id')
            
            last_add = stock_adds.iloc[-1]
            
            print(last_add)
            
            #drop the last stock add
            stock_adds = stock_adds.drop([last_add.name])
            
            item_num = 1
            while True:
                try:
                    item_id = last_add.loc['item{}_id'.format(item_num)]
                    quantity = int(last_add.loc['item{}_quantity'.format(item_num)])
                except (KeyError, ValueError):
                    break
                
                #remove the stock of the item
                try:
                    stock.loc[item_id, 'stock'] -= quantity
                except KeyError as err:
                    self.show_missing_stock_item_message(item_id, err)
                    undo_ok = False
                    break
                
                item_num += 1
        
            if undo_ok:
                #resave the stock adding
                stock_adds_to_save = stock_adds.set_index(['date', 'time'])
                try:
                    stock_adds_to_save.to_csv(self.STOCK_ADDING_FILEPATH)
                except PermissionError as err:
                    self.show_save_failed_message('stock input database', err)
                    undo_ok = False
                    
                if undo_ok:
                    #resave the stock database
                    try:
                        stock.to_csv(self.STOCK_FILEPATH)
                    except PermissionError as err:
                        #re-add the stock add
                        stock_adds = stock_adds.append(last_add)
                        stock_adds = stock_adds.set_index(['date', 'time'])
                        stock_adds.to_csv(self.STOCK_ADDING_FILEPATH)
                    
                        self.show_save_failed_message('stock database', err)
                        undo_ok = False
                        
        
        
        
        
        
        
        
    