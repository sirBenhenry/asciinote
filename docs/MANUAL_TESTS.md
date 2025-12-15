# Manual Test Checklist

This document provides a checklist for manually testing the core features of AsciiCanvas.

## 1. Basic Editing
- [ ] Open the application.
- [ ] Enter `TEXT` mode (`i`).
- [ ] Type a sentence.
- [ ] Use `Backspace` and `Delete`.
- [ ] Move the cursor with `h/j/k/l`.
- [ ] Exit to `NAV` mode (`Esc`).
- [ ] The document saves automatically. Close and reopen to verify.

## 2. Selection and Clipboard
- [ ] Enter `NAV` mode.
- [ ] Start selection (`v`).
- [ ] Move the cursor to select a rectangle of text.
- [ ] Copy the selection (`y`).
- [ ] Move the cursor to a new location.
- [ ] Paste the selection (`p`).
- [ ] Verify the pasted content is correct.
- [ ] Undo the paste (`u`).
- [ ] Redo the paste (`Ctrl+R`).

## 3. Shapes
- [ ] Enter `SHAPE` mode (`s`).
- [ ] Draw a line (`l`, move, `Enter`).
- [ ] Draw a rectangle (`r`, move, `Enter`).
- [ ] Cancel a shape drawing (`Esc`).

## 4. Tables
- [ ] Enter `SHAPE` mode (`s`).
- [ ] Start table tool (`t`, type `10,5`, `Enter`).
- [ ] Draw a rectangle to define the table area.
- [ ] Verify the table is created.

## 5. Math
- [ ] Enter `MATH` mode (`m`).
- [ ] Type `a/b`, then `Enter`. Verify the fraction is rendered.
- [ ] Type `x^2`, then `Enter`. Verify the exponent is rendered.

## 6. UI Elements
- [ ] Open the Command Palette (`Ctrl+P`).
- [ ] Toggle the minimap.
- [ ] Toggle the side panel.
- [ ] View keybindings (`?`).

## 7. PDF Export
- [ ] Create a `PageFrame` object (`s`, `p`, draw rectangle).
- [ ] Open the Command Palette (`Ctrl+P`).
- [ ] Select "Export to PDF".
- [ ] Save the PDF.
- [ ] Open the PDF and verify the content.
