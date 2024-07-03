# Tamanho da etiqueta: ETIQUETA ADESIVA BOPP PEROLADO 100 x 150mm - COUCHE PERSONALIZADA 250 UNID.

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128

class LabelPrint():
  def __init__(self, LabelInfo):
    self.label_info = LabelInfo

  def create_label(self):
    width = 15*cm
    height = 10*cm
    c = canvas.Canvas(f"etq.pdf", pagesize=landscape((width,height)))
    c.setFontSize(10)

    c.drawString(x=cm,y=8*cm, text=f"{self.label_info.date}")

    c.line(0,7.8*cm,15*cm,7.8*cm)

    c.drawString(x=0.2*cm, y=7.2*cm, text=f"Cliente: {self.label_info.client}")
    c.drawString(x=0.2*cm, y=6.5*cm, text=f"Código: {self.label_info.name}")
    c.drawString(x=0.3, y=6*cm, text=f"Descrição: {self.label_info.description}")

    name_barcode = code128.Code128(f'{self.label_info.name}', humanReadable=True, width=5*cm)
    name_barcode.drawOn(c, x=0.2*cm, y=3*cm)
    
    c.drawString(x=0.2*cm, y=1*cm, text=f"Quantidade: {self.label_info.quantity}")

    c.showPage()
    c.save()