"""
Module for generating and managing production order labels in PDF format.

This module defines the `Label` class, which is responsible for creating 
customized labels for production orders (`OrdemDeProducao`). It includes 
methods for generating the label content (such as client information, material 
codes, descriptions, barcodes, quantities, and weights), saving the label as 
a PDF file, and printing the label.

Key Features:
    - Dynamic label creation based on `OrdemDeProducao` data.
    - Supports multiple label formats and customization options.
    - Integration with barcode generation (Code128).
    - Print support via default printer using Windows API.
    
Classes:
    - Label: A class to generate, customize, and print labels for production orders.

Dependencies:
    - ReportLab: For generating and customizing PDF labels.
    - win32api, win32print: For printing the generated PDF labels on Windows.

Usage:
    The `Label` class is instantiated with an `OrdemDeProducao` object, 
    and methods can be used to generate a label, customize it, and save or print it.
"""

import logging
import pathlib
import platform
from datetime import datetime as dt
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from reportlab.graphics.barcode.code128 import Code128
from reportlab.graphics.barcode import code39
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from core.get_data import OrdemDeProducao

if platform.system() == "Windows":
    import win32api
    import win32print

LABEL_SIZE: int = (428, 283)
MWM_LABEL_SIZE = (105*mm, 75*mm)
FONTS_PATH: pathlib.Path = pathlib.Path(__file__).parent / "assets/fonts"
LABELS_PATH: pathlib.Path = pathlib.Path().parent / "tmp/labels"
LABELS_PATH.mkdir(parents=True, exist_ok=True)
LABEL_FONTS: list = [
    TTFont("ConsolasRegular", FONTS_PATH / "Consolas-Regular.ttf"),
    TTFont("DubaiBold", FONTS_PATH / "Dubai-Bold.ttf"),
    TTFont("FiraCodeRegular", FONTS_PATH / "FiraCode-Regular.ttf"),
    TTFont("FiraCodeBold", FONTS_PATH / "FiraCode-Bold.ttf"),
    TTFont("LucidaConsoleRegular", FONTS_PATH / "LucidaConsole-Regular.ttf"),
    TTFont("YugoSemiBold", FONTS_PATH / "Yugo-SemiBold.ttc"),
    TTFont("YugoSemiLight", FONTS_PATH / "Yugo-SemiLight.ttc")
]


