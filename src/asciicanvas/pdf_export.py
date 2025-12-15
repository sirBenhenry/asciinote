from reportlab.pdfgen import canvas as reportlab_canvas
from reportlab.lib import pagesizes
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .model import Canvas, PageFrame

def export_to_pdf(canvas: Canvas, output_path: str):
    """Exports the content of all page frames to a PDF."""
    
    # In a real app, the font would be bundled. For now, assume it's available.
    # pdfmetrics.registerFont(TTFont('DejaVuSansMono', 'path/to/font.ttf'))

    c = reportlab_canvas.Canvas(output_path, pagesize=pagesizes.a4)
    width, height = pagesizes.a4

    page_frames = sorted(
        [obj for obj in canvas.objects.values() if isinstance(obj, PageFrame)],
        key=lambda p: (p.y, p.x)
    )

    for frame in page_frames:
        # This is a simplified rendering. A real implementation would need
        # to calculate cell size and handle colors.
        char_width = 6
        char_height = 12
        
        y_pos = height - 50 # Start from top
        
        for r in range(frame.height):
            text_line = ""
            for col in range(frame.width):
                cell = canvas.get_cell(frame.x + col, frame.y + r)
                text_line += cell.ch
            
            c.drawString(50, y_pos, text_line)
            y_pos -= char_height
            
            if y_pos <= 50:
                c.showPage()
                y_pos = height - 50

        c.showPage()

    c.save()
