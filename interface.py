import customtkinter as ctk
from CTkMessagebox import CTkMessagebox as ctkmsg
from get_data import LabelData
from label_print import LabelPrint

class Interface:
  def __init__(self, master):
    super().__init__()

    self.variables()
    self.master = master
    self.master.geometry("500x500")

    self.id_input = ctk.CTkEntry(self.master, placeholder_text="Digite o número da OP")
    self.id_input.bind('<Return>', self.search_id)
    self.id_input.pack(pady=10)

    self.search_button = ctk.CTkButton(self.master, command=self.search_id, text="Buscar")
    self.search_button.pack(pady=10)

    self.code_input = ctk.CTkEntry(self.master, textvariable=self.code_var)
    self.code_input.pack(pady=10)


  def variables(self):
    self.master = None
    self.label_data = LabelData('./ordem.xlsx')
    self.label_data_df = self.label_data.label_data
    self.code_var = ctk.StringVar()
    self.id = ''

  def search_id(self, event=None):
    self.id = self.id_input.get()
    if (self.label_data_df['Código'] == self.id).any():
      try:
        ctkmsg(title="Busca", message=f"O valor pesquisado é: {self.id}", option_1="OK", icon="check")
        info = self.label_data.get_data(self.id)
        self.code_var.set(info.code)
        self.code_input.configure(textvariable=self.code_var)
      except Exception as e:
        ctkmsg(title="Erro", message=e ,option_1="OK", icon='cancel')
    else:
      ctkmsg(title="Não encontrado", message=f"Valor: {self.id} não foi encontrado", option_1="OK", icon="warning")
    
    

""" root = ctk.CTk()
root.title("Testando")
#root.attributes("-fullscreen", True)
interface = Interface(root)
root.mainloop() """
