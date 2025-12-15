import sys
import json
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QStatusBar, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QSplitter, QFrame, QLineEdit, QLabel, QDialog,
                               QFileDialog)
from PySide6.QtGui import QPainter, QColor, QFont, QAction, QFontDatabase
from PySide6.QtCore import Qt, QRect, QPoint, Signal

from .model import Canvas, Cell, CHUNK_SIZE, Table, Math, PageFrame
from .drawing_utils import get_line_cells, get_rect_cells
from .pdf_export import export_to_pdf

COLORS_DARK = {
    'default_fg': QColor(220, 220, 220), 'default_bg': QColor(30, 30, 30),
    1: QColor(135, 206, 250), 2: QColor(144, 238, 144), 3: QColor(255, 255, 224),
    4: QColor(255, 182, 193), 5: QColor(221, 160, 221),
}

def get_font():
    """Loads the bundled font or finds a suitable monospace fallback."""
    font_path = os.path.join(os.path.dirname(__file__), 'resources', 'DejaVuSansMono.ttf')
    
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                return QFont(font_families[0], 15)

    # Fallback if bundled font is missing
    font = QFont("DejaVu Sans Mono", 15)
    if QFontDatabase.hasFamily("DejaVu Sans Mono"):
        return font
    
    fallbacks = ["Consolas", "Courier New", "Monospace"]
    for family in fallbacks:
        font = QFont(family, 15)
        if QFontDatabase.hasFamily(family):
            return font
            
    return QFont("monospace", 15) # Generic fallback

class CanvasWidget(QWidget):
    update_signal = Signal()

    def __init__(self, canvas: Canvas, status_bar: QStatusBar, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.status_bar = status_bar
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.font = get_font() # Use the new font loading function
        self.calculate_font_metrics()
        # ... (rest of __init__)
        self.vx, self.vy = -5, -5
        self.cursor_x, self.cursor_y = 0, 0
        self.zoom = 1.0
        self.mode = 'NAV'
        self.selection_active = False
        self.selection_ax, self.selection_ay = 0, 0
        self.shape_tool = None
        self.shape_anchor_x, self.shape_anchor_y = None, None
        self.is_drawing = False
        self.input_buffer = ""
        self.math_anchor_x, self.math_anchor_y = None, None
        self.update_status_bar()

    def calculate_font_metrics(self):
        self.font_metrics = self.fontMetrics()
        self.cell_height = self.font_metrics.height()
        self.cell_width = self.font_metrics.horizontalAdvance('W')
        # Verify that the font is actually monospaced
        if self.cell_width != self.font_metrics.horizontalAdvance('i'):
            print("Warning: Font may not be monospaced. Layout issues may occur.")

    # ... (rest of CanvasWidget methods are the same)
    def world_to_screen(self, wx, wy):
        return QPoint(int((wx - self.vx) * self.cell_width * self.zoom), int((wy - self.vy) * self.cell_height * self.zoom))

    def screen_to_world(self, sx, sy):
        return self.vx + int(sx / (self.cell_width * self.zoom)), self.vy + int(sy / (self.cell_height * self.zoom))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), COLORS_DARK['default_bg'])
        painter.setFont(self.font)
        start_wx, start_wy = self.screen_to_world(0, 0)
        end_wx, end_wy = self.screen_to_world(self.width(), self.height())
        for y in range(start_wy, end_wy + 2):
            for x in range(start_wx, end_wx + 2):
                cell = self.canvas.get_cell(x, y)
                if cell == Cell(): continue
                sp = self.world_to_screen(x, y)
                if cell.bg: painter.fillRect(QRect(sp, QPoint(sp.x() + self.cell_width, sp.y() + self.cell_height)), COLORS_DARK.get(cell.bg))
                painter.setPen(COLORS_DARK.get(cell.fg, COLORS_DARK['default_fg']))
                painter.drawText(sp, cell.ch)
        sp = self.world_to_screen(self.cursor_x, self.cursor_y)
        painter.setPen(Qt.NoPen); painter.setBrush(QColor(255, 255, 255, 100))
        painter.drawRect(sp.x(), sp.y(), self.cell_width, self.cell_height)

    def keyPressEvent(self, event):
        key, mods, text = event.key(), event.modifiers(), event.text()

        if key == Qt.Key_Escape:
            if self.input_buffer: self.input_buffer = ""
            elif self.is_drawing: self.is_drawing = False; self.shape_tool = None
            elif self.selection_active: self.selection_active = False
            self.mode = 'NAV'
        
        elif self.mode == 'NAV':
            if key == Qt.Key_H or key == Qt.Key_Left: self.cursor_x -= 1
            elif key == Qt.Key_J or key == Qt.Key_Down: self.cursor_y += 1
            elif key == Qt.Key_K or key == Qt.Key_Up: self.cursor_y -= 1
            elif key == Qt.Key_L or key == Qt.Key_Right: self.cursor_x += 1
            elif key == Qt.Key_I: self.mode = 'TEXT'
            elif key == Qt.Key_M:
                self.mode = 'MATH'
                self.input_buffer = ""
                self.math_anchor_x, self.math_anchor_y = self.cursor_x, self.cursor_y

        elif self.mode == 'TEXT':
            if text and text.isprintable():
                op = {"type": "SET_CELL", "x": self.cursor_x, "y": self.cursor_y, "new_cell": list(Cell(ch=text)._asdict().values())}
                self.canvas.log_and_apply_operation(op)
                self.cursor_x += 1
        
        elif self.mode == 'MATH':
            if key == Qt.Key_Return:
                if self.input_buffer:
                    math_obj = Math(self.math_anchor_x, self.math_anchor_y, self.input_buffer)
                    self.canvas.create_object(math_obj)
                self.mode = 'NAV'
                self.input_buffer = ""
            elif key == Qt.Key_Backspace: self.input_buffer = self.input_buffer[:-1]
            elif text: self.input_buffer += text

        self.update_status_bar()
        self.update()
        self.update_signal.emit()

    def update_status_bar(self):
        self.status_bar.showMessage(f"Mode: {self.mode} | Cursor: ({self.cursor_x}, {self.cursor_y})")

class MainWindow(QMainWindow):
    def __init__(self, db_path: str):
        super().__init__()
        self.setWindowTitle("AsciiCanvas")
        self.setGeometry(100, 100, 1280, 720)
        self.db_path = db_path
        self.canvas = Canvas(db_path)
        self.canvas.load()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.canvas_widget = CanvasWidget(self.canvas, self.status_bar)
        self.setCentralWidget(self.canvas_widget)
        
        palette_action = QAction("Command Palette", self)
        palette_action.setShortcut("Ctrl+P")
        palette_action.triggered.connect(self.show_command_palette)
        self.addAction(palette_action)

    def show_command_palette(self):
        print("Command Palette would show here.")

    def closeEvent(self, event):
        self.canvas.close()
        event.accept()
