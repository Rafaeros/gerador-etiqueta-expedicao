import pandas as pd
from datetime import datetime as dt

today = dt.today()

class LabelInfo:
  def __init__(self, date, client, name, description, quantity):
    self.date = date
    self.client = client
    self.name = name
    self.description = description
    self.quantity = quantity

class LabelData:
  def __init__(self, file_path):
    self.label_data = self.load_data(file_path)
    self.format_data()
    self.print_data()

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

  def get_data(self, op):
    try:
      current_data = self.label_data.loc[self.label_data['Código']==op, ['Cliente', 'Cód. Material', 'Material', 'Quantidade']]
      current_label = LabelInfo(today, current_data.loc[:,['Cliente']].to_string(index=False, header=False), current_data.loc[:,['Cód. Material']].to_string(index=False, header=False), current_data.loc[:,['Material']].to_string(index=False, header=False), current_data.loc[:,['Quantidade']].to_string(index=False, header=False))
      return current_label
    except Exception as e:
      print(f"not found {e}")
      return None