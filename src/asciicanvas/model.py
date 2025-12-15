import uuid
from typing import Dict, Tuple, Optional, NamedTuple, Any, List
import msgpack
import time
from collections import deque

from .database import Database, compress_data, decompress_data
from .math_parser import parse_math, ASTNode, Number, Fraction, Exponent, Root

CHUNK_SIZE = 128
CHECKPOINT_INTERVAL = 2000
UNDO_LIMIT = 100

class Cell(NamedTuple):
    ch: str = ' '
    fg: Optional[int] = None
    bg: Optional[int] = None
    owner: Optional[str] = None

class AsciiObject:
    def __init__(self, obj_id: str = None):
        self.id = obj_id or str(uuid.uuid4())
        self.type = self.__class__.__name__
    def to_dict(self) -> Dict[str, Any]: raise NotImplementedError
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AsciiObject': raise NotImplementedError
    def render(self) -> List[Tuple[int, int, Cell]]: raise NotImplementedError
    def get_bounding_box(self) -> Tuple[int, int, int, int]: raise NotImplementedError

class Table(AsciiObject):
    def __init__(self, x: int, y: int, rows: int, cols: int, cell_w: int, cell_h: int, obj_id: str = None):
        super().__init__(obj_id)
        self.x, self.y, self.rows, self.cols, self.cell_w, self.cell_h = x, y, rows, cols, cell_w, cell_h
    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        return self.x, self.y, self.x + self.cols * (self.cell_w + 1), self.y + self.rows * (self.cell_h + 1)
    def to_dict(self) -> Dict[str, Any]:
        return {'id': self.id, 'type': self.type, 'x': self.x, 'y': self.y, 'rows': self.rows, 'cols': self.cols, 'cell_w': self.cell_w, 'cell_h': self.cell_h}
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Table':
        return cls(data['x'], data['y'], data['rows'], data['cols'], data['cell_w'], data['cell_h'], data['id'])
    def render(self) -> List[Tuple[int, int, Cell]]:
        cells = []
        for r in range(self.rows + 1):
            for c in range(self.cols + 1):
                if r < self.rows:
                    for i in range(self.cell_w):
                        px, py = self.x + c * (self.cell_w + 1), self.y + r * (self.cell_h + 1) + i + 1
                        cells.append((px, py, Cell(ch='│', owner=self.id)))
                if c < self.cols:
                    for i in range(self.cell_h):
                        px, py = self.x + c * (self.cell_w + 1) + i + 1, self.y + r * (self.cell_h + 1)
                        cells.append((px, py, Cell(ch='─', owner=self.id)))
        return cells

class Math(AsciiObject):
    def __init__(self, x: int, y: int, raw_text: str, obj_id: str = None):
        super().__init__(obj_id)
        self.x, self.y, self.raw_text = x, y, raw_text
    def to_dict(self) -> Dict[str, Any]:
        return {'id': self.id, 'type': self.type, 'x': self.x, 'y': self.y, 'raw_text': self.raw_text}
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Math':
        return cls(data['x'], data['y'], data['raw_text'], data['id'])
    def render(self) -> List[Tuple[int, int, Cell]]:
        return [(self.x + i, self.y, Cell(ch=c, owner=self.id)) for i, c in enumerate(self.raw_text)]
    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        return self.x, self.y, self.x + len(self.raw_text), self.y

class PageFrame(AsciiObject):
    def __init__(self, x: int, y: int, width: int, height: int, obj_id: str = None):
        super().__init__(obj_id)
        self.x, self.y, self.width, self.height = x, y, width, height
    def to_dict(self) -> Dict[str, Any]:
        return {'id': self.id, 'type': self.type, 'x': self.x, 'y': self.y, 'width': self.width, 'height': self.height}
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PageFrame':
        return cls(data['x'], data['y'], data['width'], data['height'], data['id'])
    def render(self) -> List[Tuple[int, int, Cell]]:
        cells = []
        for i in range(self.width):
            cells.append((self.x + i, self.y, Cell(ch='-')))
            cells.append((self.x + i, self.y + self.height - 1, Cell(ch='-')))
        for i in range(self.height):
            cells.append((self.x, self.y + i, Cell(ch='|')))
            cells.append((self.x + self.width - 1, self.y + i, Cell(ch='|')))
        return cells
    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        return self.x, self.y, self.x + self.width, self.y + self.height

class Chunk:
    def __init__(self, cx: int, cy: int):
        self.cx, self.cy = cx, cy
        self.cells: Dict[Tuple[int, int], Cell] = {}
        self.dirty = False
    def get_cell(self, lx: int, ly: int) -> Cell: return self.cells.get((lx, ly), Cell())
    def set_cell(self, lx: int, ly: int, cell: Cell):
        if cell == Cell():
            if (lx, ly) in self.cells: del self.cells[(lx, ly)]
        else: self.cells[(lx, ly)] = cell
        self.dirty = True
    def serialize(self) -> bytes:
        data = {'chars': {(lx, ly): c.ch for (lx, ly), c in self.cells.items() if c.ch != ' '}}
        return compress_data(msgpack.packb(data, use_bin_type=True))
    @classmethod
    def deserialize(cls, cx: int, cy: int, data: bytes) -> 'Chunk':
        chunk = cls(cx, cy)
        unpacked = msgpack.unpackb(decompress_data(data), raw=False)
        for (lx, ly), ch in unpacked.get('chars', {}).items():
            chunk.cells[(lx, ly)] = Cell(ch=ch)
        return chunk

