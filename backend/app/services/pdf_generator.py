"""
PDF Generator - Create A3/A4 PDF reports with map images
"""
from reportlab.lib.pagesizes import A3, A4, landscape, portrait
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from io import BytesIO
from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import os


class PDFGenerator:
    """Generate PDF reports with map images"""

    def __init__(
        self,
        paper_size: str = "A3",
        orientation: str = "landscape"
    ):
        self.paper_size = paper_size
        self.orientation = orientation

        # Set page size
        if paper_size == "A3":
            base_size = A3
        else:
            base_size = A4

        if orientation == "landscape":
            self.page_size = landscape(base_size)
        else:
            self.page_size = portrait(base_size)

        self.width, self.height = self.page_size

        # Create output directory
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

        # Initialize PDF buffer
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=self.page_size)

        # Colors
        self.primary_color = HexColor("#1565c0")
        self.secondary_color = HexColor("#424242")
        self.background_color = HexColor("#fafafa")
        self.border_color = HexColor("#333333")

        # Layout dimensions (in mm, converted to points)
        self.margin = 8 * mm
        self.info_panel_width = 80 * mm
        self.title_height = 35 * mm

        # Track temp files for cleanup
        self.temp_files = []
        self.page_counter = 0

    def add_page(
        self,
        title: str,
        subtitle: Optional[str] = None,
        map_image: Optional[bytes] = None,
        location: Optional[Dict] = None,
        scale: int = 2500,
        page_number: int = 1,
        total_pages: int = 1
    ):
        """Add a page to the PDF"""
        c = self.canvas

        # Calculate areas
        map_area_width = self.width - self.info_panel_width - self.margin
        map_area_height = self.height - (2 * self.margin)

        # Draw map area background
        c.setFillColor(HexColor("#e8f4e8"))
        c.rect(
            self.margin,
            self.margin,
            map_area_width - self.margin,
            map_area_height,
            fill=True,
            stroke=False
        )

        # Draw map image if provided
        if map_image:
            self._draw_map_image(
                map_image,
                self.margin + 1*mm,
                self.margin + 1*mm,
                map_area_width - self.margin - 2*mm,
                map_area_height - 2*mm
            )
        else:
            # Draw placeholder
            self._draw_map_placeholder(
                title,
                self.margin + 1*mm,
                self.margin + 1*mm,
                map_area_width - self.margin - 2*mm,
                map_area_height - 2*mm
            )

        # Draw north arrow
        self._draw_north_arrow(
            self.margin + 15*mm,
            self.height - self.margin - 15*mm
        )

        # Draw scale bar
        self._draw_scale_bar(
            self.margin + 15*mm,
            self.margin + 15*mm,
            scale
        )

        # Draw info panel background
        info_x = self.width - self.info_panel_width - self.margin
        c.setFillColor(self.background_color)
        c.rect(
            info_x,
            self.margin,
            self.info_panel_width,
            map_area_height,
            fill=True,
            stroke=True
        )

        # Draw title block
        self._draw_title_block(
            info_x,
            self.height - self.margin - self.title_height,
            title,
            subtitle
        )

        # Draw location info
        y_pos = self.height - self.margin - self.title_height - 5*mm
        y_pos = self._draw_info_section(
            info_x + 4*mm,
            y_pos,
            location,
            scale,
            page_number,
            total_pages
        )

        # Draw legend
        y_pos = self._draw_legend(info_x + 4*mm, y_pos - 10*mm)

        # Draw company block at bottom
        self._draw_company_block(
            info_x,
            self.margin,
            page_number,
            total_pages
        )

        # Finish page
        c.showPage()

    def _draw_map_image(self, image_bytes: bytes, x: float, y: float, width: float, height: float):
        """Draw map image on the page"""
        try:
            img = Image.open(BytesIO(image_bytes))
            # Use unique filename per page to prevent ReportLab from reusing cached image
            self.page_counter += 1
            img_path = self.output_dir / f"temp_map_page_{self.page_counter}.png"
            img.save(img_path, "PNG")
            self.temp_files.append(img_path)  # Track for cleanup

            self.canvas.drawImage(
                str(img_path),
                x, y,
                width=width,
                height=height,
                preserveAspectRatio=True,
                anchor='c'
            )
        except Exception as e:
            print(f"Error drawing map image: {e}")
            self._draw_map_placeholder("Map laden mislukt", x, y, width, height)

    def _draw_map_placeholder(self, text: str, x: float, y: float, width: float, height: float):
        """Draw placeholder when no map image available"""
        c = self.canvas

        # Draw background pattern
        c.setStrokeColor(HexColor("#cccccc"))
        c.setLineWidth(0.5)
        for i in range(int(width / (10*mm)) + 1):
            c.line(x + i*10*mm, y, x + i*10*mm, y + height)
        for i in range(int(height / (10*mm)) + 1):
            c.line(x, y + i*10*mm, x + width, y + i*10*mm)

        # Draw centered text
        c.setFillColor(HexColor("#2e7d32"))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(x + width/2, y + height/2, text)

    def _draw_north_arrow(self, x: float, y: float):
        """Draw north arrow"""
        c = self.canvas
        size = 10 * mm

        # White background circle
        c.setFillColor(white)
        c.circle(x, y, size/2, fill=True, stroke=True)

        # Arrow using path
        c.setFillColor(black)
        p = c.beginPath()
        p.moveTo(x, y + size/2 - 2*mm)
        p.lineTo(x - 3*mm, y - 2*mm)
        p.lineTo(x, y)
        p.lineTo(x + 3*mm, y - 2*mm)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # N label
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x, y - size/2 + 2*mm, "N")

    def _draw_scale_bar(self, x: float, y: float, scale: int):
        """Draw scale bar"""
        c = self.canvas

        # Background
        c.setFillColor(white)
        c.rect(x - 5*mm, y - 5*mm, 90*mm, 15*mm, fill=True, stroke=True)

        # Scale segments
        segment_width = 20 * mm
        for i in range(4):
            c.setFillColor(black if i % 2 == 0 else white)
            c.rect(x + i*segment_width, y, segment_width, 4*mm, fill=True, stroke=True)

        # Scale labels
        c.setFillColor(black)
        c.setFont("Helvetica", 7)

        # Calculate real-world distance per segment (in meters)
        # segment_width in mm * scale / 1000 = meters
        meters_per_segment = (20 * scale) / 1000

        for i in range(5):
            distance = int(i * meters_per_segment)
            label = f"{distance}m" if distance < 1000 else f"{distance/1000:.1f}km"
            c.drawCentredString(x + i*segment_width, y - 3*mm, label)

    def _draw_title_block(self, x: float, y: float, title: str, subtitle: Optional[str]):
        """Draw title block"""
        c = self.canvas
        width = self.info_panel_width

        # Header background
        c.setFillColor(self.primary_color)
        c.rect(x, y, width, self.title_height, fill=True, stroke=True)

        # Title
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + width/2, y + self.title_height - 10*mm, "GIS2BIM OpenAnalysis")

        c.setFont("Helvetica", 9)
        c.drawCentredString(x + width/2, y + self.title_height - 16*mm, "Locatie Rapport")

        # Subtitle
        if subtitle:
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x + width/2, y + self.title_height - 25*mm, title)
            c.setFont("Helvetica", 8)
            c.drawCentredString(x + width/2, y + self.title_height - 31*mm, subtitle)
        else:
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(x + width/2, y + self.title_height - 28*mm, title)

    def _draw_info_section(
        self,
        x: float,
        y: float,
        location: Optional[Dict],
        scale: int,
        page_number: int,
        total_pages: int
    ) -> float:
        """Draw location info section, returns y position after drawing"""
        c = self.canvas
        row_height = 5 * mm
        label_width = 25 * mm

        info_items = [
            ("Tekening", f"{page_number} / {total_pages}"),
            ("Adres", location.get("address", "-") if location else "-"),
            ("Gemeente", location.get("municipality", "-") if location else "-"),
            ("Lat/Lng", f"{location.get('lat', 0):.5f}, {location.get('lng', 0):.5f}" if location else "-"),
            ("Schaal", f"1:{scale:,}".replace(",", ".")),
            ("Formaat", f"{self.paper_size} {'liggend' if self.orientation == 'landscape' else 'staand'}"),
            ("Datum", datetime.now().strftime("%d-%m-%Y")),
        ]

        for label, value in info_items:
            y -= row_height

            # Label background
            c.setFillColor(HexColor("#f5f5f5"))
            c.rect(x, y, label_width, row_height, fill=True, stroke=False)

            # Label
            c.setFillColor(HexColor("#555555"))
            c.setFont("Helvetica-Bold", 7)
            c.drawString(x + 2*mm, y + 1.5*mm, label)

            # Value
            c.setFillColor(black)
            c.setFont("Helvetica", 7)

            # Truncate long values
            max_chars = 25
            display_value = value[:max_chars] + "..." if len(value) > max_chars else value
            c.drawString(x + label_width + 2*mm, y + 1.5*mm, display_value)

            # Border
            c.setStrokeColor(HexColor("#dddddd"))
            c.line(x, y, x + self.info_panel_width - 8*mm, y)

        return y

    def _draw_legend(self, x: float, y: float) -> float:
        """Draw legend section"""
        c = self.canvas
        item_height = 5 * mm

        # Header
        c.setFillColor(self.secondary_color)
        c.rect(x - 4*mm, y - 5*mm, self.info_panel_width, 7*mm, fill=True, stroke=True)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y - 2*mm, "Legenda")

        y -= 12 * mm

        legend_items = [
            ("#81c784", "Groenvoorziening"),
            ("#90caf9", "Water"),
            ("#ffcc80", "Bebouwd gebied"),
            ("#e0e0e0", "Verharding"),
            ("#d32f2f", "Locatie marker"),
        ]

        for color, label in legend_items:
            # Color box
            c.setFillColor(HexColor(color))
            c.rect(x, y, 8*mm, 4*mm, fill=True, stroke=True)

            # Label
            c.setFillColor(black)
            c.setFont("Helvetica", 7)
            c.drawString(x + 11*mm, y + 1*mm, label)

            y -= item_height

        return y

    def _draw_company_block(self, x: float, y: float, page_number: int, total_pages: int):
        """Draw company info block at bottom"""
        c = self.canvas
        height = 25 * mm
        width = self.info_panel_width

        # Logo area
        c.setFillColor(self.primary_color)
        c.rect(x, y + height - 10*mm, width, 10*mm, fill=True, stroke=True)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + width/2, y + height - 7*mm, "GIS2BIM")

        # Info
        c.setFillColor(HexColor("#666666"))
        c.setFont("Helvetica", 6)
        c.drawCentredString(x + width/2, y + height - 15*mm, "OpenAEC Foundation")
        c.drawCentredString(x + width/2, y + height - 19*mm, "www.openaec.org")

        # Page number
        c.setFillColor(HexColor("#f5f5f5"))
        c.rect(x, y, width, 6*mm, fill=True, stroke=True)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + width/2, y + 1.5*mm, f"Tekening {page_number} van {total_pages}")

    def _cleanup_temp_files(self):
        """Remove temporary image files"""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
        self.temp_files = []

    def save(self, filename: str) -> Path:
        """Save the PDF to file"""
        self.canvas.save()

        output_path = self.output_dir / filename
        with open(output_path, "wb") as f:
            f.write(self.buffer.getvalue())

        # Cleanup temp files
        self._cleanup_temp_files()

        return output_path

    def get_bytes(self) -> bytes:
        """Get PDF as bytes"""
        self.canvas.save()
        pdf_bytes = self.buffer.getvalue()

        # Cleanup temp files
        self._cleanup_temp_files()

        return pdf_bytes
