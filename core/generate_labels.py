import pathlib
import platform
from datetime import timedelta, datetime as dt
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.graphics.barcode.code128 import Code128
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet

if platform.system() == "Windows":
    import win32api
    import win32print

from core.get_data import OrdemDeProducao

LABEL_SIZE: int = (428, 283)
MARGIN: int = 14
FONTS_PATH: pathlib.Path = pathlib.Path(__file__).parent / "assets/fonts"
LABEL_FONTS: list = [TTFont("FiraCodeRegular", FONTS_PATH / "FiraCode-Regular.ttf"), TTFont("FiraCodeBold", FONTS_PATH / "FiraCode-Bold.ttf")]
LABELS_PATH: pathlib.Path = pathlib.Path().parent / "tmp/labels"
LABELS_PATH.mkdir(parents=True, exist_ok=True)

class Label(Canvas):
    op: OrdemDeProducao
    pdf_path: str

    def __init__(self, op: OrdemDeProducao) -> None:
        self.op = op
        pdf_path = LABELS_PATH / f"{self.op.code}.pdf"
        print(pdf_path)
        super().__init__(str(pdf_path), LABEL_SIZE)
        for font in LABEL_FONTS:
            pdfmetrics.registerFont(font)

    def _draw_text(self, x: int, y: int, text: str, font = "FiraCodeRegular", font_size = 10):
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        text.replace("\n", "<br/>")
        style.fontName = font
        style.fontSize = font_size
        paragraph = Paragraph(text, style)
        paragraph.wrapOn(self, 460, 283)
        paragraph.drawOn(self, x, y)

    def _create_label_barcode(self, x: int, y: int, barcode: str, barWidth = 1.4, barHeight = 30, humanReadable = True, max_width = LABEL_SIZE[0], font = "FiraCodeRegular", font_size = 10, min_scale = 1.1):
        barcode = Code128(barcode, barWidth = barWidth, barHeight = barHeight, humanReadable = True, fontName = font, fontSize = font_size)
        scale = min((max_width-x) / barcode.width, min_scale)
        self.saveState()
        self.scale(scale, 1)
        barcode.drawOn(self, x/scale, y)
        self.restoreState()

    def generate_label(self) -> (bool, str):
        lot = self.op.box_count
        lot_quantity = self.op.quantity

        if not lot_quantity % lot == 0:
            return (False, "Quantidade inválida, não é divisivel pelo numero de caixas.")

        lot_quantity = lot_quantity / lot
        for i in range(1,lot+1,1):
            elements_positions = {
                "date": {"x": MARGIN, "y": 215, "text": dt.now().strftime("%d/%m/%Y"), "font": "FiraCodeRegular", "font_size": 12},
                "lot": {"x": 113, "y": 215, "text": f"{i}/{lot}", "font": "FiraCodeRegular", "font_size": 12},
                "line": {"x1": 0, "y1": 200, "x2": 428, "y2": 200},
                "client": {"x": MARGIN, "y": 170, "text": f"CLIENTE: {self.op.client}", "font": "FiraCodeRegular", "font_size": 12},
                "material_code": {"x": MARGIN, "y": 150, "text": f"CODIGO: {self.op.material_code}", "font": "FiraCodeBold", "font_size": 18},
                "description": {"x": MARGIN, "y": 125, "text": f"DESCRICAO: {self.op.description}", "font": "FiraCodeRegular", "font_size": 12},
                "barcode": {"x": -5, "y": 65, "text": self.op.barcode, "font": "FiraCodeRegular", "font_size": 12},
                "quantity": {"x": MARGIN, "y": 20, "text": f"QUANTIDADE: {lot_quantity:.0f}", "font": "FiraCodeRegular", "font_size": 12},
                "quantity_barcode" : {"x": 150, "y": 15, "text": f"{lot_quantity:.0f}", "font": "FiraCodeRegular", "font_size": 12},
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
        self.save()
        self.print_label(str(LABELS_PATH / f"{self.op.code}.pdf"))
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
    op = OrdemDeProducao(223536, "CEA085 000 000", "CEABS SERVIÇOS ELETRONICOS LTDA", "MODULO ISCA 2GKF", "CEA085 000 000 (225664)", 2000, 1, 1050)
    lb = Label(op)
    lb.generate_label()