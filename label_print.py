"""
  Create a label to print
"""

# Tamanho da etiqueta: ETIQUETA ADESIVA BOPP PEROLADO 100 x 150mm - COUCHE PERSONALIZADA 250 UNID.
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageWin
from barcode.codex import Code128, Code39
from barcode.writer import ImageWriter
from win32 import win32print
import win32ui
from get_data import LabelInfo

LABEL_PATH: str = "./tmp/labels/"

class LabelPrint():
    """
    LabelPrint class that contains methods to print the label.
    """
    label_info: LabelInfo
    label: Image

    def __init__(self, info: LabelInfo) -> None:
        """
        Initialize the LabelPrint class. with the LabelInfo object.
        """
        self.label_info = info

    def mm_to_px(self, mm: float, dpi: int = 300) -> int:
        """
        Convert mm to pixels.
        """
        return int(mm * (dpi / 25.4))

    def wrap_text(self, text: str, max_chars: int = 35) -> str:
        """"
        Wrap text.
        """
        # Inicializa variáveis
        max_chars: int = max_chars
        words: list[str] = text.split(' ')
        lines: list[str] = []
        current_line: str = ""

        # Verifica se a quantidade de caracteres excedeu o limite definido e quebra a linha do texto
        for word in words:
            if len(current_line) + len(word) + 1 > max_chars:
                lines.append(current_line)
                current_line = word
            else:
                if current_line:
                    current_line += ' ' + word
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)
        wrapped_text: str = '\n'.join(lines)

        return wrapped_text

    def draw_label_elements(
        self,
        image: Image,
        draw: ImageDraw,
        attributes: list[dict],
        font_path: str
    ) -> None:
        """
        Draw label elements.
        """
        for attribute in attributes:
            if 'width' in attribute:
                barcode_buffer: BytesIO = BytesIO()
                barcode: Code128 = Code128(
                    attribute['text'], writer=ImageWriter())
                options: dict = {
                    "module_width": attribute['width'],
                    "module_height": attribute['height'],
                    "quiet_zone": 1,
                    "font_path": font_path,
                    "font_size": 10
                }
                barcode.write(barcode_buffer, options)
                barcode_image: Image = Image.open(barcode_buffer)
                image.paste(barcode_image, attribute['xy'])
            else:
                draw.text(attribute['xy'], attribute['text'],
                          font=attribute['font'], fill='black')

    def draw_mwm_label_elements(self, image: Image, draw: ImageDraw,
                                attributes: list[dict]) -> None:
        """
        Draw MWM label elements.
        """
        # Concatenando o qty_number com o PCs sem que se sobreponham
        font: ImageFont = attributes[11]['font']
        bbox: tuple[int, int, int, int] = font.getbbox(attributes[11]['text'])
        attributes[13]['xy'] = (self.mm_to_px(74)+bbox[2], self.mm_to_px(35))

        # Iterando os atributos e verificando se o elemento possui o atributo 'width'
        # Se sim, o elemento é um código de barras
        for attribute in attributes:
            if 'width' in attribute:
                barcode_buffer: BytesIO = BytesIO()
                barcode: Code39 = Code39(
                    attribute['text'], writer=ImageWriter())
                options: dict = {
                    "module_width": attribute['width'],
                    "module_height": 8,
                    "quiet_zone": 1,
                    "write_text": False
                }
                barcode.write(barcode_buffer, options)
                barcode_image: Image = Image.open(barcode_buffer)
                image.paste(barcode_image, attribute['xy'])

        # Iterando os atributos e verificando se o elemento não possui o atributo 'width'
        # Se sim, o elemento é um texto
        for attribute in attributes:
            if 'width' not in attribute:
                draw.text(attribute['xy'], attribute['text'],
                          fill='black', font=attribute['font'])

    def create_label(self) -> None:
        """
        Create label.
        """

        WIDTH: int = self.mm_to_px(150)  # pylint: disable=C0103
        HEIGHT: int = self.mm_to_px(100)  # pylint: disable=C0103
        FONT_PATH: str = "./assets/fonts/FiraCode-Regular.ttf"  # pylint: disable=C0103

        # Posições dos elementos da etiqueta (label)
        attr: list[dict] = [
            {
                'xy': (self.mm_to_px(10), self.mm_to_px(20)),
                'text': f'{self.label_info.date}',
                'font': ImageFont.truetype(FONT_PATH, size=62)
            },
            {
                'xy': (self.mm_to_px(50),
                       self.mm_to_px(20)),
                'text': f'{self.label_info.boxes}',
                'font': ImageFont.truetype(FONT_PATH, size=62)},
            {
                'xy': (self.mm_to_px(5),
                       self.mm_to_px(27)),
                'text': f'CLIENTE: {self.wrap_text(self.label_info.client)}',
                'font': ImageFont.truetype(FONT_PATH, size=55)
            },
            {
                'xy': (self.mm_to_px(5), self.mm_to_px(40)),
                'text': f'CÓDIGO: {self.label_info.code}',
                'font': ImageFont.truetype(FONT_PATH, size=80)
            },
            {
                'xy': (self.mm_to_px(5), self.mm_to_px(48)),
                'text': f'DESCRICÃO: {self.wrap_text(self.label_info.description)}',
                'font': ImageFont.truetype(FONT_PATH, size=62)
            },
            {
                'xy': (self.mm_to_px(5), self.mm_to_px(68)),
                'text': f'{self.label_info.barcode}',
                'font': ImageFont.truetype(FONT_PATH, size=62),
                'width': 0.34,
                'height': 10
            },
            {
                'xy': (self.mm_to_px(5), self.mm_to_px(90)),
                'text': f'QUANTIDADE: {self.label_info.quantity}',
                'font': ImageFont.truetype(FONT_PATH, size=62)
            },
            {
                'xy': (self.mm_to_px(70), self.mm_to_px(86)),
                'text': f'{self.label_info.quantity}',
                'font': ImageFont.truetype(FONT_PATH, size=62),
                'width': 0.4,
                'height': 8
            },
            {
                'xy': (self.mm_to_px(120), self.mm_to_px(90)),
                'text': f'{self.label_info.weight} Kg',
                'font': ImageFont.truetype(FONT_PATH, size=62)
            },
        ]

        # Criar imagem em branco (label)
        op_label = Image.new('RGB', (WIDTH, HEIGHT), color='white')

        # Criar objeto para desenhar na imagem
        draw: ImageDraw.Draw = ImageDraw.Draw(op_label)

        # Desenhando elementos do label
        draw.line((self.mm_to_px(0), self.mm_to_px(26), self.mm_to_px(160), self.mm_to_px(26)),
                  fill='black', width=2)
        self.draw_label_elements(op_label, draw, attr, FONT_PATH)

        op_label.thumbnail((WIDTH, HEIGHT))
        op_label.save(f'{LABEL_PATH}etq.png')

    def create_mwm_label(self) -> None:
        """
        Create MWM label.
        """
        WIDTH: int = self.mm_to_px(105, 300)  # pylint: disable=C0103
        HEIGHT: int = self.mm_to_px(75, 300)  # pylint: disable=C0103
        FONT_PATH: str = "./assets/fonts/"  # pylint: disable=C0103

        layout_positions: dict[str, tuple] = {
            'rectangle': (self.mm_to_px(7.5), self.mm_to_px(5.5),
                          self.mm_to_px(97.5), self.mm_to_px(69.5)),
            'lines': [
                (self.mm_to_px(7.5), self.mm_to_px(31.5),
                 self.mm_to_px(97.5), self.mm_to_px(31.5)),
                (self.mm_to_px(7.5), self.mm_to_px(42.5),
                 self.mm_to_px(97.5), self.mm_to_px(42.5)),
                (self.mm_to_px(7.5), self.mm_to_px(55.5),
                 self.mm_to_px(97.5), self.mm_to_px(55.5))
            ],
        }

        # Posições dos elementos da etiqueta (label)
        attributes: list[dict] = [
            # Cliente
            {
                'xy': (self.mm_to_px(7.5), self.mm_to_px(2.7)),
                'text': 'MWM MOTORES E GERADORES',
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHB.TTC', size=self.mm_to_px(9, 100))
            },
            # Versão
            {
                'xy': (self.mm_to_px(88), self.mm_to_px(2.7)),
                'text': 'V.2.3.4',
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHB.TTC', size=self.mm_to_px(9, 100))
            },
            # Part:
            {
                'xy': (self.mm_to_px(8), self.mm_to_px(5.5)),
                'text': 'Part:',
                'font': ImageFont.truetype(f'{FONT_PATH}LUCON.TTF', size=self.mm_to_px(10, 100))
            },
            # Part_number
            {
                'xy': (self.mm_to_px(23), self.mm_to_px(9)),
                'text': self.label_info.client_code,
                'font': ImageFont.truetype(f'{FONT_PATH}CONSOLA.TTF', size=self.mm_to_px(27, 110))
            },
            # Part_number_barcode
            {
                'xy': (self.mm_to_px(23), self.mm_to_px(18.3)),
                'text': self.label_info.client_code,
                'width': 0.22
            },
            # fabricante/fornecedor
            {
                'xy': (self.mm_to_px(24), self.mm_to_px(17)),
                'text': 'fornecedor/fabricante',
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHB.TTC', size=self.mm_to_px(6, 100))
            },
            # Supplier:
            {
                'xy': (self.mm_to_px(8), self.mm_to_px(28.5)),
                'text': 'Supplier:',
                'font': ImageFont.truetype(f'{FONT_PATH}LUCON.TTF', size=self.mm_to_px(8, 100))
            },
            # Supplier_number
            {
                'xy': (self.mm_to_px(23), self.mm_to_px(28.7)),
                'text': '15175',
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHB.TTC', size=self.mm_to_px(7.2, 100))
            },
            # Date:
            {
                'xy': (self.mm_to_px(70), self.mm_to_px(28)),
                'text': 'Date:',
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHB.TTC', size=self.mm_to_px(10, 100))
            },
            # Data doa dia
            {
                'xy': (self.mm_to_px(80), self.mm_to_px(28.5)),
                'text': self.label_info.date,
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHR.TTC', size=self.mm_to_px(8, 100))
            },
            # Qty:
            {
                'xy': (self.mm_to_px(8), self.mm_to_px(31.7)),
                'text': 'Qty:',
                'font': ImageFont.truetype(f'{FONT_PATH}LUCON.TTF', size=self.mm_to_px(10, 100))
            },
            # Qty_number
            {
                'xy': (self.mm_to_px(74), self.mm_to_px(34)),
                'text':  str(self.label_info.quantity),
                'font': ImageFont.truetype(f'{FONT_PATH}CONSOLA.TTF', size=self.mm_to_px(22.9, 110))
            },
            # Qty_number_barcode
            {
                'xy': (self.mm_to_px(23), self.mm_to_px(32)),
                'text': str(self.label_info.quantity),
                'width': 0.22
            },
            # PCs
            {
                'xy': (self.mm_to_px(84), self.mm_to_px(35)),
                'text': 'PCs',
                'font': ImageFont.truetype(f'{FONT_PATH}DUBAI-BOLD.TTF',
                                           size=self.mm_to_px(12.5, 110))
            },
            # Lot:
            {
                'xy': (self.mm_to_px(8), self.mm_to_px(43)),
                'text': 'Lot:',
                'font': ImageFont.truetype(f'{FONT_PATH}LUCON.TTF', size=self.mm_to_px(10, 100))
            },
            # Lot_number
            {
                'xy': (self.mm_to_px(23), self.mm_to_px(43)),
                'text': self.label_info.op,
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHB.TTC', size=self.mm_to_px(8.2, 100))
            },
            # Lot_number_barcode
            {
                'xy': (self.mm_to_px(22.5), self.mm_to_px(45)),
                'text': self.label_info.op, 'width': 0.28},
            # ID:
            {
                'xy': (self.mm_to_px(8), self.mm_to_px(56)),
                'text': 'ID:',
                'font': ImageFont.truetype(f'{FONT_PATH}LUCON.TTF', size=self.mm_to_px(10, 100))
            },
            # ID_number
            {
                'xy': (self.mm_to_px(23), self.mm_to_px(56)),
                'text': f'15175{self.label_info.mwm_date}{str(self.label_info.boxes).zfill(6)}',
                'font': ImageFont.truetype(f'{FONT_PATH}YUGOTHB.TTC', size=self.mm_to_px(8.2, 100))
            },
            # ID_number_barcode
            {
                'xy': (self.mm_to_px(22.5), self.mm_to_px(58)),
                'text': f'15175{self.label_info.mwm_date}{str(self.label_info.boxes).zfill(6)}',
                'width': 0.205
            },
        ]
        # Criar imagem em branco (etiqueta)
        mwm_label = Image.new('RGB', (WIDTH, HEIGHT), color='white')
        # Criar objeto para desenhar na imagem
        draw: ImageDraw.Draw = ImageDraw.Draw(mwm_label)

        # Layout etiqueta
        draw.rectangle(layout_positions.get('rectangle'),
                       fill='white', outline='black', width=3)
        for i in range(len(layout_positions['lines'])):
            draw.line(layout_positions['lines'][i], width=3, fill='black')

        self.draw_mwm_label_elements(mwm_label, draw, attributes)

        mwm_label.thumbnail((WIDTH, HEIGHT))
        mwm_label.save(f'{LABEL_PATH}etq.png')

    def print_label(self,  largura_mm: float, altura_mm: float, dpi: int = 300,
                    file_path: str = './tmp/labels/etq.png') -> None:
        """
        Print label.
        """
        abs_file_path: str = os.path.abspath(file_path)
        # Configuração da impressora
        default_printer: str = win32print.GetDefaultPrinter()
        printer = win32print.OpenPrinter(default_printer)

        try:
            # Redimensionando a imagem da etiqueta
            label_print = Image.open(abs_file_path)
            largura_px = int((largura_mm / 25.4) * dpi)
            altura_px = int((altura_mm / 25.4) * dpi)
            label_resized = label_print.resize(
                (largura_px, altura_px))

            if not largura_mm == 105 and not altura_mm == 75:
                label_resized = label_resized.rotate(90, expand=True)

            # Configuração da impressão
            printer_dc = win32ui.CreateDC()
            printer_dc.CreatePrinterDC(default_printer)
            printer_dc.StartDoc("Impressão de Etiqueta")
            printer_dc.StartPage()

            label_dib = ImageWin.Dib(label_resized)
            x0, y0, x1, y1 = 0, 0, largura_px, altura_px
            label_dib.draw(printer_dc.GetHandleOutput(), (x0, y0, x1, y1))
            printer_dc.EndPage()
            printer_dc.EndDoc()
            printer_dc.DeleteDC()
        except FileNotFoundError:
            print(f"Erro: Arquivo '{abs_file_path}' não encontrado.")
        except PermissionError:
            print(f"Erro: Permissão negada para acessar '{abs_file_path}'.")
        finally:
            win32print.ClosePrinter(printer)

if __name__ == '__main__':
    label_info = LabelInfo(223568, "CLIENTE", "CODIGO",
                           "DESCRICAO", 10, 3, 100)
    label = LabelPrint(label_info)
    label.create_label()
    label.print_label(150, 100)
