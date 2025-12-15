# AsciiCanvas File Format (*.asciicanvas)

The AsciiCanvas document is a single SQLite file. The file extension is `.asciicanvas`.

## 1. Pragmas and Setup

The database is initialized with the following settings to ensure performance and durability:

- **`journal_mode = WAL`**: Write-Ahead Logging is enabled to allow for high-performance writes and concurrent reads without locking the database. This is critical for the journaling mechanism.
- **`synchronous = NORMAL`**: In WAL mode, this provides a good balance between safety and speed. The OS will handle syncing writes to disk.

## 2. SQLite Schema

### `meta` table

Stores key-value metadata for the document.

```sql
CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value BLOB
);
```

| Key | Description | Value Type |
|---|---|---|
| `version` | File format version. | Integer |
| `last_journal_seq` | The sequence number of the last journal entry successfully compacted during a checkpoint. | Integer |
| `...` | Other document-level settings can be stored here. | BLOB |

### `chunks` table

Stores the cell data for each non-empty chunk on the canvas.

```sql
CREATE TABLE chunks (
    cx INT,
    cy INT,
    data BLOB,
    PRIMARY KEY(cx, cy)
);
```

- `cx`, `cy`: The integer coordinates of the chunk. The world coordinate `(x, y)` is in chunk `(floor(x/128), floor(y/128))`.
- `data`: The serialized and compressed data for the chunk.

### `objects` table

Stores data for higher-level objects like tables, math formulas, and page frames.

```sql`
CREATE TABLE objects (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    data BLOB
);
```

- `id`: A unique identifier for the object (e.g., a UUID). This ID is referenced by the `owner` property of cells.
- `type`: A string identifying the object type (e.g., "table", "math", "page_frame").
- `data`: Serialized and compressed data specific to the object type.

### `journal` table

An append-only log of all operations that modify the document state. This is the core of the autosave and crash recovery system.

```sql
CREATE TABLE journal (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INT NOT NULL,
    op BLOB
);
```

- `seq`: A monotonically increasing sequence number for ordering operations.
- `ts`: A Unix timestamp (integer) of when the operation occurred.
- `op`: The serialized operation itself.

## 3. Chunk Data Serialization

The `data` BLOB in the `chunks` table is created through a two-step process:

1.  **Serialization:** The chunk's cell data is stored in a dictionary of dictionaries and then serialized using `msgpack`. Only non-default values are stored.

    ```python
    chunk_data = {
        "chars": {(lx, ly): "A", ...},  # (lx, ly) are local to the chunk (0-127)
        "fg":    {(lx, ly): 1, ...},
        "bg":    {(lx, ly): 2, ...},
        "owner": {(lx, ly): "obj_id_1", ...}
    }
    serialized_data = msgpack.packb(chunk_data)
    ```

2.  **Compression:** The serialized `msgpack` byte string is then compressed using `zstd`. If `zstd` is unavailable, `gzip` is used as a fallback.

The reverse process (decompress then deserialize) is used when loading chunks.

## 4. Journal Operation (`op`) Serialization

The `op` BLOB in the `journal` table is a `msgpack`-serialized dictionary representing a single, reversible user action.

Example operation for setting a cell's character:

```python
op = {
    "type": "SET_CHAR",
    "pos": (x, y),
    "new_ch": "A",
    "old_ch": " "  # Store old value for undo
}
serialized_op = msgpack.packb(op)
```

This structure ensures that every operation is atomic and can be easily replayed to reconstruct state or reversed for the undo/redo feature.
