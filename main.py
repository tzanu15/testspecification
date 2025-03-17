import os
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def get_resource_path(relative_path):
    """Get the correct path whether running as a script or an executable."""
    if getattr(sys, 'frozen', False):  # Running as compiled .exe
        base_path = os.path.dirname(sys.executable) # Use folder where main.exe is
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))  # Development mode

    return os.path.join(base_path, relative_path)

def load_stylesheet(used_app):
    """Load the stylesheet file with the correct path handling."""
    qss_path = get_resource_path("utils/style.qss")

    if os.path.exists(qss_path):  # Check if the file exists
        with open(qss_path, "r") as f:
            used_app.setStyleSheet(f.read())
    else:
        print(f"⚠️ WARNING: Stylesheet not found: {qss_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_stylesheet(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
