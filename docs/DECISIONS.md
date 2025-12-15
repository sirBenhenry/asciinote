# AsciiCanvas Design Decisions

This document records the choices made when interpreting ambiguous requirements from the project prompt.

1.  **Project Name:** The prompt refers to "AsciiCanvas" but my tooling has created a project named "asciinote". I will proceed with the name "asciinote" but the deliverables will match the "AsciiCanvas" functionality.

2.  **Font Bundling:** The prompt specifies bundling DejaVu Sans Mono TTF. For initial development, I will rely on the system-installed font. Bundling will be implemented during the packaging phase. This is to simplify the initial setup.

3.  **Undo/Redo Stack:** The prompt requires a minimum of 100 undo steps. The undo/redo mechanism will be implemented using the journal. Each journal entry that represents a state change will be an undoable action. The undo stack will be capped at a configurable limit (defaulting to 100) to manage memory.

4.  **Backspace in Insert Mode:** The "bounded row segment" for pulling text left is capped at 500 cells. This is a hard limit to prevent performance degradation on extremely long lines of text. The search for a boundary (table border, 5+ spaces) will occur within this 500-cell lookbehind limit.

5.  **Math Auto-formatting Triggers:** The "finish signal" for math formatting is defined as leaving the math object's region. This includes moving the cursor outside the object's bounding box, switching modes, or clicking outside the object. This provides a clear and predictable user experience.

6.  **Table Growth and Push-down:** The "local collision" policy is critical. The horizontal band for collision detection is defined as the table's x-range plus a 2-cell padding on each side. This prevents objects far to the left or right from being affected. The push-down will be a "greedy" cascade: push the first colliding object, then check if that object's new position causes another collision, and repeat until no more collisions are found within the band.

7.  **Default Colors:** The 5 preset colors are not specified. I will choose a set of 5 distinct, aesthetically pleasing colors that work well in both light and dark modes. A default palette will be: Blue, Green, Yellow, Red, Purple. Pastel versions for filled shapes will be lighter shades of these colors.

8.  **AUR Package:** The `PKGBUILD` will be created to the best of my ability, but may require manual adjustment by an Arch Linux user for final publishing. It will pull from a specified git commit hash.

9.  **Windows Compatibility:** While the code will be cross-platform (using `pathlib` for paths, etc.), no specific testing or packaging for Windows will be performed initially. The focus is Linux-first.

10. **Initial File Structure:** I am creating a flat structure for the `src/asciicanvas` directory for simplicity. As the project grows, I will refactor it into sub-packages (e.g., `model`, `ui`, `storage`).