class Label(Canvas):
    """
    A class to generate and manage labels for 'OrdemDeProducao' (Production Orders).

    Inherits from the Canvas class and provides methods to generate labels 
    in PDF format, including the ability to print and customize label content 
    such as client information, material codes, descriptions, barcodes, 
    quantities, and weights. The label format and content vary based on 
    the 'OrdemDeProducao' data provided.

    Attributes:
        ordem (OrdemDeProducao): An object representing a production order.
        pdf_path (str): The file path where the generated PDF label will be saved.
        today_date (datetime): The current date, used for date-related label content.
    """
    ordem: OrdemDeProducao
    pdf_path: pathlib.Path
    today_date: dt


    def __init__(self, ordem: OrdemDeProducao) -> None:
        """
        Initializes a label generator object for a given 'OrdemDeProducao' object.

        This constructor sets up the label generation based on the order's material code, 
        determining the appropriate label size and font. If the material code starts with 
        "MWM", a specific label size is used; otherwise, a default size is applied.

        :param ordem: The 'OrdemDeProducao' object containing order details 
        used to create the label.
        
        The constructor also registers fonts for use in the label creation process.
        """
        self.ordem = ordem
        self.pdf_path = LABELS_PATH / f"{self.ordem.code}.pdf"
        self.today_date = dt.now()
        if self.ordem.material_code.startswith("MWM"):
            super().__init__(str(self.pdf_path), MWM_LABEL_SIZE)
        else:
            super().__init__(str(self.pdf_path), LABEL_SIZE)

        for font in LABEL_FONTS:
            pdfmetrics.registerFont(font)

    def _draw_text(self, x: int, y: int, text: str, font = "FiraCodeRegular", font_size = 10):
        """
        Draws the specified text on the label at the given coordinates 
        with the specified font and size.

        This function creates a paragraph of text using the specified font and size, and then 
        draws it on the label at the given position. The text is first wrapped and formatted 
        according to the available space on the label.

        :param x: The x-coordinate where the text will be drawn.
        :param y: The y-coordinate where the text will be drawn.
        :param text: The string of text to be displayed.
        :param font: The font to be used for the text. Defaults to "FiraCodeRegular".
        :param font_size: The size of the font to be used. Defaults to 10.

        :return: None
        """
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
        """
        Calculates the width of a string when rendered with a specific font and size.

        This function uses the `stringWidth` method to compute the width of the provided text 
        using the specified font and font size. The returned width can be used for positioning 
        elements such as text and barcodes on the label.

        :param text: The string for which the width is to be calculated.
        :param font: The font to be used for the text. Defaults to "FiraCodeRegular".
        :param font_size: The font size to be used for the text. Defaults to 10.

        :return: The width of the string in units used by the rendering system (e.g., points).
        """
        return self.stringWidth(text, font, font_size)

    def _create_label_barcode(
        self,
        x: int,
        y: int, barcode: str,
        bar_width = 1.4,
        bar_height = 30,
        max_width = LABEL_SIZE[0],
        font = "FiraCodeRegular",
        font_size = 10,
        min_scale = 1.1
    ) -> None:
        """
        Generates a barcode label with Code128 format and draws it on the page.

        :param x: The x-coordinate for the barcode's position on the label.
        :param y: The y-coordinate for the barcode's position on the label.
        :param barcode: The barcode string that will be encoded.
        :param bar_width: The width of the bars in the barcode. Defaults to 1.4.
        :param bar_height: The height of the barcode. Defaults to 30.
        :param max_width: The maximum width available for the barcode.
         Defaults to the width of the label.
        :param font: The font used for the human-readable text under the barcode. 
         Defaults to "FiraCodeRegular".
        :param font_size: The font size for the human-readable text. Defaults to 10.
        :param min_scale: The minimum scale applied to the barcode to fit 
         it within the available space. Defaults to 1.1.

        :return: None. The function directly modifies the page by drawing the barcode.
        """
        barcode = Code128(
            barcode,
            barWidth = bar_width,
            barHeight = bar_height,
            humanReadable = True,
            fontName = font,
            fontSize = font_size
        )
        scale = min((max_width-x) / barcode.width, min_scale)
        self.saveState()
        self.scale(scale, 1)
        barcode.drawOn(self, x/scale, y)
        self.restoreState()

    def _create_mwm_label_barcode(self, x: int, y: int, barcode: str, bar_width, bar_height, ratio)  -> None:
        """
        Generates a Code39 barcode for the MWM label and draws it at the specified position.

        Args:
            x (int): X position where the barcode will be drawn.
            y (int): Y position where the barcode will be drawn.
            barcode (str): Barcode value.
            bar_width (float): Width of the individual bars in the barcode.
            bar_height (float): Height of the barcode.
            ratio (float): Ratio between thin and wide bars.

        Returns:
            None
        """
        barcode = code39.Standard39(barcode, barWidth = bar_width, barHeight = bar_height, ratio=ratio, checksum=False)
        barcode.drawOn(self, x, y)

    def mwm_label(self, index: int = 1) -> tuple[bool, str]:
        """
        Generates an MWM label with barcode 39 and a size of 105x100mm.

        This function generates a label with a predefined layout and includes various elements:
        - Fixed and dynamic texts (e.g., client code, order code, supplier, quantity, date).
        - Barcodes for the quantity and order code.
        - Multiple lines to separate different sections of the label.

        The label contains the following fields:
            - MWM company name and version.
            - Part number, supplier, date, quantity, lot, and ID.
            - Barcodes for the order information.

        :param index: The index number used to differentiate labels for different items.
            Defaults to 1.

        :return: A tuple indicating the success of the label generation.
            - Returns (True, "") if the label is generated successfully.
            - Returns (False, "Error message") if there is an error during label generation.
        """
        mwm_margin = 7.5*mm
        internal_margin = 21.5*mm

        labels =  [
            {"x": mwm_margin, "y": 69*mm, "text": "MWM MOTORES E GERADORES", "font": "YugoSemiBold", "font_size": 9},
            {"x": 87*mm, "y": 69*mm, "text": "V.2.3.4", "font": "YugoSemiBold", "font_size": 9},
            {"x": 8*mm, "y": 66*mm, "text": "Part:", "font": "LucidaConsoleRegular", "font_size": 10},
            {"x": internal_margin, "y": 54.9*mm, "text": "fornecedor/fabricante", "font": "YugoSemiBold", "font_size": 6},
            {"x": 8*mm, "y": 43*mm, "text": "Supplier:15175", "font": "LucidaConsoleRegular", "font_size": 8},
            {"x": 72*mm, "y": 43.5*mm, "text": "Date:", "font": "YugoSemiBold", "font_size": 10},
            {"x": 8*mm, "y": 40*mm, "text": "Qty:", "font": "LucidaConsoleRegular", "font_size": 10},
            {"x": 8*mm, "y": 28.2*mm, "text": "Lot:", "font": "LucidaConsoleRegular", "font_size": 10},
            {"x": 8*mm, "y": 15.5*mm, "text": "ID:", "font": "LucidaConsoleRegular", "font_size": 10}
        ]

        self._draw_text(81.2*mm, 42.8*mm, f"{self.today_date.strftime('%d/%m/%Y')}", "YugoSemiLight", 8)
        values = [
            {"x": internal_margin, "y": 65*mm, "text": self.ordem.client_code, "font": "ConsolasRegular", "font_size": 27},
            {"x": 75*mm, "y": 39*mm, "text": f"{self.ordem.quantity/self.ordem.box_count:.0f}", "font": "ConsolasRegular", "font_size": 22.9},
            {"x": internal_margin, "y": 27.8*mm, "text": f"{self.ordem.code}", "font": "YugoSemiBold", "font_size": 8.2},
            {"x": internal_margin, "y": 14.8*mm, "text": f"15175{self.today_date.strftime('%Y%m%d')}{index:06d}", "font": "YugoSemiBold", "font_size": 8.2},
        ]

        barcodes = [
            {"x": 15*mm, "y": 48*mm, "bar_width": 0.3*mm, "bar_height": 8*mm, "ratio": 2.2},
            {"x": 15*mm, "y": 34*mm, "bar_width": 0.4*mm, "bar_height": 8*mm, "ratio": 2.2},
            {"x": 15*mm, "y": 20.3*mm, "bar_width": 0.4*mm, "bar_height": 8*mm, "ratio": 2.2},
            {"x": 15*mm, "y": 7*mm, "bar_width": 0.26*mm, "bar_height": 8*mm, "ratio": 2.2}
        ]

        lines = [
            {"x1": mwm_margin, "y1": 43.5*mm, "x2": 105*mm-mwm_margin, "y2": 43.5*mm},
            {"x1": mwm_margin, "y1": 32.5*mm, "x2": 105*mm-mwm_margin, "y2": 32.5*mm},
            {"x1": mwm_margin, "y1": 19.5*mm, "x2": 105*mm-mwm_margin, "y2": 19.5*mm}
        ]

        for label in labels:
            self._draw_text(label["x"], label["y"], label["text"], label["font"], label["font_size"])

        for value, barcode in zip(values, barcodes):
            self._draw_text(value["x"], value["y"], value["text"], value["font"], value["font_size"])
            if value["x"] == 75*mm:
                qty_size = self._get_string_width(value["text"], value["font"], value["font_size"])
                x_label = value["x"] + qty_size + 2*mm
                self._draw_text(x_label, 35.2*mm, "PCs", "DubaiBold", 12.5)

            self._create_mwm_label_barcode(barcode["x"], barcode["y"], value["text"], barcode["bar_width"], barcode["bar_height"], barcode["ratio"])

        for line in lines:
            self.line(line["x1"], line["y1"], line["x2"], line["y2"])
        self.rect(mwm_margin, 5.5*mm, 90*mm, 64*mm)

        self.showPage()
        return (True, "")

    def normal_label(self) -> tuple[bool, str]:
        """
        Generates a normal label with the order details.

        This function generates a label containing various order details, such as client, material code, description,
        barcode, quantity, weight, and date. The label is created by drawing text and barcodes at specified positions 
        on the label template. A line is also drawn for visual separation.

        The label elements are as follows:
            - Date
            - Client name
            - Material code
            - Material description
            - Barcode for the material
            - Quantity per box
            - Barcode for quantity
            - Weight

        :return: A tuple indicating the success of the label generation.
            - Returns (True, "") if the label is generated successfully.
            - Returns (False, "Error message") if there is an error during label generation.
        """
        margin: int = 14
        elements_positions = {
            "date": {"x": margin, "y": 215, "text": self.today_date.strftime("%d/%m/%Y"), "font": "FiraCodeRegular", "font_size": 12},
            #"lot": {"x": 113, "y": 215, "text": f"{index}/{self.op.box_count}", "font": "FiraCodeRegular", "font_size": 12},
            "line": {"x1": 0, "y1": 200, "x2": 428, "y2": 200},
            "client": {"x": margin, "y": 170, "text": f"CLIENTE: {self.ordem.client}", "font": "FiraCodeRegular", "font_size": 12},
            "material_code": {"x": margin, "y": 150, "text": f"CODIGO: {self.ordem.material_code}", "font": "FiraCodeBold", "font_size": 18},
            "description": {"x": margin, "y": 118, "text": f"DESCRICAO: {self.ordem.description}", "font": "FiraCodeRegular", "font_size": 12},
            "barcode": {"x": -5, "y": 65, "text": self.ordem.barcode, "font": "FiraCodeRegular", "font_size": 12},
            "quantity": {"x": margin, "y": 20, "text": f"QUANTIDADE: {self.ordem.quantity/self.ordem.box_count:.0f} UND", "font": "FiraCodeRegular", "font_size": 12},
            "quantity_barcode" : {"x": 150, "y": 15, "text": f"{self.ordem.quantity/self.ordem.box_count:.0f}", "font": "FiraCodeRegular", "font_size": 12},
            "weight": {"x": 350, "y": 20, "text": f"{self.ordem.weight} KG", "font": "FiraCodeRegular", "font_size": 12}
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

    def generate_label(self) -> tuple[bool, str]:
        """
        Generates labels for the production order.

        :return: 
            A tuple containing a boolean value indicating the success of the operation and a string with the error message, if any.
            - If the operation is successful, returns (True, "").
            - If there is a failure, returns (False, "Error message").
        """
        if not self.ordem.quantity % self.ordem.box_count == 0:
            return (False, "Quantidade inválida, não é divisivel pelo numero de caixas.")

        try:
            for i in range(1,self.ordem.box_count+1):
                if self.ordem.material_code.startswith("MWM"):
                    self.mwm_label(i)
                else:
                    self.normal_label()
            self.save()
        except ValueError as e:
            logging.error(e, exc_info=True)
            return (False, str(e))

        self.print_label(str(self.pdf_path))
        return (True, "")

    def print_label(self, pdf_path: str) -> bool:
        """
        Prints the label from the provided PDF file path.

        :param pdf_path: The file path of the PDF label to be printed.
        
        :return: A boolean indicating the success of the print operation:
            - Returns True if the print operation is successful.
            - Returns False if any error occurs during the print process.
        """     
        printer = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(printer)
        try:
            win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)
        except FileNotFoundError:
            logging.error("Arquivo nao encontrado")
            return False
        except PermissionError:
            logging.error("Permissao negada")
            return False
        except win32api.error:
            logging.error("Erro ao imprimir")
            return False
        finally:
            win32print.ClosePrinter(hprinter)
        return True


if __name__ == "__main__":
    ordem = OrdemDeProducao(
        223536, "PRODUTO A",
        "CLIENTE A",
        "DESCRICAO PRODUTO A (PRODUTO A)",
        "DESCRICAO PRODUTO A",
        2000,
        1,
        "10,50"
    )
    lb = Label(ordem)
    lb.generate_label()
