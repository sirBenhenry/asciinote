from typing import List, Tuple

from .model import Cell

def get_line_cells(x1: int, y1: int, x2: int, y2: int) -> List[Tuple[int, int, Cell]]:
    """
    Returns the cells for a line using Bresenham's algorithm with box-drawing characters.
    """
    cells = []
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx + dy

    # Determine dominant axis for character choice
    is_steep = abs(y2 - y1) > abs(x2 - x1)

    x, y = x1, y1
    while True:
        # This is a simplified character selection.
        # A real implementation would need to check neighbors to select the correct junction characters.
        if is_steep:
            char = '│'
        else:
            char = '─'
        
        # For diagonal lines, a simple approximation
        if dx != 0 and dy != 0:
            if sx > 0 and sy > 0: char = '╲'
            elif sx < 0 and sy < 0: char = '╲'
            else: char = '╱'

        cells.append((x, y, Cell(ch=char)))

        if x == x2 and y == y2:
            break
        
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
            
    return cells

def get_rect_cells(x1: int, y1: int, x2: int, y2: int, filled: bool) -> List[Tuple[int, int, Cell]]:
    """
    Returns the cells for a rectangle.
    """
    cells = []
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            is_border = (y == min_y or y == max_y or x == min_x or x == max_x)
            
            if not is_border and filled:
                cells.append((x, y, Cell(bg=1))) # Use color 1 for fill
            elif is_border:
                char = ''
                if (x, y) == (min_x, min_y): char = '┌'
                elif (x, y) == (max_x, min_y): char = '┐'
                elif (x, y) == (min_x, max_y): char = '└'
                elif (x, y) == (max_x, max_y): char = '┘'
                elif y == min_y or y == max_y: char = '─'
                elif x == min_x or x == max_x: char = '│'
                cells.append((x, y, Cell(ch=char)))
    return cells
