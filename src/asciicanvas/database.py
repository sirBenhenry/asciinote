import sqlite3
import zlib
from typing import Dict, Any, Tuple, Optional, List

try:
    import zstd
except ImportError:
    zstd = None

def compress_data(data: bytes) -> bytes:
    return zstd.compress(data) if zstd else zlib.compress(data)

def decompress_data(data: bytes) -> bytes:
    try:
        return zstd.decompress(data) if zstd else zlib.decompress(data)
    except (zlib.error, RuntimeError):
        return data

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self):
        if not self.conn: raise ConnectionError("Database is not connected.")
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value BLOB);")
            self.conn.execute("CREATE TABLE IF NOT EXISTS chunks (cx INT, cy INT, data BLOB, PRIMARY KEY(cx, cy));")
            self.conn.execute("CREATE TABLE IF NOT EXISTS objects (id TEXT PRIMARY KEY, type TEXT NOT NULL, data BLOB);")
            self.conn.execute("CREATE TABLE IF NOT EXISTS journal (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts INT NOT NULL, op BLOB);")

    def get_meta(self, key: str) -> Optional[bytes]:
        if not self.conn: raise ConnectionError("Database not connected")
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM meta WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_meta(self, key: str, value: bytes):
        if not self.conn: raise ConnectionError("Database not connected")
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))

    def get_chunk(self, cx: int, cy: int) -> Optional[bytes]:
        if not self.conn: raise ConnectionError("Database not connected.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM chunks WHERE cx = ? AND cy = ?", (cx, cy))
        row = cursor.fetchone()
        return row[0] if row else None

    def put_chunk(self, cx: int, cy: int, data: bytes):
        if not self.conn: raise ConnectionError("Database not connected.")
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO chunks (cx, cy, data) VALUES (?, ?, ?)", (cx, cy, data))

    def get_all_objects(self) -> List[Tuple[str, str, bytes]]:
        """Retrieves all objects from the database."""
        if not self.conn: raise ConnectionError("Database not connected.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, type, data FROM objects")
        return cursor.fetchall()

    def put_object(self, obj_id: str, obj_type: str, data: bytes):
        """Inserts or updates an object in the database."""
        if not self.conn: raise ConnectionError("Database not connected.")
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO objects (id, type, data) VALUES (?, ?, ?)", (obj_id, obj_type, data))

    def append_journal_op(self, timestamp: int, op_data: bytes) -> int:
        if not self.conn: raise ConnectionError("Database not connected.")
        with self.conn:
            cursor = self.conn.execute("INSERT INTO journal (ts, op) VALUES (?, ?)", (timestamp, op_data))
            return cursor.lastrowid

    def get_journal_ops_after(self, seq: int) -> List[Tuple[int, bytes]]:
        if not self.conn: raise ConnectionError("Database not connected.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT seq, op FROM journal WHERE seq > ? ORDER BY seq ASC", (seq,))
        return cursor.fetchall()

    def get_last_journal_seq(self) -> int:
        if not self.conn: raise ConnectionError("Database not connected.")
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(seq) FROM journal")
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0

    def truncate_journal_before(self, seq: int):
        if not self.conn: raise ConnectionError("Database not connected.")
        with self.conn:
            self.conn.execute("DELETE FROM journal WHERE seq <= ?", (seq,))
