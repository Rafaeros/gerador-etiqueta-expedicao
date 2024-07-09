# Tamanho da etiqueta: ETIQUETA ADESIVA BOPP PEROLADO 100 x 150mm - COUCHE PERSONALIZADA 250 UNID.

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics

from reportlab.graphics.barcode import code128
from reportlab.platypus import SimpleDocTemplate, Paragraph


class LabelPrint():
  def __init__(self, LabelInfo):
    self.label_info = LabelInfo

  def get_string_width(self, text, font_name, font_size):
    return pdfmetrics.stringWidth(text, font_name, font_size)
  
  # Função, para adaptar o texto a comprimento e largura do pdf.
  def draw_text(self, canvas, text, x, y, max_width, initial_font_size, font_name="Courier"):
    font_size = initial_font_size
    text_width = self.get_string_width(text, font_name, font_size)
    
    while text_width > max_width and font_size > 1:
        font_size -= 1
        text_width = self.get_string_width(text, font_name, font_size)
    
    canvas.setFont(font_name, font_size)
    canvas.drawString(x, y, text)
  
  def draw_text_break(self, canvas, text, x, y, max_width, font_size, font_name="Courier"):
    doc = SimpleDocTemplate("temp.pdf", pagesize=letter)
    
    # Configurar o estilo do parágrafo
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = font_name
    style.fontSize = font_size

    # Criar o parágrafo com quebra de linha automática
    paragraph = Paragraph(text, style)

    # Construir o parágrafo no documento temporário
    doc.build([paragraph])

    # Desenhar o parágrafo no canvas
    canvas.saveState()
    canvas.translate(x, y)
    paragraph.wrapOn(canvas, max_width, 500)
    paragraph.drawOn(canvas, 0, 0)
    canvas.restoreState()

  def draw_desc_barcode(self, canvas, barcode_value, x, y, max_width):
    barcode = code128.Code128(barcode_value, barWidth=0.5*mm, barHeight=15*mm, humanReadable=True, fontSize=10)
    barcode_width = barcode.width

    scale = max_width / barcode_width
    # Desenha o código de barras com a escala calculada
    canvas.saveState()
    canvas.scale(scale, 1)
    barcode.drawOn(canvas, x / scale, y)  # Ajusta a posição para considerar a escala
    canvas.restoreState()

  def draw_qtd_barcode(self, canvas, barcode_value, x, y, max_width, barHeight):
    barcode = code128.Code128(barcode_value, barWidth=0.5*mm, barHeight=barHeight, humanReadable=True, fontSize=10)
    barcode_width = barcode.width

    scale = max_width / barcode_width
    # Desenha o código de barras com a escala calculada
    canvas.saveState()
    canvas.scale(scale, 1)
    barcode.drawOn(canvas, x / scale, y)  # Ajusta a posição para considerar a escala
    canvas.restoreState()

  def create_label(self):
    # Dimensões da etiqueta
    width = 150*mm
    height = 100*mm

    margin_left = 5*mm
    max_width = 140*mm

    # Posição dos elementos
    # Data
    date_x, date_y = 10*mm, height-25*mm
    # Linha horizontal
    line_x1, line_y1, line_x2, line_y2 = 0, height-30*mm, width, height-30*mm
    # Cliente
    client_x, client_y = margin_left, height-40*mm
    # Código
    code_x, code_y = margin_left, height-50*mm
    # Descrição
    description_x, description_y = margin_left, height-60*mm
    # Código de barras descrição.
    desc_barcode_x, desc_barcode_y = 0, height-80*mm
    # Quantidade
    qtd_x, qtd_y = margin_left, height-95*mm
    # Código de barras quantidade.
    qtd_barcode_x, qtd_barcode_y = 50*mm, height-95*mm

    pdf = canvas.Canvas(f"etq.pdf", pagesize=landscape((width,height)))

    # Data
    self.draw_text(pdf, f"{self.label_info.date}", date_x, date_y, max_width, 12)

    # Linha Divisória
    pdf.line(line_x1, line_y1, line_x2, line_y2)

    # Cliente
    self.draw_text(pdf, f"CLIENTE: {self.label_info.client}", client_x, client_y, max_width, 18)

    # Código
    self.draw_text(pdf, f"CÓDIGO: {self.label_info.code}", code_x, code_y, max_width, 20)

    # Descrição
    self.draw_text_break(pdf, f"DESCRIÇÃO: {str(self.label_info.description)}", description_x, description_y, max_width, 16)

    # Código de Barras
    self.draw_desc_barcode(pdf, f"{self.label_info.set_barcode_data()}", desc_barcode_x, desc_barcode_y, max_width)

    # Quantidade
    self.draw_text(pdf, f"QUANTIDADE: {self.label_info.quantity}", qtd_x, qtd_y, max_width, 12)

    # Codigo de barras quantidade
    self.draw_qtd_barcode(pdf, f"{self.label_info.quantity}", qtd_barcode_x, qtd_barcode_y, 40*mm, 10*mm)

    pdf.save()