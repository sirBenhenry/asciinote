import os
import pytest
from time import time

from asciicanvas.database import Database
from asciicanvas.model import Canvas, Cell, CHUNK_SIZE

@pytest.fixture
def db_path():
    """Provides a temporary database path for testing."""
    test_db = "test.asciicanvas"
    yield test_db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_database_creation(db_path):
    """Test that the database and tables are created successfully."""
    db = Database(db_path)
    db.connect()
    db.create_tables()
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert {"meta", "chunks", "objects", "journal"}.issubset(tables)
    
    db.close()

def test_journal_append(db_path):
    """Test appending an operation to the journal."""
    db = Database(db_path)
    db.connect()
    db.create_tables()

    op_data = b'{"op": "test"}'
    ts = int(time())
    db.append_journal_op(ts, op_data)

    cursor = db.conn.cursor()
    cursor.execute("SELECT ts, op FROM journal ORDER BY seq DESC LIMIT 1;")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == ts
    assert row[1] == op_data

    db.close()

def test_chunk_serialization_loop(db_path):
    """Test that serializing and deserializing a chunk yields the same data."""
    canvas = Canvas(db_path)
    canvas.load()

    # Set some cells in a chunk
    canvas.set_cell(10, 20, Cell(ch='A', fg=1, bg=2))
    canvas.set_cell(30, 40, Cell(ch='B', owner="obj1"))
    # Set a cell to default to test pruning
    canvas.set_cell(50, 60, Cell(ch='C'))
    canvas.set_cell(50, 60, Cell()) 

    cx, cy = 10 // CHUNK_SIZE, 20 // CHUNK_SIZE
    chunk = canvas.get_chunk(cx, cy)
    
    # Save to DB
    canvas.save_all_dirty_chunks()
    canvas.close()

    # Re-load from DB
    new_canvas = Canvas(db_path)
    new_canvas.load()

    # Verify cells
    assert new_canvas.get_cell(10, 20) == Cell(ch='A', fg=1, bg=2)
    assert new_canvas.get_cell(30, 40) == Cell(ch='B', owner="obj1")
    assert new_canvas.get_cell(50, 60) == Cell() # Should be default

    new_canvas.close()

def test_empty_chunk_not_saved(db_path):
    """Test that a chunk with only default cells is not saved."""
    canvas = Canvas(db_path)
    canvas.load()

    # Access a chunk but don't modify it
    chunk = canvas.get_chunk(1, 1)
    assert not chunk.dirty
    
    # Save and close
    canvas.save_all_dirty_chunks()
    canvas.close()

    # Check the database directly
    db = Database(db_path)
    db.connect()
    chunk_data = db.get_chunk(1, 1)
    assert chunk_data is None
    db.close()
