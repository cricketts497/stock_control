import PyQt5.QtWidgets as widgets
# from PyQt5.QtCore import Qt
import datetime as dt

class MainWindow(widgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
    
        #top bar title
        self.setWindowTitle("Stock Control")
    
        #Set the main layout for the app
        topLayout = widgets.QVBoxLayout()
        self.setLayout(topLayout)



        
        
        
        
   