"""
Module for generating shipping labels.
Provides a cross-platform implementation: PDF for Windows and PNG for Linux.
"""

import os
import platform
import pathlib
import logging
from datetime import datetime as dt
from typing import Tuple, List

import qrcode
from PIL import Image, ImageDraw, ImageFont

from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from reportlab.graphics.barcode import code39
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

from src.models.schema import OrdemDeProducao

# --- Constants & Paths ---
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
TMP_FOLDER = BASE_DIR / "tmp"
LABELS_FOLDER = TMP_FOLDER / "labels"
LABELS_FOLDER.mkdir(exist_ok=True, parents=True)

FONTS_PATH = BASE_DIR / "src" / "assets" / "fonts"

# Standard Logistic Format (Approx 100mm x 150mm)
LABEL_W_PT, LABEL_H_PT = 428, 283
MWM_W_MM, MWM_H_MM = 105.0, 75.0

DPI = 203
MM_TO_PX = DPI / 25.4
PT_TO_PX = DPI / 72.0

# --- Font Registration ---
try:
    pdfmetrics.registerFont(TTFont("ConsolasRegular", FONTS_PATH / "Consolas-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("FiraCodeRegular", FONTS_PATH / "FiraCode-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("FiraCodeBold", FONTS_PATH / "FiraCode-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("YugoSemiBold", FONTS_PATH / "Yugo-SemiBold.ttc"))
    pdfmetrics.registerFont(TTFont("YugoSemiLight", FONTS_PATH / "Yugo-SemiLight.ttc"))
    pdfmetrics.registerFont(TTFont("LucidaConsoleRegular", FONTS_PATH / "LucidaConsole-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("DubaiBold", FONTS_PATH / "Dubai-Bold.ttf"))
except Exception as e:
    logging.warning("Could not load some ReportLab fonts: %s", e)


# --- Helper Functions ---

def get_pil_font(font_name: str, size_pt: float) -> ImageFont.FreeTypeFont:
    """Loads a TrueType font for Pillow (PNG) rendering."""
    size_px = int(size_pt * PT_TO_PX)
    mappings = {
        "FiraCodeRegular": "FiraCode-Regular.ttf",
        "FiraCodeBold": "FiraCode-Bold.ttf",
        "ConsolasRegular": "Consolas-Regular.ttf",
        "YugoSemiBold": "Yugo-SemiBold.ttc",
        "YugoSemiLight": "Yugo-SemiLight.ttc",
        "LucidaConsoleRegular": "LucidaConsole-Regular.ttf",
        "DubaiBold": "Dubai-Bold.ttf"
    }
    try:
        return ImageFont.truetype(str(FONTS_PATH / mappings.get(font_name, "Arial.ttf")), size_px)
    except IOError:
        return ImageFont.load_default()

def _draw_pdf_qr(c: Canvas, qr_data: str, x: float, y: float, size: float) -> None:
    """Renders a QR code onto a ReportLab Canvas."""
    qr_code = qr.QrCodeWidget(qr_data)
    bounds = qr_code.getBounds()
    w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
    scale = min(size / w, size / h)
    drawing = Drawing(w * scale, h * scale, transform=[scale, 0, 0, scale, 0, 0])
    drawing.add(qr_code)
    drawing.drawOn(c, x, y)


class ShippingLabelGenerator:
    """Handles the routing and generation of production shipping labels."""

    def __init__(self, ordem: OrdemDeProducao):
        self.ordem = ordem
        self.today_date = dt.now()
        self.is_linux = platform.system().lower().startswith("linux")
        self.file_extension = ".png" if self.is_linux else ".pdf"

    def generate(self) -> Tuple[bool, str, List[str]]:
        """Main entry point. Returns success status, error message, and generated paths."""
        if self.ordem.box_count <= 0 or self.ordem.quantity % self.ordem.box_count != 0:
            return False, "Invalid quantity: not divisible by box count.", []

        try:
            if self.is_linux:
                return self._generate_png_files()
            return self._generate_pdf_file()
        except Exception as e:
            logging.exception("Failed to generate shipping label.")
            return False, str(e), []

    # -------------------------------------------------------------------------
    # PDF GENERATION (WINDOWS)
    # -------------------------------------------------------------------------

    def _generate_pdf_file(self) -> Tuple[bool, str, List[str]]:
        """Generates a multi-page PDF document."""
        is_mwm = self.ordem.material_code.startswith("MWM")
        size = (MWM_W_MM * mm, MWM_H_MM * mm) if is_mwm else (LABEL_W_PT, LABEL_H_PT)
        
        output_path = LABELS_FOLDER / f"shipping_{self.ordem.code}{self.file_extension}"
        pdf = Canvas(str(output_path), pagesize=size)

        for index in range(1, self.ordem.box_count + 1):
            if is_mwm:
                self._draw_mwm_pdf(pdf, index)
            else:
                self._draw_normal_pdf(pdf)
            pdf.showPage()
            
        pdf.save()
        return True, "", [str(output_path)]

    def _draw_normal_pdf(self, pdf: Canvas) -> None:
        """Renders the standard logistic grid layout via ReportLab."""
        qty_per_box = self.ordem.quantity / self.ordem.box_count
        pdf.setLineWidth(2)
        
        # Date (Top safe zone)
        pdf.setFont("FiraCodeBold", 12)
        pdf.drawString(10, 222, f"DATA: {self.today_date.strftime('%d/%m/%Y')}")

        # Grid Border
        pdf.rect(5, 5, 410, 210, stroke=1, fill=0)

        # Horizontal Grid Lines
        pdf.line(5, 175, 415, 175)
        pdf.line(5, 100, 415, 100)
        
        # Vertical Grid Lines (Aligned perfectly)
        pdf.line(200, 175, 200, 5)       # Left section separator
        pdf.line(305, 175, 305, 5)       # Continuous right split (Qty|Weight, QR|Icons)

        # Destinatário
        pdf.setFont("FiraCodeRegular", 9)
        pdf.drawString(10, 203, "DESTINATÁRIO:")
        
        c_style = getSampleStyleSheet()["Normal"].clone("Dest")
        c_style.fontName = "FiraCodeBold"
        c_style.fontSize = 12
        c_style.leading = 14
        p_client = Paragraph(self.ordem.client, c_style)
        w, h = p_client.wrapOn(pdf, 400, 25)
        p_client.drawOn(pdf, 10, 200 - h)

        # Material Code
        pdf.setFont("FiraCodeRegular", 10)
        pdf.drawString(10, 158, "CÓDIGO MATERIAL:")
        pdf.setFont("FiraCodeBold", 16)
        pdf.drawString(10, 140, self.ordem.material_code)

        if self.ordem.client_code:
            pdf.setFont("FiraCodeRegular", 9)
            pdf.drawString(10, 115, "CÓD. CLIENTE: ")
            pdf.setFont("FiraCodeBold", 11)
            pdf.drawString(85, 115, self.ordem.client_code)

        # Description
        pdf.setFont("FiraCodeRegular", 10)
        pdf.drawString(10, 85, "DESCRIÇÃO:")
        
        d_style = getSampleStyleSheet()["Normal"].clone("Desc")
        d_style.fontName = "FiraCodeRegular"
        d_style.fontSize = 10
        d_style.leading = 12
        p_desc = Paragraph(self.ordem.description, d_style)
        p_desc.wrapOn(pdf, 185, 65)
        p_desc.drawOn(pdf, 10, 10)

        # Quantity
        pdf.setFont("FiraCodeRegular", 10)
        pdf.drawString(205, 158, "QTD TOTAL:")
        pdf.setFont("FiraCodeBold", 18)
        pdf.drawString(205, 125, f"{qty_per_box:.0f} UN")

        # Weight
        pdf.setFont("FiraCodeRegular", 10)
        pdf.drawString(312, 158, "PESO:")
        pdf.setFont("FiraCodeBold", 18)
        pdf.drawString(312, 125, f"{self.ordem.weight} KG")

        # QR Code
        qr_data = f"{self.ordem.code};{self.ordem.material_code};{int(qty_per_box)}"
        qr_size = 75
        qr_x = 215
        _draw_pdf_qr(pdf, qr_data, qr_x, 15, qr_size)
        pdf.setFont("FiraCodeRegular", 6)
        pdf.drawCentredString(252, 8, "VERIFICAR CONTEÚDO")

        # Instructions / Logistic Icons
        pdf.setFont("FiraCodeRegular", 8)
        pdf.drawCentredString(360, 85, "INSTRUÇÕES:")
        
        self._draw_vector_fragile(pdf, 315, 45)
        self._draw_vector_up(pdf, 365, 45)
        
        pdf.setFont("FiraCodeBold", 7)
        pdf.drawCentredString(332, 35, "FRÁGIL")
        pdf.drawCentredString(382, 35, "P/ CIMA")

    def _draw_vector_fragile(self, pdf: Canvas, x: float, y: float) -> None:
        """Renders the fragile (glass) icon natively in vectors."""
        pdf.setLineWidth(1.5)
        pdf.rect(x, y, 35, 35) 
        pdf.line(x+8, y+28, x+27, y+28)
        pdf.line(x+8, y+28, x+17.5, y+15)
        pdf.line(x+27, y+28, x+17.5, y+15)
        pdf.line(x+17.5, y+15, x+17.5, y+6)
        pdf.line(x+11, y+6, x+24, y+6)

    def _draw_vector_up(self, pdf: Canvas, x: float, y: float) -> None:
        """Renders the this-side-up (arrows) icon natively in vectors."""
        pdf.setLineWidth(1.5)
        pdf.rect(x, y, 35, 35) 
        pdf.line(x+6, y+6, x+29, y+6) 
        pdf.line(x+13, y+6, x+13, y+26)
        pdf.line(x+9, y+20, x+13, y+28)
        pdf.line(x+17, y+20, x+13, y+28)
        pdf.line(x+22, y+6, x+22, y+26)
        pdf.line(x+18, y+20, x+22, y+28)
        pdf.line(x+26, y+20, x+22, y+28)

    def _draw_mwm_pdf(self, pdf: Canvas, index: int) -> None:
        """Renders the specialized MWM label format."""
        mwm_margin = 7.5 * mm
        internal_margin = 21.5 * mm
        qty_per_box = self.ordem.quantity / self.ordem.box_count

        pdf.rect(mwm_margin, 5.5 * mm, 90 * mm, 64 * mm)
        pdf.line(mwm_margin, 43.5 * mm, 105 * mm - mwm_margin, 43.5 * mm)
        pdf.line(mwm_margin, 32.5 * mm, 105 * mm - mwm_margin, 32.5 * mm)
        pdf.line(mwm_margin, 19.5 * mm, 105 * mm - mwm_margin, 19.5 * mm)

        pdf.setFont("YugoSemiBold", 9)
        pdf.drawString(mwm_margin, 69 * mm, "MWM MOTORES E GERADORES")
        pdf.drawString(87 * mm, 69 * mm, "V.2.3.4")
        
        pdf.setFont("LucidaConsoleRegular", 10)
        pdf.drawString(8 * mm, 66 * mm, "Part:")
        pdf.drawString(8 * mm, 40 * mm, "Qty:")
        pdf.drawString(8 * mm, 28.2 * mm, "Lot:")
        pdf.drawString(8 * mm, 15.5 * mm, "ID:")
        
        pdf.setFont("LucidaConsoleRegular", 8)
        pdf.drawString(8 * mm, 43 * mm, "Supplier:15175")
        
        pdf.setFont("YugoSemiBold", 10)
        pdf.drawString(72 * mm, 43.5 * mm, "Date:")
        pdf.setFont("YugoSemiBold", 6)
        pdf.drawString(internal_margin, 54.9 * mm, "fornecedor/fabricante")

        pdf.setFont("YugoSemiLight", 8)
        pdf.drawString(81.2 * mm, 42.8 * mm, self.today_date.strftime("%d/%m/%Y"))
        
        pdf.setFont("ConsolasRegular", 27)
        pdf.drawString(internal_margin, 65 * mm, self.ordem.client_code)
        
        qty_str = f"{qty_per_box:.0f}"
        pdf.setFont("ConsolasRegular", 22.9)
        pdf.drawString(75 * mm, 39 * mm, qty_str)
        
        qty_width = pdf.stringWidth(qty_str, "ConsolasRegular", 22.9)
        pdf.setFont("DubaiBold", 12.5)
        pdf.drawString(75 * mm + qty_width + 2 * mm, 35.2 * mm, "PCs")

        pdf.setFont("YugoSemiBold", 8.2)
        pdf.drawString(internal_margin, 27.8 * mm, str(self.ordem.code))
        id_str = f"15175{self.today_date.strftime('%Y%m%d')}{index:06d}"
        pdf.drawString(internal_margin, 14.8 * mm, id_str)

        barcodes = [
            {"val": self.ordem.client_code, "y": 48 * mm},
            {"val": qty_str, "y": 34 * mm},
            {"val": str(self.ordem.code), "y": 20.3 * mm},
            {"val": id_str, "y": 7 * mm}
        ]
        
        for bc in barcodes:
            if bc["val"]:
                barcode = code39.Standard39(
                    bc["val"], barWidth=0.25 * mm, barHeight=8 * mm, ratio=2.0, checksum=False
                )
                barcode.drawOn(pdf, 15 * mm, bc["y"])

    # -------------------------------------------------------------------------
    # PNG GENERATION (LINUX)
    # -------------------------------------------------------------------------

    def _generate_png_files(self) -> Tuple[bool, str, List[str]]:
        """Generates multiple single-page PNG files for thermal printers."""
        is_mwm = self.ordem.material_code.startswith("MWM")
        w_px = int(MWM_W_MM * MM_TO_PX) if is_mwm else int(LABEL_W_PT * PT_TO_PX)
        h_px = int(MWM_H_MM * MM_TO_PX) if is_mwm else int(LABEL_H_PT * PT_TO_PX)
        
        paths = []
        for index in range(1, self.ordem.box_count + 1):
            img = Image.new("RGB", (w_px, h_px), "white")
            draw = ImageDraw.Draw(img)

            if is_mwm:
                self._draw_mwm_png(draw, img, index)
            else:
                self._draw_normal_png(draw, img)
            
            # Rotates 180 deg to feed correctly into standard Linux thermal setups
            img = img.transpose(Image.Transpose.ROTATE_180)
            
            output_path = LABELS_FOLDER / f"shipping_{self.ordem.code}_{index:03d}.png"
            img.save(output_path)
            paths.append(str(output_path))
            
        return True, "", paths

    def _draw_normal_png(self, draw: ImageDraw.Draw, img: Image) -> None:
        """Renders the standard logistic grid layout via Pillow."""
        qty_per_box = self.ordem.quantity / self.ordem.box_count

        def pt(val): return int(val * PT_TO_PX)
        def y_inv(y_val): return int((LABEL_H_PT - y_val) * PT_TO_PX)
        
        def draw_txt(x_pt, y_pt, text, font_name, size, anchor="ls"):
            font = get_pil_font(font_name, size)
            draw.text((pt(x_pt), y_inv(y_pt)), text, font=font, fill="black", anchor=anchor)

        def wrap_text(text, max_w_pt, font_name, size_pt):
            font = get_pil_font(font_name, size_pt)
            words = text.split()
            lines, current_line = [], ""
            max_w_px = pt(max_w_pt)
            for word in words:
                if draw.textlength(current_line + " " + word, font=font) < max_w_px:
                    current_line += " " + word
                else:
                    lines.append(current_line.strip())
                    current_line = word
            lines.append(current_line.strip())
            return lines

        # Header Date
        draw_txt(10, 222, f"DATA: {self.today_date.strftime('%d/%m/%Y')}", "FiraCodeBold", 12)

        # Border
        draw.rectangle([pt(5), y_inv(215), pt(415), y_inv(5)], outline="black", width=pt(2))

        # Grid Lines (Aligned perfectly)
        draw.line([pt(5), y_inv(175), pt(415), y_inv(175)], fill="black", width=pt(2))
        draw.line([pt(5), y_inv(100), pt(415), y_inv(100)], fill="black", width=pt(2))
        
        draw.line([pt(200), y_inv(175), pt(200), y_inv(5)], fill="black", width=pt(2))
        draw.line([pt(305), y_inv(175), pt(305), y_inv(5)], fill="black", width=pt(2))

        # Destinatário
        draw_txt(10, 203, "DESTINATÁRIO:", "FiraCodeRegular", 9)
        client_lines = wrap_text(self.ordem.client, 400, "FiraCodeBold", 12)
        y_client = 190
        for line in client_lines[:2]:
            draw_txt(10, y_client, line, "FiraCodeBold", 12)
            y_client -= 14

        # Material Details
        draw_txt(10, 158, "CÓDIGO MATERIAL:", "FiraCodeRegular", 10)
        draw_txt(10, 140, self.ordem.material_code, "FiraCodeBold", 16)
        
        if self.ordem.client_code:
            draw_txt(10, 115, "CÓD. CLIENTE: ", "FiraCodeRegular", 9)
            draw_txt(85, 115, self.ordem.client_code, "FiraCodeBold", 11)
        
        # Description
        draw_txt(10, 85, "DESCRIÇÃO:", "FiraCodeRegular", 10)
        desc_lines = wrap_text(self.ordem.description, 185, "FiraCodeRegular", 10)
        y_desc = 70
        for line in desc_lines[:5]:
            draw_txt(10, y_desc, line, "FiraCodeRegular", 10)
            y_desc -= 12

        # Quantity
        draw_txt(205, 158, "QTD TOTAL:", "FiraCodeRegular", 10)
        draw_txt(205, 125, f"{qty_per_box:.0f} UN", "FiraCodeBold", 18)

        # Weight
        draw_txt(312, 158, "PESO:", "FiraCodeRegular", 10)
        draw_txt(312, 125, f"{self.ordem.weight} KG", "FiraCodeBold", 18)

        # QR Code
        qr_data = f"{self.ordem.code};{self.ordem.material_code};{int(qty_per_box)}"
        qr_size_pt = 75
        qr_x_pt = 215
        
        qr_obj = qrcode.QRCode(version=1, box_size=10, border=0)
        qr_obj.add_data(qr_data)
        qr_obj.make(fit=True)
        q_img = qr_obj.make_image(fill_color="black", back_color="white")
        q_img = q_img.resize((pt(qr_size_pt), pt(qr_size_pt)), Image.NEAREST)
        
        img.paste(q_img, (pt(qr_x_pt), y_inv(15 + qr_size_pt)))
        draw_txt(252, 8, "VERIFICAR CONTEÚDO", "FiraCodeRegular", 6, anchor="ms")

        # Logistic Icons
        draw_txt(360, 85, "INSTRUÇÕES:", "FiraCodeRegular", 8, anchor="ms")
        self._draw_vector_fragile_pil(draw, 315, 45)
        self._draw_vector_up_pil(draw, 365, 45)
        
        draw_txt(332, 35, "FRÁGIL", "FiraCodeBold", 7, anchor="ms")
        draw_txt(382, 35, "P/ CIMA", "FiraCodeBold", 7, anchor="ms")


    def _draw_vector_fragile_pil(self, draw: ImageDraw.Draw, x: float, y: float) -> None:
        """Renders the fragile (glass) icon natively in vectors for PIL."""
        def pt(val): return int(val * PT_TO_PX)
        def y_inv(y_val): return int((LABEL_H_PT - y_val) * PT_TO_PX)
        lw = pt(1.5)
        draw.rectangle([pt(x), y_inv(y+35), pt(x+35), y_inv(y)], outline="black", width=lw)
        draw.line([pt(x+8), y_inv(y+28), pt(x+27), y_inv(y+28)], fill="black", width=lw)
        draw.line([pt(x+8), y_inv(y+28), pt(x+17.5), y_inv(y+15)], fill="black", width=lw)
        draw.line([pt(x+27), y_inv(y+28), pt(x+17.5), y_inv(y+15)], fill="black", width=lw)
        draw.line([pt(x+17.5), y_inv(y+15), pt(x+17.5), y_inv(y+6)], fill="black", width=lw)
        draw.line([pt(x+11), y_inv(y+6), pt(x+24), y_inv(y+6)], fill="black", width=lw)

    def _draw_vector_up_pil(self, draw: ImageDraw.Draw, x: float, y: float) -> None:
        """Renders the this-side-up (arrows) icon natively in vectors for PIL."""
        def pt(val): return int(val * PT_TO_PX)
        def y_inv(y_val): return int((LABEL_H_PT - y_val) * PT_TO_PX)
        lw = pt(1.5)
        draw.rectangle([pt(x), y_inv(y+35), pt(x+35), y_inv(y)], outline="black", width=lw)
        draw.line([pt(x+6), y_inv(y+6), pt(x+29), y_inv(y+6)], fill="black", width=lw)
        
        draw.line([pt(x+13), y_inv(y+6), pt(x+13), y_inv(y+26)], fill="black", width=lw)
        draw.line([pt(x+9), y_inv(y+20), pt(x+13), y_inv(y+28)], fill="black", width=lw)
        draw.line([pt(x+17), y_inv(y+20), pt(x+13), y_inv(y+28)], fill="black", width=lw)
        
        draw.line([pt(x+22), y_inv(y+6), pt(x+22), y_inv(y+26)], fill="black", width=lw)
        draw.line([pt(x+18), y_inv(y+20), pt(x+22), y_inv(y+28)], fill="black", width=lw)
        draw.line([pt(x+26), y_inv(y+20), pt(x+22), y_inv(y+28)], fill="black", width=lw)

    def _draw_mwm_png(self, draw: ImageDraw.Draw, img: Image, index: int) -> None:
        """Renders the specialized MWM label format for PIL."""
        try:
            from barcode import Code39
            from barcode.writer import ImageWriter
        except ImportError:
            logging.error("python-barcode is required to generate MWM PNG labels.")
            return

        def mm2px(mm_val): return int(mm_val * MM_TO_PX)
        
        mwm_margin = mm2px(7.5)
        internal_margin = mm2px(21.5)

        draw.rectangle([mwm_margin, mm2px(MWM_H_MM - 69.5), mm2px(97.5), mm2px(MWM_H_MM - 5.5)], outline="black", width=2)
        
        for y_mm in [43.5, 32.5, 19.5]:
            y_px = mm2px(MWM_H_MM - y_mm)
            draw.line([mwm_margin, y_px, mm2px(105 - 7.5), y_px], fill="black", width=2)

        def draw_txt(x_mm, y_mm, text, font_name="FiraCodeRegular", size_pt=10):
            font = get_pil_font(font_name, size_pt)
            draw.text((mm2px(x_mm), mm2px(MWM_H_MM - y_mm) - size_pt), text, font=font, fill="black")

        draw_txt(7.5, 69, "MWM MOTORES E GERADORES", "YugoSemiBold", 9)
        draw_txt(8, 66, "Part:", "LucidaConsoleRegular", 10)
        draw_txt(21.5, 65, self.ordem.client_code, "ConsolasRegular", 27)

        def draw_code39(val, x_mm, y_mm):
            if not val: return
            options = {'module_width': 0.15, 'module_height': 8.0, 'quiet_zone': 1.0, 'font_size': 0, 'write_text': False}
            try:
                code_img = Code39(str(val), writer=ImageWriter(), add_checksum=False).render(options)
                code_img = code_img.resize((int(code_img.width * 0.8), mm2px(8)))
                img.paste(code_img, (mm2px(x_mm), mm2px(MWM_H_MM - y_mm - 8)))
            except Exception:
                pass

        draw_code39(self.ordem.client_code, 15, 48)