import pandas as pd
from datetime import datetime as dt

file_date = dt.now().strftime("%d_%m_%Y")

class LabelInfo:
  def __init__(self, client, code, description, quantity, weight):
    today = dt.now().strftime("%d/%m/%Y")
    self.date = today
    self.client = client
    self.code = code
    self.barcode = None
    self.description = description
    self.quantity = quantity
    self.weight = weight
    self.set_barcode_data()

  def set_barcode_data(self):
    split_description = self.description.split(" ")
    self.barcode = self.code +" "+ split_description[-1]
    return self.barcode

class LabelData:
  def __init__(self, file_path = f"./ordens_{file_date}.xlsx"):
    self.file_path = file_path
    self.label_data = self.load_data(file_path)
    self.format_data()

  def load_data(self, file_path):
    try:
      return pd.read_excel(file_path)
    except Exception as e:
      print(f"Error loading data: {e}")
      return None
    
  def format_data(self):
    self.label_data = self.label_data[['Código', 'Cliente', 'Cód. Material', 'Material', 'Quantidade']]

  def print_data(self):
    print(self.label_data)

  def get_data(self, op, kg):
    try:
      current_data = self.label_data.loc[self.label_data['Código']==op, ['Cliente', 'Cód. Material', 'Material', 'Quantidade']]
      current_label = LabelInfo(current_data.loc[:,['Cliente']].to_string(index=False, header=False), current_data.loc[:,['Cód. Material']].to_string(index=False, header=False), current_data.loc[:,['Material']].to_string(index=False, header=False), current_data.loc[:,['Quantidade']].to_string(index=False, header=False), kg)
      return current_label
    except Exception as e:
      print(f"not found {e}")
      return None