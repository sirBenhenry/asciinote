# AsciiCanvas Architecture

This document outlines the high-level architecture of the AsciiCanvas application.

## 1. Data Model

The core of the application is the `Canvas` object, which represents the infinite 2D grid of characters.

- **Canvas:** The main logical container for the entire document. It does not store cell data directly but manages `Chunks`.
- **Chunk:** The canvas is divided into fixed-size chunks (128x128 cells) to manage memory and storage efficiently. Chunks are loaded on-demand.
- **Cell:** A cell is the smallest unit on the canvas, containing a character (`ch`), foreground color (`fg`), background color (`bg`), and an optional `owner` ID. Empty cells (containing a space with default colors) are not stored.
- **Objects:** Higher-level entities like tables, math formulas, and page frames are managed as `Objects`. They have a unique ID, a type, and associated data. The `owner` field in a `Cell` links it to an object, enabling object-aware operations.

## 2. Storage Layer

Persistence is handled by a single-file SQLite database with WAL (Write-Ahead Logging) enabled for crash safety and performance.

- **`meta` table:** Stores key-value metadata about the document.
- **`chunks` table:** Stores canvas chunks. Each row contains chunk coordinates (`cx`, `cy`) and serialized cell data.
- **`objects` table:** Stores object metadata and properties.
- **`journal` table:** An append-only log of all state-changing operations. This is critical for autosave, crash recovery, and undo/redo.

Data within the `chunks` and `objects` tables is serialized using `msgpack` for a compact binary representation and compressed with `zstd` to save space.

## 3. Rendering

The canvas is rendered using PySide6 (Qt).

- **Virtualization:** Only the visible portion of the canvas is rendered at any time.
- **Chunk-based Rendering:** The renderer iterates through the chunks that intersect the current viewport, then draws the cells within them.
- **Draw Call Batching:** To optimize performance, render calls are batched. Runs of text with the same styling are drawn together.
- **Minimap:** The minimap provides a high-level overview of the canvas. It is rendered by drawing a block for each chunk, colored based on the density of non-empty cells within that chunk.

## 4. Input and Modes

User input is handled through a state machine that corresponds to the application's modes.

- **NAV (Navigation) Mode:** The default mode for movement and commands. Printable characters are interpreted as commands, not text input.
- **TEXT, MATH, SHAPE Modes:** Specialized modes for inserting and editing content.
- **Keybinding Dispatcher:** A trie-based dispatcher handles multi-key sequences (e.g., `gg` in Vim). Keymaps are configurable per mode via a `keymap.toml` file.
- **Command Palette:** Provides access to less frequent commands.

## 5. Crash Safety and Backups

- **Journaling:** Every user action that modifies the document is immediately appended to the `journal` table in a short, atomic transaction. On startup, the application replays any uncommitted journal entries to restore the last known state.
- **Checkpointing:** Periodically, the journal is compacted into the `chunks` and `objects` tables to keep load times fast.
- **Daily Backups:** On the first launch of a day, any document opened is automatically backed up to a separate folder. The last 3 daily backups are retained.
