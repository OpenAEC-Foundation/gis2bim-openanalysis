"""
PDF Generator - Create A3/A4 PDF reports with map images
Professional layout based on engineering drawing standards
"""
from reportlab.lib.pagesizes import A3, A4, landscape, portrait
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white, red
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import os


class PDFGenerator:
    """Generate PDF reports with map images - Professional engineering layout"""

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

        # Colors - Professional scheme
        self.primary_color = HexColor("#1565c0")  # Blue header
        self.accent_color = HexColor("#0d47a1")   # Darker blue
        self.border_color = HexColor("#333333")
        self.light_gray = HexColor("#f5f5f5")
        self.dark_gray = HexColor("#424242")
        self.red_marker = HexColor("#d32f2f")

        # Layout dimensions (in mm, converted to points)
        self.margin = 5 * mm
        self.footer_height = 22 * mm  # Bottom info strip
        self.title_block_width = 120 * mm
        self.info_block_width = 100 * mm

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
        total_pages: int = 1,
        project_number: str = "-",
        reference: str = "-",
        author: str = "GIS2BIM"
    ):
        """Add a page to the PDF with professional engineering layout"""
        c = self.canvas

        # Calculate map area (full width, minus footer)
        map_x = self.margin
        map_y = self.margin + self.footer_height
        map_width = self.width - (2 * self.margin)
        map_height = self.height - self.footer_height - (2 * self.margin)

        # Draw outer border
        c.setStrokeColor(self.border_color)
        c.setLineWidth(1.5)
        c.rect(self.margin, self.margin,
               self.width - 2*self.margin,
               self.height - 2*self.margin,
               fill=False, stroke=True)

        # Draw map image
        if map_image:
            self._draw_map_image(map_image, map_x, map_y, map_width, map_height)
        else:
            self._draw_map_placeholder(title, map_x, map_y, map_width, map_height)

        # Draw location marker in center of map
        if location:
            marker_x = map_x + map_width / 2
            marker_y = map_y + map_height / 2
            self._draw_location_marker(marker_x, marker_y)

        # Draw north arrow (top left of map)
        self._draw_north_arrow(map_x + 15*mm, map_y + map_height - 15*mm)

        # Draw scale bar (bottom left of map, above footer)
        self._draw_scale_bar(map_x + 15*mm, map_y + 10*mm, scale)

        # Draw footer strip (info blocks at bottom)
        self._draw_footer(
            title=title,
            subtitle=subtitle,
            location=location,
            scale=scale,
            page_number=page_number,
            total_pages=total_pages,
            project_number=project_number,
            reference=reference,
            author=author
        )

        # Finish page
        c.showPage()

    def _draw_map_image(self, image_bytes: bytes, x: float, y: float, width: float, height: float):
        """Draw map image on the page"""
        try:
            img = Image.open(BytesIO(image_bytes))
            # Use unique filename per page
            self.page_counter += 1
            img_path = self.output_dir / f"temp_map_page_{self.page_counter}.png"
            img.save(img_path, "PNG")
            self.temp_files.append(img_path)

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
            self._draw_map_placeholder("Kaart laden mislukt", x, y, width, height)

    def _draw_map_placeholder(self, text: str, x: float, y: float, width: float, height: float):
        """Draw placeholder when no map image available"""
        c = self.canvas

        # Light background
        c.setFillColor(HexColor("#e8f4e8"))
        c.rect(x, y, width, height, fill=True, stroke=False)

        # Grid pattern
        c.setStrokeColor(HexColor("#d0d0d0"))
        c.setLineWidth(0.25)
        grid_spacing = 20 * mm
        for i in range(int(width / grid_spacing) + 1):
            c.line(x + i*grid_spacing, y, x + i*grid_spacing, y + height)
        for i in range(int(height / grid_spacing) + 1):
            c.line(x, y + i*grid_spacing, x + width, y + i*grid_spacing)

        # Centered text
        c.setFillColor(self.dark_gray)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(x + width/2, y + height/2, text)

    def _draw_location_marker(self, x: float, y: float):
        """Draw a red location pin marker"""
        c = self.canvas

        # Outer glow/shadow
        c.setFillColor(HexColor("#00000033"))
        c.circle(x + 1, y - 1, 6*mm, fill=True, stroke=False)

        # Red pin
        c.setFillColor(self.red_marker)
        c.setStrokeColor(HexColor("#b71c1c"))
        c.setLineWidth(1)

        # Pin body (teardrop shape using bezier)
        p = c.beginPath()
        p.moveTo(x, y + 8*mm)
        p.curveTo(x - 5*mm, y + 5*mm, x - 5*mm, y, x, y - 3*mm)
        p.curveTo(x + 5*mm, y, x + 5*mm, y + 5*mm, x, y + 8*mm)
        c.drawPath(p, fill=True, stroke=True)

        # White inner circle
        c.setFillColor(white)
        c.circle(x, y + 3*mm, 2.5*mm, fill=True, stroke=False)

    def _draw_north_arrow(self, x: float, y: float):
        """Draw north arrow"""
        c = self.canvas
        size = 12 * mm

        # White background circle with border
        c.setFillColor(white)
        c.setStrokeColor(self.border_color)
        c.setLineWidth(0.5)
        c.circle(x, y, size/2, fill=True, stroke=True)

        # Arrow pointing up
        c.setFillColor(black)
        p = c.beginPath()
        p.moveTo(x, y + size/2 - 2*mm)
        p.lineTo(x - 2.5*mm, y - 1*mm)
        p.lineTo(x, y + 1*mm)
        p.lineTo(x + 2.5*mm, y - 1*mm)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # N label
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x, y - size/2 + 3*mm, "N")

    def _draw_scale_bar(self, x: float, y: float, scale: int):
        """Draw scale bar"""
        c = self.canvas

        # White background box
        c.setFillColor(white)
        c.setStrokeColor(self.border_color)
        c.setLineWidth(0.5)
        c.rect(x - 3*mm, y - 4*mm, 75*mm, 12*mm, fill=True, stroke=True)

        # Scale segments (4 segments)
        segment_width = 15 * mm
        bar_y = y + 2*mm
        for i in range(4):
            c.setFillColor(black if i % 2 == 0 else white)
            c.setStrokeColor(black)
            c.rect(x + i*segment_width, bar_y, segment_width, 3*mm, fill=True, stroke=True)

        # Scale labels
        c.setFillColor(black)
        c.setFont("Helvetica", 6)

        # Calculate meters per segment
        meters_per_segment = (15 * scale) / 1000
        for i in range(5):
            distance = int(i * meters_per_segment)
            label = f"{distance}m" if distance < 1000 else f"{distance/1000:.1f}km"
            c.drawCentredString(x + i*segment_width, y - 2*mm, label)

        # Scale ratio
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y + 6*mm, f"Schaal 1:{scale:,}".replace(",", "."))

    def _draw_footer(
        self,
        title: str,
        subtitle: Optional[str],
        location: Optional[Dict],
        scale: int,
        page_number: int,
        total_pages: int,
        project_number: str,
        reference: str,
        author: str
    ):
        """Draw footer with title block and info table"""
        c = self.canvas
        footer_y = self.margin
        footer_height = self.footer_height

        # Horizontal divider line between map and footer
        c.setStrokeColor(self.border_color)
        c.setLineWidth(1)
        c.line(self.margin, footer_y + footer_height,
               self.width - self.margin, footer_y + footer_height)

        # === LEFT SECTION: Logo and Title ===
        left_x = self.margin
        left_width = self.title_block_width

        # Logo/brand area (blue box)
        c.setFillColor(self.primary_color)
        c.rect(left_x, footer_y, 40*mm, footer_height, fill=True, stroke=True)

        # Logo text
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(left_x + 20*mm, footer_y + footer_height - 8*mm, "GIS2BIM")
        c.setFont("Helvetica", 7)
        c.drawCentredString(left_x + 20*mm, footer_y + footer_height - 13*mm, "OpenAnalysis")
        c.setFont("Helvetica", 5)
        c.drawCentredString(left_x + 20*mm, footer_y + 3*mm, "openaec.org")

        # Title area
        title_x = left_x + 42*mm
        c.setFillColor(self.light_gray)
        c.rect(title_x, footer_y, left_width - 42*mm, footer_height, fill=True, stroke=True)

        # Layer title (large)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 14)
        # Truncate if too long
        display_title = title[:30] + "..." if len(title) > 30 else title
        c.drawString(title_x + 3*mm, footer_y + footer_height - 9*mm, display_title)

        # Subtitle
        if subtitle:
            c.setFont("Helvetica", 8)
            c.drawString(title_x + 3*mm, footer_y + footer_height - 15*mm, subtitle[:40])

        # Location address
        if location:
            c.setFont("Helvetica", 7)
            addr = location.get("address", "")[:50]
            c.drawString(title_x + 3*mm, footer_y + 3*mm, addr)

        # === MIDDLE SECTION: Page number ===
        middle_x = left_x + left_width + 2*mm
        middle_width = 25*mm

        c.setFillColor(self.accent_color)
        c.rect(middle_x, footer_y, middle_width, footer_height, fill=True, stroke=True)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(middle_x + middle_width/2, footer_y + footer_height/2, f"{page_number}")
        c.setFont("Helvetica", 7)
        c.drawCentredString(middle_x + middle_width/2, footer_y + 3*mm, f"van {total_pages}")

        # === RIGHT SECTION: Info table ===
        right_width = self.width - self.margin - middle_x - middle_width - 2*mm
        right_x = middle_x + middle_width + 2*mm

        # Info table background
        c.setFillColor(white)
        c.rect(right_x, footer_y, right_width, footer_height, fill=True, stroke=True)

        # Info table - 2 columns, 4 rows
        col_width = right_width / 2
        row_height = footer_height / 4

        info_data = [
            # Row 1
            [("KENMERK", reference), ("FORMAAT", f"{self.paper_size} {'liggend' if self.orientation == 'landscape' else 'staand'}")],
            # Row 2
            [("SCHAAL", f"1:{scale:,}".replace(",", ".")), ("PROJECTNR", project_number)],
            # Row 3
            [("DATUM", datetime.now().strftime("%d-%m-%Y")), ("WIJZ", "-")],
            # Row 4
            [("AUTEUR", author), ("OPDRACHTGEVER", "-")]
        ]

        for row_idx, row in enumerate(info_data):
            for col_idx, (label, value) in enumerate(row):
                cell_x = right_x + col_idx * col_width
                cell_y = footer_y + footer_height - (row_idx + 1) * row_height

                # Cell border
                c.setStrokeColor(HexColor("#cccccc"))
                c.setLineWidth(0.5)
                c.rect(cell_x, cell_y, col_width, row_height, fill=False, stroke=True)

                # Label (small, gray)
                c.setFillColor(HexColor("#888888"))
                c.setFont("Helvetica", 5)
                c.drawString(cell_x + 2*mm, cell_y + row_height - 3*mm, label)

                # Value
                c.setFillColor(black)
                c.setFont("Helvetica-Bold", 7)
                # Truncate if too long
                display_value = str(value)[:15]
                c.drawString(cell_x + 2*mm, cell_y + 1.5*mm, display_value)

    def add_summary_page(
        self,
        title: str,
        location: Optional[Dict],
        layers: list,
        page_number: int = 1,
        total_pages: int = 1
    ):
        """Add a summary/cover page"""
        c = self.canvas

        # Background
        c.setFillColor(white)
        c.rect(0, 0, self.width, self.height, fill=True, stroke=False)

        # Header bar
        c.setFillColor(self.primary_color)
        c.rect(0, self.height - 50*mm, self.width, 50*mm, fill=True, stroke=False)

        # Title
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(self.width/2, self.height - 25*mm, "Locatie Analyse")
        c.setFont("Helvetica", 16)
        c.drawCentredString(self.width/2, self.height - 38*mm, "GIS2BIM OpenAnalysis Rapport")

        # Location info
        y_pos = self.height - 70*mm
        if location:
            c.setFillColor(black)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(self.width/2, y_pos, location.get("address", "Onbekende locatie"))

            c.setFont("Helvetica", 11)
            y_pos -= 10*mm
            c.drawCentredString(self.width/2, y_pos, f"Gemeente: {location.get('municipality', '-')}")

            y_pos -= 8*mm
            lat = location.get('lat', 0)
            lng = location.get('lng', 0)
            c.drawCentredString(self.width/2, y_pos, f"Coördinaten: {lat:.6f}, {lng:.6f}")

        # Layers list
        y_pos -= 25*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin + 20*mm, y_pos, f"Kaartlagen in dit rapport ({len(layers)}):")

        y_pos -= 8*mm
        c.setFont("Helvetica", 9)
        col_width = (self.width - 60*mm) / 3

        for idx, layer in enumerate(layers):
            col = idx % 3
            row = idx // 3
            x = self.margin + 20*mm + col * col_width
            y = y_pos - row * 6*mm

            layer_name = layer.get("name", layer.get("layerId", f"Laag {idx+1}"))
            c.drawString(x, y, f"• {layer_name[:30]}")

        # Footer
        c.setFillColor(self.light_gray)
        c.rect(0, 0, self.width, 30*mm, fill=True, stroke=False)

        c.setFillColor(self.dark_gray)
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width/2, 18*mm, f"Gegenereerd op {datetime.now().strftime('%d-%m-%Y %H:%M')}")
        c.drawCentredString(self.width/2, 10*mm, "Powered by OpenAEC Foundation • openaec.org")

        c.showPage()

    def add_analysis_page(
        self,
        analysis_data: Dict,
        location: Optional[Dict],
        page_number: int = 1,
        total_pages: int = 1
    ):
        """Add an analysis page with statistics"""
        c = self.canvas

        # Draw outer border
        c.setStrokeColor(self.border_color)
        c.setLineWidth(1.5)
        c.rect(self.margin, self.margin,
               self.width - 2*self.margin,
               self.height - 2*self.margin,
               fill=False, stroke=True)

        # Header bar
        header_height = 25 * mm
        header_y = self.height - self.margin - header_height
        c.setFillColor(self.primary_color)
        c.rect(self.margin, header_y, self.width - 2*self.margin, header_height, fill=True, stroke=True)

        # Title
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(self.width/2, header_y + 8*mm, "Locatie Analyse")

        # Location subtitle
        if location:
            c.setFont("Helvetica", 10)
            addr = location.get("address", "")[:60]
            c.drawCentredString(self.width/2, header_y + 2*mm, addr)

        # Content area
        content_y = header_y - 10*mm
        content_x = self.margin + 10*mm
        content_width = self.width - 2*self.margin - 20*mm

        # Extract data
        buildings = analysis_data.get("buildings", {})
        parcels = analysis_data.get("parcels", {})
        neighborhood = analysis_data.get("neighborhood", {})
        summary = analysis_data.get("summary", {})

        # === SUMMARY BOX ===
        c.setFillColor(HexColor("#e3f2fd"))
        box_height = 20*mm
        c.rect(content_x, content_y - box_height, content_width, box_height, fill=True, stroke=True)

        c.setFillColor(self.dark_gray)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(content_x + 5*mm, content_y - 7*mm, "Samenvatting:")
        c.setFont("Helvetica", 9)
        description = summary.get("beschrijving", "Geen data beschikbaar")
        c.drawString(content_x + 5*mm, content_y - 14*mm, description[:100])

        content_y -= box_height + 15*mm

        # === THREE COLUMN LAYOUT ===
        col_width = content_width / 3 - 5*mm
        col_x = [content_x, content_x + col_width + 5*mm, content_x + 2*(col_width + 5*mm)]

        # Column 1: Buildings
        self._draw_stat_box(c, col_x[0], content_y, col_width, "Panden (BAG)", [
            ("Aantal panden", buildings.get("count", 0)),
            ("Gem. bouwjaar", buildings.get("average_year", "-")),
            ("Oudste pand", buildings.get("oldest_building", "-")),
            ("Nieuwste pand", buildings.get("newest_building", "-")),
        ], self.primary_color)

        # Column 2: Parcels
        self._draw_stat_box(c, col_x[1], content_y, col_width, "Percelen (Kadaster)", [
            ("Aantal percelen", parcels.get("count", 0)),
            ("Totaal oppervlakte", f"{parcels.get('total_area_ha', 0)} ha"),
            ("Totaal m2", f"{parcels.get('total_area_m2', 0):,}".replace(",", ".")),
        ], HexColor("#2e7d32"))

        # Column 3: Neighborhood
        # Format WOZ value
        woz = neighborhood.get("gem_woningwaarde")
        woz_str = f"\u20ac {woz:,.0f}".replace(",", ".") if woz else "-"

        self._draw_stat_box(c, col_x[2], content_y, col_width, "Buurt (CBS)", [
            ("Buurtnaam", neighborhood.get("buurt_naam", "-")),
            ("Gemeente", neighborhood.get("gemeente_naam", "-")),
            ("Inwoners", neighborhood.get("inwoners", "-")),
            ("Gem. WOZ-waarde", woz_str),
        ], HexColor("#c62828"))

        content_y -= 75*mm

        # === AGE DISTRIBUTION CHART ===
        age_dist = buildings.get("age_distribution", {})
        if age_dist and any(age_dist.values()):
            self._draw_age_chart(c, content_x, content_y, content_width, age_dist)
            content_y -= 55*mm

        # === STATUS DISTRIBUTION ===
        status_dist = buildings.get("status_distribution", {})
        if status_dist:
            self._draw_status_table(c, content_x, content_y, content_width/2, status_dist)

        # Footer
        self._draw_footer(
            title="Locatie Analyse",
            subtitle="Statistieken uit BAG, Kadaster en CBS",
            location=location,
            scale=0,
            page_number=page_number,
            total_pages=total_pages,
            project_number="-",
            reference="-",
            author="GIS2BIM"
        )

        c.showPage()

    def _draw_stat_box(self, c, x: float, y: float, width: float, title: str, items: list, color):
        """Draw a statistics box with title and key-value pairs"""
        box_height = 65*mm

        # Box background
        c.setFillColor(white)
        c.setStrokeColor(color)
        c.setLineWidth(2)
        c.rect(x, y - box_height, width, box_height, fill=True, stroke=True)

        # Title bar
        title_height = 10*mm
        c.setFillColor(color)
        c.rect(x, y - title_height, width, title_height, fill=True, stroke=False)

        # Title text
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + width/2, y - 7*mm, title)

        # Items
        item_y = y - title_height - 10*mm
        for label, value in items:
            c.setFillColor(HexColor("#666666"))
            c.setFont("Helvetica", 8)
            c.drawString(x + 5*mm, item_y, str(label))

            c.setFillColor(black)
            c.setFont("Helvetica-Bold", 10)
            display_value = str(value) if value else "-"
            c.drawString(x + 5*mm, item_y - 5*mm, display_value[:20])

            item_y -= 13*mm

    def _draw_age_chart(self, c, x: float, y: float, width: float, age_data: Dict):
        """Draw age distribution bar chart"""
        chart_height = 45*mm

        # Title
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Bouwjaar Verdeling")

        # Background
        chart_y = y - chart_height
        c.setFillColor(HexColor("#fafafa"))
        c.rect(x, chart_y, width, chart_height - 5*mm, fill=True, stroke=True)

        # Bars
        categories = [
            ("voor_1900", "< 1900", HexColor("#8d6e63")),
            ("1900_1945", "1900-1945", HexColor("#7986cb")),
            ("1945_1975", "1945-1975", HexColor("#4db6ac")),
            ("1975_2000", "1975-2000", HexColor("#ffb74d")),
            ("na_2000", "> 2000", HexColor("#81c784")),
        ]

        total = sum(age_data.values()) or 1
        max_val = max(age_data.values()) or 1
        bar_width = (width - 30*mm) / len(categories)
        bar_max_height = chart_height - 20*mm

        for i, (key, label, color) in enumerate(categories):
            value = age_data.get(key, 0)
            bar_height = (value / max_val) * bar_max_height if max_val > 0 else 0

            bar_x = x + 10*mm + i * bar_width
            bar_y = chart_y + 10*mm

            # Bar
            c.setFillColor(color)
            c.rect(bar_x, bar_y, bar_width - 5*mm, bar_height, fill=True, stroke=False)

            # Value on top
            c.setFillColor(black)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(bar_x + (bar_width-5*mm)/2, bar_y + bar_height + 2*mm, str(value))

            # Label below
            c.setFont("Helvetica", 7)
            c.drawCentredString(bar_x + (bar_width-5*mm)/2, chart_y + 3*mm, label)

    def _draw_status_table(self, c, x: float, y: float, width: float, status_data: Dict):
        """Draw status distribution table"""
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "Pand Status Verdeling")

        table_y = y - 8*mm
        row_height = 6*mm

        for status, count in list(status_data.items())[:6]:  # Max 6 items
            c.setFillColor(HexColor("#f5f5f5"))
            c.rect(x, table_y - row_height, width, row_height, fill=True, stroke=True)

            c.setFillColor(black)
            c.setFont("Helvetica", 8)
            c.drawString(x + 3*mm, table_y - row_height + 2*mm, str(status)[:30])

            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(x + width - 3*mm, table_y - row_height + 2*mm, str(count))

            table_y -= row_height

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

        self._cleanup_temp_files()
        return output_path

    def get_bytes(self) -> bytes:
        """Get PDF as bytes"""
        self.canvas.save()
        pdf_bytes = self.buffer.getvalue()
        self._cleanup_temp_files()
        return pdf_bytes
