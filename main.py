import sys
from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication

def main():
    #setup the container
    app = QApplication(sys.argv)
    window = MainWindow()
    window.window_quit_signal.connect(app.quit)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()