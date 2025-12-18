import sys
from PySide6.QtWidgets import QApplication

from .ui import MainWindow
from . import config

def main():
    """
    Main function to run the AsciiCanvas application.
    """
    # FIX: Call the new, non-recursive setup function once at startup
    config.ensure_config_and_dirs_exist()
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
