import customtkinter as ctk
from CTkMessagebox import CTkMessagebox as ctkmsg
from get_data import LabelData, LabelInfo
from label_print import LabelPrint
from balance_communication import Serial
import time

class Interface:
  def __init__(self):
    self.master = ctk.CTk()
    self.master.geometry("800x600")
    self.master.resizable(False, False)
    self.master.title("Gerador De Etiquetas")
    self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
    self.create_variables()
    self.create_window()

  def run(self):
    self.master.mainloop()

  def on_closing(self):
    if self.serial_com.is_open:
      self.serial_com.close()
    self.master.destroy()

  def create_variables(self):
    try:
      self.label_data = LabelData()
      self.label_data_df = self.label_data.label_data
    except Exception as e:
      msg = ctkmsg(self.master, title=f"Erro ao carregar planilha", message=f"Não encontrado o arquivo: ordens.xlsx com a data de hoje ({e})", icon="warning", option_1="OK")
      msg.wait_window()
      if msg.get() == "OK":
        self.master.destroy()
    
    self.serial_com = Serial()
    self.client_var: str = ctk.StringVar()
    self.code_var: str = ctk.StringVar()
    self.description_var: str = ctk.StringVar()
    self.barcode_var: str = ctk.StringVar()
    self.quantity_var: str = ctk.IntVar()
    self.weight_var: str = ctk.StringVar()
    self.lot_var: int = ctk.IntVar()
    self.manual_weight_var: str = ctk.StringVar(value="on")
    self.lot_quantity = ''
    self.id: str = ''

  def create_window(self):
    self.id_label = ctk.CTkLabel(self.master, text="Número da OP:")
    self.id_input = ctk.CTkEntry(self.master, placeholder_text="Digite o número da OP")
    self.id_input.bind('<Return>', self.search_id)

    self.search_button = ctk.CTkButton(self.master, text="Buscar", command=self.search_id, height=35, corner_radius=10)
    self.clear_inputs_button = ctk.CTkButton(self.master, text="Limpar", command=self.clear_inputs, fg_color='red', height=35, corner_radius=10)
    self.clear_inputs_button.bind('<Delete>', self.clear_inputs)

    self.serial_com_port_menu = ctk.CTkOptionMenu(self.master, values=["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7"], command=self.serial_port_callback)

    self.client_label = ctk.CTkLabel(self.master, text="Cliente:")
    self.client_input = ctk.CTkEntry(self.master, placeholder_text="Cliente do Produto", width=550, height=35)

    self.code_label = ctk.CTkLabel(self.master, text="Código:")
    self.code_input = ctk.CTkEntry(self.master, placeholder_text="Código do Produto", width=300, height=35)

    self.description_label = ctk.CTkLabel(self.master, text="Descrição:")
    self.description_input = ctk.CTkEntry(self.master, placeholder_text="Descrição do Produto", width=550, height=35)

    self.barcode_label = ctk.CTkLabel(self.master, text="Código de barras:")
    self.barcode_input = ctk.CTkEntry(self.master, placeholder_text="Código de barras do Produto", width=300, height=35)

    self.quantity_label = ctk.CTkLabel(self.master, text="Quantidade Total:")
    self.quantity_input = ctk.CTkEntry(self.master, placeholder_text="Quantidade Total", width=200, height=35)

    self.manual_weight_checkbox = ctk.CTkCheckBox(self.master, text="Inserir Peso Manualmente", onvalue="on", offvalue="off", variable=self.manual_weight_var, command=self.manual_weight_callback)

    self.weight_label = ctk.CTkLabel(self.master, text="Peso: ")
    self.weight_input = ctk.CTkEntry(self.master, placeholder_text="Peso: 0,00 Kg")

    self.lot_label = ctk.CTkLabel(self.master, text="Insira a quantidade de caixas:")
    self.lot_input = ctk.CTkEntry(self.master, placeholder_text="N° de caixas:")

    self.print_button = ctk.CTkButton(self.master, text="Imprimir", command=self.print_label, width=150, height=50, corner_radius=10)

    padding = {'padx': 5, 'pady': 10}

    self.id_label.grid(row=0,column=1, **padding)
    self.id_input.grid(row=0, column=2, **padding)
    self.search_button.grid(row=0, column=3, **padding)
    self.clear_inputs_button.grid(row=1, column=3, **padding)

    self.serial_com_port_menu.grid(row=0, column=4, **padding)

    self.code_label.grid(row=1, column=1, **padding)
    self.code_input.grid(row=1,column=2, **padding)

    self.client_label.grid(row=2, column=1, **padding)
    self.client_input.grid(row=3, column=1, columnspan=4, **padding)
    
    self.description_label.grid(row=4, column=1, **padding)
    self.description_input.grid(row=5, column=1, columnspan=4, **padding)

    self.barcode_label.grid(row=6, column=1, **padding)
    self.barcode_input.grid(row=6, column=2, **padding)

    self.lot_label.grid(row=6, column=3)
    self.lot_input.grid(row=6, column=4)

    self.quantity_label.grid(row=7, column=1, **padding)
    self.quantity_input.grid(row=7, column=2, **padding)

    self.weight_label.grid(row=7, column=3)
    self.manual_weight_checkbox.grid(row=8, column=3)
    self.weight_input.grid(row=7, column=4)

    self.print_button.grid(row=10, column=2, columnspan=3, pady=20)

  def serial_port_callback(self, choice: str):
    if self.serial_com.is_open:
      self.serial_com.close()

    self.serial_com.set_port(choice)
    response = self.serial_com.connect()
    ctkmsg(self.master, title="Comunicação Serial", message=response, option_1="OK")

  def manual_weight_callback(self):
    print("Manual weight chekbox value: ", self.manual_weight_var.get())

  def search_id(self, event=None):
    self.id = f"OP-{self.id_input.get().zfill(7)}"
    
    if not (self.label_data_df['Código'] == self.id).any():
      ctkmsg(title="Não encontrado", message=f"Valor: {self.id} não foi encontrado", option_1="OK", icon="warning")
      return
      
    try:
      info = self.label_data.get_data(self.id, "")
      self.client_var.set(info.client)
      self.code_var.set(info.code)
      self.description_var.set(info.description)
      self.barcode_var.set(info.barcode)
      self.quantity_var.set(info.quantity)
      self.lot_var.set(1)

      if self.client_input.get() != "":
        ctkmsg(self.master, title="Aviso", message="Insira outra OP", option_1="OK", icon="warning")
        return

      self.client_input.insert(0, self.client_var.get())
      self.code_input.insert(0, self.code_var.get())
      self.description_input.insert(0, self.description_var.get())
      self.barcode_input.insert(0, self.barcode_var.get())
      self.quantity_input.insert(0, self.quantity_var.get())
      self.lot_input.insert(0, self.lot_var.get())

      
      if self.manual_weight_var.get() == "off":
        weight: float = self.serial_com.get_weight()
        """ str_weight: str = f"{weight:.2f}"
        print("PESO PUXADO:", str_weight)
        str_weight: str = str_weight.replace(".", ",")
        self.weight_var.set(str_weight) """
        self.weight_input.insert(0, weight)

    except Exception as e:
      ctkmsg(title="Erro", message=e ,option_1="OK", icon='cancel')
    
  def clear_inputs(self, event=None):
    self.id_input.delete(0, ctk.END)
    self.client_input.delete(0, ctk.END)
    self.code_input.delete(0, ctk.END)
    self.description_input.delete(0, ctk.END)
    self.barcode_input.delete(0, ctk.END)
    self.quantity_input.delete(0, ctk.END)
    self.weight_input.delete(0, ctk.END)
    self.lot_input.delete(0, ctk.END)

  def print_label(self):
    quantity = int(self.quantity_input.get())
    lot = int(self.lot_input.get())

    if quantity % lot != 0:
      ctkmsg(self.master, title="Erro", message="Quantidade total não pode ser divisível pelo número de caixas", icon='warning', option_1="OK")
      self.lot_quantity = int(quantity/lot)
      return

    if self.weight_input.get() == "":
      ctkmsg(self.master, title="Aviso", message="Campo de peso está vazio, por favor preencha!", icon='warning', option_1="OK")
      return
    
    try:
      label = LabelPrint(LabelInfo(self.client_input.get(), self.code_input.get(), self.description_input.get(), self.lot_quantity, self.weight_input.get()))
      label.create_label()
      time.sleep(0.5)
      
      for _ in range(int(self.lot_input.get())):
        time.sleep(0.5)
        label.print_label()

    except Exception as e:
      ctkmsg(self.master, message=f"Erro ao imprimir: {e}", title="Erro", icon="cancel", option_1="OK")
    
    finally:
      self.clear_inputs()