class Canvas:
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.objects: Dict[str, AsciiObject] = {}
        self.last_checkpoint_seq = 0
        self.undo_stack: deque[Dict] = deque(maxlen=UNDO_LIMIT)
        self.redo_stack: deque[Dict] = deque(maxlen=UNDO_LIMIT)

    def load(self):
        self.db.connect()
        self.db.create_tables()
        for obj_id, obj_type, obj_data in self.db.get_all_objects():
            obj_data_unpacked = msgpack.unpackb(decompress_data(obj_data), raw=False)
            if obj_type == 'Table': self.objects[obj_id] = Table.from_dict(obj_data_unpacked)
            elif obj_type == 'Math': self.objects[obj_id] = Math.from_dict(obj_data_unpacked)
            elif obj_type == 'PageFrame': self.objects[obj_id] = PageFrame.from_dict(obj_data_unpacked)
        last_seq_bytes = self.db.get_meta('last_checkpoint_seq')
        if last_seq_bytes: self.last_checkpoint_seq = int(last_seq_bytes.decode())
        self._replay_journal()

    def _replay_journal(self):
        ops = self.db.get_journal_ops_after(self.last_checkpoint_seq)
        for seq, op_data in ops:
            op = msgpack.unpackb(op_data, raw=False)
            self.apply_operation(op)
            if 'old_cell' in op or op.get('type') == 'CREATE_OBJECT':
                self.undo_stack.append(op)

    def close(self):
        if self.db.conn: self.perform_checkpoint(); self.db.close()

    def apply_operation(self, op: Dict[str, Any]):
        op_type = op.get('type')
        if op_type == 'SET_CELL':
            self.set_cell(op['x'], op['y'], Cell(*op['new_cell']))
        elif op_type == 'CREATE_OBJECT':
            obj_data = op['obj_data']
            obj_type = obj_data['type']
            if obj_type == 'Table': obj = Table.from_dict(obj_data)
            elif obj_type == 'Math': obj = Math.from_dict(obj_data)
            elif obj_type == 'PageFrame': obj = PageFrame.from_dict(obj_data)
            else: return
            self.objects[obj.id] = obj
            for x, y, cell in obj.render(): self.set_cell(x, y, cell)

    def get_cell(self, x: int, y: int) -> Cell:
        cx, cy = x // CHUNK_SIZE, y // CHUNK_SIZE
        chunk = self.get_chunk(cx, cy)
        return chunk.get_cell(x % CHUNK_SIZE, y % CHUNK_SIZE)

    def get_chunk(self, cx: int, cy: int) -> Chunk:
        if (cx, cy) not in self.chunks:
            chunk_data = self.db.get_chunk(cx, cy)
            if chunk_data: self.chunks[(cx, cy)] = Chunk.deserialize(cx, cy, chunk_data)
            else: self.chunks[(cx, cy)] = Chunk(cx, cy)
        return self.chunks[(cx, cy)]
    
    def set_cell(self, x: int, y: int, cell: Cell):
        cx, cy = x // CHUNK_SIZE, y // CHUNK_SIZE
        chunk = self.get_chunk(cx, cy)
        chunk.set_cell(x % CHUNK_SIZE, y % CHUNK_SIZE, cell)
        
    def log_and_apply_operation(self, op: Dict[str, Any]):
        if op['type'] == 'SET_CELL':
            # FIX: Convert dict_values to a list for serialization
            op['old_cell'] = list(self.get_cell(op['x'], op['y'])._asdict().values())
        self._execute_and_log_op(op)
        self.undo_stack.append(op)
        self.redo_stack.clear()

    def _execute_and_log_op(self, op: Dict[str, Any]):
        self.apply_operation(op)
        packed_op = msgpack.packb(op, use_bin_type=True)
        op_seq = self.db.append_journal_op(int(time.time()), packed_op)
        if op_seq - self.last_checkpoint_seq >= CHECKPOINT_INTERVAL:
            self.perform_checkpoint()
            
    def create_object(self, obj: AsciiObject):
        self.objects[obj.id] = obj
        creation_op = {'type': 'CREATE_OBJECT', 'obj_data': obj.to_dict()}
        self.log_and_apply_operation(creation_op)
        for x, y, cell in obj.render():
            op = {"type": "SET_CELL", "x": x, "y": y, "new_cell": list(cell._asdict().values())}
            self.log_and_apply_operation(op)
            
    def perform_checkpoint(self):
        #...
        pass
