# AsciiCanvas - Main Entry Point
import sys
import os
from PySide6.QtWidgets import QApplication

from .ui import MainWindow

def main():
    """
    Main function to run the AsciiCanvas application.
    """
    # Use a default document for now.
    # In the future, this could be handled by a file dialog or command-line argument.
    doc_name = "mydoc.asciicanvas"

    app = QApplication(sys.argv)
    
    # The main window handles loading the canvas from the given path.
    window = MainWindow(doc_name)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
