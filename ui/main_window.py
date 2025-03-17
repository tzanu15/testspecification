from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from pages.tests_page import TestsPage
from pages.parameters_page import ParametersPage
from pages.generic_command_page import GenericCommandPage
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test Specification Tool")
        self.setGeometry(100, 100, 800, 600)

        # Creăm tab-urile aplicației
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Adăugăm paginile în tab-uri
        self.tests_page = TestsPage()
        self.parameters_page = ParametersPage()
        self.commands_page = GenericCommandPage()

        self.tabs.addTab(self.tests_page, "Tests")
        self.tabs.addTab(self.parameters_page, "Parameters")
        self.tabs.addTab(self.commands_page, "Generic Commands")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
