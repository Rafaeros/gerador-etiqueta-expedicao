import pathlib
import platform
from datetime import timedelta, datetime as dt
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.graphics.shapes import Rect
from reportlab.graphics.barcode.code128 import Code128
from reportlab.graphics.barcode import code39
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

if platform.system() == "Windows":
    import win32api
    import win32print

from core.get_data import OrdemDeProducao

LABEL_SIZE: int = (428, 283)
MARGIN: int = 14

MWM_LABEL_SIZE = (105*mm, 75*mm)
MWM_MARGIN = 7.5*mm

FONTS_PATH: pathlib.Path = pathlib.Path(__file__).parent / "assets/fonts"
LABEL_FONTS: list = [
    TTFont("ConsolasRegular", FONTS_PATH / "Consolas-Regular.ttf"),
    TTFont("DubaiBold", FONTS_PATH / "Dubai-Bold.ttf"),
    TTFont("FiraCodeRegular", FONTS_PATH / "FiraCode-Regular.ttf"), 
    TTFont("FiraCodeBold", FONTS_PATH / "FiraCode-Bold.ttf"),
    TTFont("LucidaConsoleRegular", FONTS_PATH / "LucidaConsole-Regular.ttf"),
    TTFont("YugoSemiBold", FONTS_PATH / "Yugo-SemiBold.ttc"),
    TTFont("YugoSemiLight", FONTS_PATH / "Yugo-SemiLight.ttc")
]

LABELS_PATH: pathlib.Path = pathlib.Path().parent / "tmp/labels"
LABELS_PATH.mkdir(parents=True, exist_ok=True)

