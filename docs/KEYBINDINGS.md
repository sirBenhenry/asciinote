# AsciiCanvas Default Keybindings

This document lists the default keybindings for AsciiCanvas. All keybindings are configurable by editing the `keymap.toml` file in the application's data directory.

## Global

| Key | Action |
|---|---|
| `Ctrl+P` | Open Command Palette |
| `Ctrl+Q` | Quit Application |
| `Esc` | Return to NAV mode / Cancel current operation |

## NAV (Navigation) Mode

This is the default mode.

### Movement

| Key | Action |
|---|---|
| `h` / `Left` | Move cursor left |
| `j` / `Down` | Move cursor down |
| `k` / `Up` | Move cursor up |
| `l` / `Right` | Move cursor right |
| `Shift+Left` / `Shift+h` | Jump to previous word start |
| `Shift+Right` / `Shift+l` | Jump to next word start |

### Mode Switching

| Key | Action |
|---|---|
| `i` | Enter TEXT mode at cursor |
| `m` | Enter MATH mode at cursor |
| `s` | Enter SHAPE mode |
| `v` | Enter visual selection mode |

### Editing & Selection

| Key | Action |
|---|---|
| `x` | Delete character at cursor |
| `d` | With selection: delete selection. `dd` for line deletion (future). |
| `y` | With selection: copy (yank) selection |
| `p` | Paste after cursor |
| `P` | Paste before cursor |
| `M` | With selection: move selection |
| `u` | Undo |
| `Ctrl+R` | Redo |

### Colors

| Key Sequence | Action |
|---|---|
| `c` then `1-5` | Set foreground color on selection/cell |
| `b` then `1-5` | Set background color on selection/cell |

### View

| Key | Action |
|---|---|
| `Ctrl+F` | Search canvas |
| `+` / `Ctrl+=` | Zoom in |
| `-` / `Ctrl+-` | Zoom out |
| `0` | Reset zoom to 100% |

## TEXT Mode

Entered with `i` from NAV mode.

| Key | Action |
|---|---|
| Printable Chars | Insert character at cursor |
| `Backspace` | Behavior depends on OVR/INS mode |
| `Delete` | Delete character/word forward |
| `Enter` | Move cursor down one cell |
| `Shift+Enter` | Move down and align to current word start |
| `Ctrl+Enter` | Move down and align to current sentence start |
| `~` (Tilde) | Toggle between Overwrite (OVR) and Insert (INS) mode |

## MATH Mode

Entered with `m` from NAV mode. Behaves like TEXT mode, but with auto-formatting.

| Key | Action |
|---|---|
| `⇔` | (Configurable) Fast insert equivalence symbol |
| `Space`, `Enter`, `Arrow Keys` | Trigger math formatting for the current expression |

## SHAPE Mode

Entered with `s` from NAV mode.

| Key | Action |
|---|---|
| `l` | Select Line tool |
| `a` | Select Arrow tool |
| `r` | Select Rectangle (outline) tool |
| `R` | Select Rectangle (filled) tool |
| `c` | Select Circle/Ellipse (outline) tool |
| `C` | Select Circle/Ellipse (filled) tool |
| `t` | Select Table tool (fixed cell size) |
| `T` | Select Table tool (auto-resize) |
| `Enter` | Set start point (A) or end point (B) to commit shape |
| `Esc` | Cancel shape preview / Exit SHAPE mode |
