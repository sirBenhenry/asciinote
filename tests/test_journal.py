import os
import pytest
import msgpack
from time import time

from asciicanvas.model import Canvas, Cell
from asciicanvas.database import Database

@pytest.fixture
def canvas_with_journal():
    """Provides a temporary canvas and db_path for journal testing."""
    db_path = "test_journal.asciicanvas"
    canvas = Canvas(db_path)
    canvas.load()
    yield canvas
    canvas.close()
    if os.path.exists(db_path):
        os.remove(db_path)

def test_apply_op_set_cell(canvas_with_journal):
    """Test that a SET_CELL operation correctly modifies the canvas."""
    canvas = canvas_with_journal
    op = {
        "type": "SET_CELL",
        "x": 10,
        "y": 20,
        "new_cell": Cell(ch='X', fg=1, bg=2, owner="id1")._asdict().values()
    }
    canvas.apply_operation(op)
    cell = canvas.get_cell(10, 20)
    assert cell.ch == 'X'
    assert cell.fg == 1
    assert cell.bg == 2
    assert cell.owner == "id1"

def test_journal_replay_on_load(canvas_with_journal):
    """Test that journaled operations are replayed when a canvas is loaded."""
    db_path = canvas_with_journal.db.db_path
    
    db = Database(db_path)
    db.connect()
    
    op1 = { "type": "SET_CELL", "x": 5, "y": 5, "new_cell": Cell(ch='A')._asdict().values() }
    op2 = { "type": "SET_CELL", "x": 6, "y": 6, "new_cell": Cell(ch='B', fg=1)._asdict().values() }
    
    db.append_journal_op(int(time()), msgpack.packb(op1))
    db.append_journal_op(int(time()), msgpack.packb(op2))
    
    db.close()
    canvas_with_journal.close()

    reopened_canvas = Canvas(db_path)
    reopened_canvas.load()

    assert reopened_canvas.get_cell(5, 5) == Cell(ch='A')
    assert reopened_canvas.get_cell(6, 6) == Cell(ch='B', fg=1)

    reopened_canvas.close()

def test_checkpointing_truncates_journal(canvas_with_journal):
    """Test that checkpointing compacts data and clears the journal."""
    canvas = canvas_with_journal
    db = canvas.db

    op1 = { "type": "SET_CELL", "x": 1, "y": 1, "new_cell": Cell(ch='C')._asdict().values() }
    canvas.log_and_apply_operation(op1)

    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM journal")
    assert cursor.fetchone()[0] == 1

    canvas.perform_checkpoint()

    cursor.execute("SELECT COUNT(*) FROM journal")
    assert cursor.fetchone()[0] == 0

    canvas.close()
    
    reopened_canvas = Canvas(canvas.db.db_path)
    reopened_canvas.load()
    assert reopened_canvas.get_cell(1, 1) == Cell(ch='C')
    reopened_canvas.close()
