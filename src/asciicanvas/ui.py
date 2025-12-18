import sys
import json
import os
import time
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QStatusBar, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QSplitter, QFrame, QLineEdit, QLabel, QDialog,
                               QFileDialog, QPushButton, QStackedWidget, QListWidgetItem, QInputDialog)
from PySide6.QtGui import (QPainter, QColor, QFont, QAction, QFontDatabase, QFontMetrics, QPen)
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QTimer, QPointF, QRectF

from . import config
from .model import Canvas, Cell, CHUNK_SIZE, Table, Math, PageFrame
from .drawing_utils import get_line_cells, get_rect_cells
from .pdf_export import export_to_pdf

COLORS_DARK = {
    'default_fg': QColor(220, 220, 220), 'default_bg': QColor(30, 30, 30),
    1: QColor(135, 206, 250), 2: QColor(144, 238, 144), 3: QColor(255, 255, 224),
    4: QColor(255, 182, 193), 5: QColor(221, 160, 221),
}
BASE_FONT_SIZE = 15

def get_font():
    font_path = os.path.join(os.path.dirname(__file__), 'resources', 'DejaVuSansMono.ttf')
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families: return QFont(font_families[0], BASE_FONT_SIZE)
    fallbacks = ["DejaVu Sans Mono", "Consolas", "Courier New", "Monospace"]
    for family in fallbacks:
        font = QFont(family, BASE_FONT_SIZE)
        if QFontDatabase.hasFamily(family): return font
    return QFont("monospace", BASE_FONT_SIZE)

class WelcomeWidget(QWidget):
    file_selected = Signal(str)
    create_new_file = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title_label = QLabel()
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("monospace", 12))
        title_label.setText(" ASCIICANVAS ")
        layout.addWidget(title_label)
        self.file_list = QListWidget()
        self.file_list.setMaximumWidth(400)
        self.file_list.itemDoubleClicked.connect(self.on_file_selected)
        layout.addWidget(self.file_list)
        button_layout = QHBoxLayout()
        self.new_button = QPushButton("Create New")
        self.new_button.clicked.connect(self.create_new_file.emit)
        button_layout.addWidget(self.new_button)
        self.open_folder_button = QPushButton("Open Document Folder")
        self.open_folder_button.clicked.connect(self.open_document_folder)
        button_layout.addWidget(self.open_folder_button)
        layout.addLayout(button_layout)
        self.populate_files()
    def open_document_folder(self):
        os.startfile(config.get_document_folder())
    def populate_files(self):
        self.file_list.clear()
        doc_folder = config.get_document_folder()
        for fname in sorted(os.listdir(doc_folder)):
            if fname.endswith('.asciicanvas'): self.file_list.addItem(QListWidgetItem(fname))
    def on_file_selected(self, item): self.file_selected.emit(item.text())