class Label(Canvas):
    op: OrdemDeProducao
    pdf_path: str
    today_date: dt = dt.now()

    def __init__(self, op: OrdemDeProducao) -> None:
        self.op = op
        self.pdf_path = LABELS_PATH / f"{self.op.code}.pdf"
        if self.op.material_code.startswith("MWM"):
            super().__init__(str(self.pdf_path), MWM_LABEL_SIZE)
        else:
            super().__init__(str(self.pdf_path), LABEL_SIZE)

        for font in LABEL_FONTS:
            pdfmetrics.registerFont(font)

    def _draw_text(self, x: int, y: int, text: str, font = "FiraCodeRegular", font_size = 10):
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        text.replace("\n", "<br/>")
        style.fontName = font
        style.fontSize = font_size
        paragraph = Paragraph(text, style)
        self.saveState()
        if font in ["DubaiBold", "YugoSemiLight"]:
            self.transform(1, 0, 0.2, 1, -8.5*mm, 0)
        paragraph.wrapOn(self, 428, 283)
        paragraph.drawOn(self, x, y)
        self.restoreState()

    def _get_string_width(self, text: str, font = "FiraCodeRegular", font_size = 10) -> int:
        return self.stringWidth(text, font, font_size)

    def _create_label_barcode(self, x: int, y: int, barcode: str, barWidth = 1.4, barHeight = 30, max_width = LABEL_SIZE[0], font = "FiraCodeRegular", font_size = 10, min_scale = 1.1):
        barcode = Code128(barcode, barWidth = barWidth, barHeight = barHeight, humanReadable = True, fontName = font, fontSize = font_size)
        scale = min((max_width-x) / barcode.width, min_scale)
        self.saveState()
        self.scale(scale, 1)
        barcode.drawOn(self, x/scale, y)
        self.restoreState()

    def _create_mwm_label_barcode(self, x: int, y: int, barcode: str,):
        barcode = code39.Standard39(barcode, bar_width = 5*mm, barHeight = 8*mm)
        barcode.drawOn(self, x, y)

    def mwm_label(self, index: int = 1) -> (bool, str):
        INTERNAL_MARGIN = 21.5*mm

        labels =  [
            {"x": MWM_MARGIN, "y": 69*mm, "text": "MWM MOTORES E GERADORES", "font": "YugoSemiBold", "font_size": 9},
            {"x": 87*mm, "y": 69*mm, "text": "V.2.3.4", "font": "YugoSemiBold", "font_size": 9},
            {"x": 8*mm, "y": 66*mm, "text": "Part:", "font": "LucidaConsoleRegular", "font_size": 10},
            {"x": INTERNAL_MARGIN, "y": 55*mm, "text": "fornecedor/fabricante", "font": "YugoSemiBold", "font_size": 6},
            {"x": 8*mm, "y": 43*mm, "text": "Supplier:15175", "font": "LucidaConsoleRegular", "font_size": 8},
            {"x": 72*mm, "y": 43.5*mm, "text": "Date:", "font": "YugoSemiBold", "font_size": 10},
            {"x": 8*mm, "y": 40*mm, "text": "Qty:", "font": "LucidaConsoleRegular", "font_size": 10},
            {"x": 8*mm, "y": 28.2*mm, "text": "Lot:", "font": "LucidaConsoleRegular", "font_size": 10},
            {"x": 8*mm, "y": 15.5*mm, "text": "ID:", "font": "LucidaConsoleRegular", "font_size": 10}
        ]

        # Date Value
        self._draw_text(81.2*mm, 42.8*mm, f"{self.today_date.strftime('%d/%m/%Y')}", "YugoSemiLight", 8)
        values = [
            {"x": INTERNAL_MARGIN, "y": 65*mm, "text": self.op.client_code, "font": "ConsolasRegular", "font_size": 27},
            {"x": 75*mm, "y": 39*mm, "text": f"{self.op.quantity/self.op.box_count:.0f}", "font": "ConsolasRegular", "font_size": 22.9},
            {"x": INTERNAL_MARGIN, "y": 27.8*mm, "text": f"{self.op.code}", "font": "YugoSemiBold", "font_size": 8.2},
            {"x": INTERNAL_MARGIN, "y": 14.8*mm, "text": f"15175{self.today_date.strftime('%Y%m%d')}{index:06d}", "font": "YugoSemiBold", "font_size": 8.2},
        ]

        barcodes = [
            {"x": 15*mm, "y": 48*mm},
            {"x": 15*mm, "y": 34*mm},
            {"x": 15*mm, "y": 20.3*mm},
            {"x": 15*mm, "y": 7*mm}
        ]

        lines = [
            {"x1": MWM_MARGIN, "y1": 43.5*mm, "x2": 105*mm-MWM_MARGIN, "y2": 43.5*mm},
            {"x1": MWM_MARGIN, "y1": 32.5*mm, "x2": 105*mm-MWM_MARGIN, "y2": 32.5*mm},
            {"x1": MWM_MARGIN, "y1": 19.5*mm, "x2": 105*mm-MWM_MARGIN, "y2": 19.5*mm}
        ]

        for label in labels:
            self._draw_text(label["x"], label["y"], label["text"], label["font"], label["font_size"])

        for value, barcode in zip(values, barcodes):
            self._draw_text(value["x"], value["y"], value["text"], value["font"], value["font_size"])
            if value["x"] == 75*mm:
                qty_size = self._get_string_width(value["text"], value["font"], value["font_size"])
                x_label = value["x"] + qty_size + 1*mm
                self._draw_text(x_label, 35.2*mm, "PCs", "DubaiBold", 12.5)

            self._create_mwm_label_barcode(barcode["x"], barcode["y"], value["text"])

        for line in lines:
            self.line(line["x1"], line["y1"], line["x2"], line["y2"])
        self.rect(MWM_MARGIN, 5.5*mm, 90*mm, 64*mm)

        self.showPage()
        return (True, "")

    def normal_label(self, index: int = 1) -> (bool, str):
        elements_positions = {
            "date": {"x": MARGIN, "y": 215, "text": self.today_date.strftime("%d/%m/%Y"), "font": "FiraCodeRegular", "font_size": 12},
            "lot": {"x": 113, "y": 215, "text": f"{index}/{self.op.box_count}", "font": "FiraCodeRegular", "font_size": 12},
            "line": {"x1": 0, "y1": 200, "x2": 428, "y2": 200},
            "client": {"x": MARGIN, "y": 170, "text": f"CLIENTE: {self.op.client}", "font": "FiraCodeRegular", "font_size": 12},
            "material_code": {"x": MARGIN, "y": 150, "text": f"CODIGO: {self.op.material_code}", "font": "FiraCodeBold", "font_size": 18},
            "description": {"x": MARGIN, "y": 118, "text": f"DESCRICAO: {self.op.description}", "font": "FiraCodeRegular", "font_size": 12},
            "barcode": {"x": -5, "y": 65, "text": self.op.barcode, "font": "FiraCodeRegular", "font_size": 12},
            "quantity": {"x": MARGIN, "y": 20, "text": f"QUANTIDADE: {self.op.quantity/self.op.box_count:.0f}", "font": "FiraCodeRegular", "font_size": 12},
            "quantity_barcode" : {"x": 150, "y": 15, "text": f"{self.op.quantity/self.op.box_count:.0f}", "font": "FiraCodeRegular", "font_size": 12},
            "weight": {"x": 350, "y": 20, "text": f"{self.op.weight} KG", "font": "FiraCodeRegular", "font_size": 12}
        }

        for key, value in elements_positions.items():
            if key == "line":
                self.line(value["x1"], value["y1"], value["x2"], value["y2"])
                continue
            if "barcode" in key:
                self._create_label_barcode(value["x"], value["y"], value["text"], font = value["font"], font_size = value["font_size"])
                continue
            if "quantity_barcode" in key:
                self._create_label_barcode(value["x"], value["y"], value["text"], font = value["font"], font_size = value["font_size"], max_width = 100, min_scale = 1)
                continue
            self._draw_text(value["x"], value["y"], value["text"], value["font"], value["font_size"])
        self.showPage()
        return (True, "")

    def generate_label(self) -> (bool, str):
        if not self.op.quantity % self.op.box_count == 0:
            return (False, "Quantidade inválida, não é divisivel pelo numero de caixas.")

        try:
            for i in range(1,self.op.box_count+1):
                if self.op.material_code.startswith("MWM"):
                    self.mwm_label(i)
                else:
                    self.normal_label(i)
            self.save()
        except Exception as e:
            print(e)
            return (False, "Erro ao gerar label")

        #self.print_label(str(LABELS_PATH / f"{self.op.code}.pdf"))
        return (True, "")

    def print_label(self, pdf_path: str) -> bool:
        printer = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(printer)
        try:
            win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)
        except FileNotFoundError:
            print("Arquivo nao encontrado")
            return False
        except Exception as e:
            print(e)
            return False
        finally:
            win32print.ClosePrinter(hprinter)
        return True


if __name__ == "__main__":
    op = OrdemDeProducao(223536, "PRODUTO A", "CLIENTE A", "DESCRICAO PRODUTO A (PRODUTO A)", "DESCRICAO PRODUTO A", 2000, 1, "10,50")
    lb = Label(op)
    lb.generate_label()