class CanvasWidget(QWidget):
    update_signal = Signal()
    REPEAT_DELAY_MS, REPEAT_INTERVAL_MS, SCROLL_MARGIN = 180, 16, 5
    ZOOM_STEPS = [0.2, 0.25, 0.33, 0.4, 0.5, 0.67, 0.8, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
    MOVEMENT_KEYS = {Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_H, Qt.Key_J, Qt.Key_K, Qt.Key_L}
    def __init__(self, canvas: Canvas, status_bar: QStatusBar, parent=None):
        super().__init__(parent)
        self.canvas, self.status_bar = canvas, status_bar
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.base_font = get_font()
        self.calculate_base_metrics()
        self.vx, self.vy, self.cursor_x, self.cursor_y = -5.0, -5.0, 0, 0
        self.zoom_level_index = self.ZOOM_STEPS.index(1.0)
        self.mode = 'NAV'
        self.key_press_time = {}
        self.movement_timer = QTimer(self)
        self.movement_timer.timeout.connect(self.process_held_keys)
        self.movement_timer.start(self.REPEAT_INTERVAL_MS)
        self.grid_visible = True
        self.update_status_bar()
    def calculate_base_metrics(self):
        metrics = QFontMetrics(self.base_font)
        self.base_cell_height, self.base_cell_width = metrics.height(), metrics.horizontalAdvance('W')
    def get_zoomed_cell_size(self):
        zoom = self.ZOOM_STEPS[self.zoom_level_index]
        return self.base_cell_width * zoom, self.base_cell_height * zoom
    def world_to_screen(self, wx, wy):
        cell_w, cell_h = self.get_zoomed_cell_size()
        return QPoint(int((wx - self.vx) * cell_w), int((wy - self.vy) * cell_h))
    def screen_to_world(self, sx, sy):
        cell_w, cell_h = self.get_zoomed_cell_size()
        if cell_w == 0 or cell_h == 0: return self.vx, self.vy
        return self.vx + (sx / cell_w), self.vy + (sy / cell_h)
    def center_view_on_cursor(self):
        cell_w, cell_h = self.get_zoomed_cell_size()
        view_w_cells = self.width() / cell_w if cell_w > 0 else 0
        view_h_cells = self.height() / cell_h if cell_h > 0 else 0
        self.vx, self.vy = self.cursor_x - view_w_cells / 2, self.cursor_y - view_h_cells / 2
    def ensure_cursor_visible(self):
        margin = self.SCROLL_MARGIN
        cell_w, cell_h = self.get_zoomed_cell_size()
        view_w_cells = self.width() / cell_w if cell_w > 0 else 0
        view_h_cells = self.height() / cell_h if cell_h > 0 else 0
        if self.cursor_x < self.vx + margin: self.vx = self.cursor_x - margin
        elif self.cursor_x >= self.vx + view_w_cells - margin: self.vx = self.cursor_x - view_w_cells + margin + 1
        if self.cursor_y < self.vy + margin: self.vy = self.cursor_y - margin
        elif self.cursor_y >= self.vy + view_h_cells - margin: self.vy = self.cursor_y - view_h_cells + margin + 1
    def wheelEvent(self, event):
        mods = event.modifiers()
        if mods == Qt.ControlModifier:
            world_x_before, world_y_before = self.screen_to_world(event.position().x(), event.position().y())
            if event.angleDelta().y() > 0: self.zoom_level_index = min(len(self.ZOOM_STEPS) - 1, self.zoom_level_index + 1)
            else: self.zoom_level_index = max(0, self.zoom_level_index - 1)
            world_x_after, world_y_after = self.screen_to_world(event.position().x(), event.position().y())
            self.vx += world_x_before - world_x_after; self.vy += world_y_before - world_y_after
        elif mods == Qt.ShiftModifier: self.vx -= (event.angleDelta().y() / 120) * 5
        else: self.vy -= (event.angleDelta().y() / 120) * 5
        self.update_status_bar(); self.update(); self.update_signal.emit()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            wx, wy = self.screen_to_world(event.position().x(), event.position().y())
            self.cursor_x, self.cursor_y = math.floor(wx), math.floor(wy)
            self.update_status_bar(); self.update(); self.update_signal.emit()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), COLORS_DARK['default_bg'])
        zoom_factor = self.ZOOM_STEPS[self.zoom_level_index]
        cell_w, cell_h = self.get_zoomed_cell_size()
        if cell_w <= 0.1 or cell_h <= 0.1: return
        start_wx, start_wy = self.screen_to_world(0, 0)
        end_wx, end_wy = self.screen_to_world(self.width(), self.height())
        if self.grid_visible and zoom_factor > 0.5:
            grid_pen = QPen(QColor(60, 60, 60)); grid_pen.setStyle(Qt.DotLine); painter.setPen(grid_pen)
            for x_grid in range(math.floor(start_wx), math.ceil(end_wx) + 1):
                sp = self.world_to_screen(x_grid, 0); painter.drawLine(sp.x(), 0, sp.x(), self.height())
            for y_grid in range(math.floor(start_wy), math.ceil(end_wy) + 1):
                sp = self.world_to_screen(0, y_grid); painter.drawLine(0, sp.y(), self.width(), sp.y())
        scaled_font = QFont(self.base_font); scaled_font.setPointSizeF(BASE_FONT_SIZE * zoom_factor); painter.setFont(scaled_font)
        for y in range(math.floor(start_wy), math.ceil(end_wy) + 1):
            batch_start_x, current_batch, current_style = math.floor(start_wx), "", None
            def flush_batch():
                nonlocal current_batch, batch_start_x, current_style
                if not current_batch: return
                sp = self.world_to_screen(batch_start_x, y)
                batch_width = len(current_batch) * cell_w
                if current_style[1] is not None: painter.fillRect(QRectF(sp.x(), sp.y(), batch_width, cell_h), COLORS_DARK.get(current_style[1]))
                painter.setPen(COLORS_DARK.get(current_style[0], COLORS_DARK['default_fg']))
                painter.drawText(QPointF(sp.x(), sp.y() + self.base_cell_height * zoom_factor * 0.8), current_batch)
                current_batch = ""
            for x in range(math.floor(start_wx), math.ceil(end_wx) + 2):
                cell = self.canvas.get_cell(x, y); style = (cell.fg, cell.bg)
                if style != current_style: flush_batch(); current_style = style; batch_start_x = x
                current_batch += cell.ch
            flush_batch()
        cursor_screen_pos = self.world_to_screen(self.cursor_x, self.cursor_y)
        cursor_rect = QRect(cursor_screen_pos.x(), cursor_screen_pos.y(), int(cell_w), int(cell_h))
        painter.setCompositionMode(QPainter.CompositionMode_Difference); painter.fillRect(cursor_rect, QColor(255, 255, 255)); painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    def keyPressEvent(self, event):
        key, mods, text = event.key(), event.modifiers(), event.text()
        if event.isAutoRepeat() and key in self.MOVEMENT_KEYS: return
        self.key_press_time[key] = time.time()
        dx, dy, is_move_key = 0, 0, True
        if key in self.MOVEMENT_KEYS:
            if self.mode == 'NAV' or key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                if key in (Qt.Key_Up, Qt.Key_K): dy = -1
                elif key in (Qt.Key_Down, Qt.Key_J): dy = 1
                elif key in (Qt.Key_Left, Qt.Key_H): dx = -1
                elif key in (Qt.Key_Right, Qt.Key_L): dx = 1
            else: is_move_key = False
        else: is_move_key = False
        if is_move_key:
            if mods == Qt.ShiftModifier: self.vx += dx; self.vy += dy; self.cursor_x += dx; self.cursor_y += dy
            else: self.cursor_x += dx; self.cursor_y += dy; self.ensure_cursor_visible()
        elif key == Qt.Key_Escape: self.mode = 'NAV'
        elif self.mode == 'NAV':
            if key == Qt.Key_I: self.mode = 'TEXT'
            elif key == Qt.Key_Z: self.center_view_on_cursor()
            elif key == Qt.Key_G: self.grid_visible = not self.grid_visible
        elif self.mode == 'TEXT':
            if key == Qt.Key_Backspace:
                self.cursor_x -= 1; op = {"type": "SET_CELL", "x": self.cursor_x, "y": self.cursor_y, "new_cell": list(Cell()._asdict().values())}; self.canvas.log_and_apply_operation(op); self.ensure_cursor_visible()
            elif text and text.isprintable():
                op = {"type": "SET_CELL", "x": self.cursor_x, "y": self.cursor_y, "new_cell": list(Cell(ch=text)._asdict().values())}; self.canvas.log_and_apply_operation(op); self.cursor_x += 1; self.ensure_cursor_visible()
        self.update_status_bar(); self.update(); self.update_signal.emit()
    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat() and event.key() in self.key_press_time: del self.key_press_time[event.key()]
    def process_held_keys(self):
        if not self.key_press_time: return
        now, dx, dy, moved = time.time(), 0, 0, False
        is_shift_held = Qt.Key_Shift in self.key_press_time
        for key, press_time in self.key_press_time.items():
            if (now - press_time) * 1000 > self.REPEAT_DELAY_MS:
                if key in self.MOVEMENT_KEYS:
                    if self.mode == 'NAV' or key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                        if key in (Qt.Key_Up, Qt.Key_K): dy -= 1
                        elif key in (Qt.Key_Down, Qt.Key_J): dy += 1
                        elif key in (Qt.Key_Left, Qt.Key_H): dx -= 1
                        elif key in (Qt.Key_Right, Qt.Key_L): dx += 1
                        moved = True
        if moved:
            if is_shift_held: self.vx += dx; self.vy += dy; self.cursor_x += dx; self.cursor_y += dy
            else: self.cursor_x += dx; self.cursor_y += dy; self.ensure_cursor_visible()
            self.update_status_bar(); self.update(); self.update_signal.emit()
    def update_status_bar(self):
        zoom = self.ZOOM_STEPS[self.zoom_level_index] * 100
        self.status_bar.showMessage(f"Mode: {self.mode} | Cursor: ({self.cursor_x}, {self.cursor_y}) | View: ({self.vx:.1f}, {self.vy:.1f}) | Zoom: {zoom:.0f}%")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AsciiCanvas")
        self.setGeometry(100, 100, 1280, 720)
        self.canvas_widget = None
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.welcome_widget = WelcomeWidget()
        self.welcome_widget.file_selected.connect(self.open_document)
        self.welcome_widget.create_new_file.connect(self.create_new_document)
        self.stack.addWidget(self.welcome_widget)
        self.show_welcome_screen()
    def show_welcome_screen(self):
        self.welcome_widget.populate_files()
        self.stack.setCurrentWidget(self.welcome_widget)
        self.setWindowTitle("AsciiCanvas - Welcome")
    def open_document(self, file_name: str):
        doc_path = config.get_document_folder() / file_name
        canvas = Canvas(str(doc_path))
        canvas.load()
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.canvas_widget = CanvasWidget(canvas, status_bar)
        self.stack.addWidget(self.canvas_widget)
        self.stack.setCurrentWidget(self.canvas_widget)
        self.setWindowTitle(f"AsciiCanvas - {file_name}")
    def create_new_document(self):
        file_name, ok = QInputDialog.getText(self, "Create New Document", "Enter file name:")
        if ok and file_name:
            if not file_name.endswith(".asciicanvas"): file_name += ".asciicanvas"
            doc_path = config.get_document_folder() / file_name
            if doc_path.exists(): return
            self.open_document(file_name)
    def closeEvent(self, event):
        if self.canvas_widget and self.canvas_widget.canvas:
            self.canvas_widget.canvas.close()
        event.accept()
