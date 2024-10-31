"""Interface module."""
import time
import webbrowser as web
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox as ctkmsg

from get_data import LabelData, LabelInfo
from label_print import LabelPrint
from balance_communication import Serial

class Interface:
    """Interface class."""
    def __init__(self) -> None:
        """ Initialize the interface. """
        self.master = ctk.CTk()
        self.master.geometry("800x500")
        self.master.resizable(False, False)
        self.master.title("Gerador De Etiquetas")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.label_data: LabelData = LabelData()
        self.label_data_df = ""
        self.load_data()
        self.serial_com = Serial()
        self.client_var = ctk.StringVar()
        self.code_var = ctk.StringVar()
        self.description_var = ctk.StringVar()
        self.barcode_var = ctk.StringVar()
        self.quantity_var  = ctk.IntVar()
        self.weight_var = ctk.StringVar()
        self.box_var = ctk.IntVar()
        self.manual_weight_var = ctk.StringVar(value="on")
        self.lot_quantity = ''
        self.op= ''
        self.create_window()

    def run(self) -> None:
        """
        Run the interface.
        """
        self.master.mainloop()

    def on_closing(self) -> None:
        """
        Closes the window.
        """
        if self.serial_com.is_open:
            self.serial_com.stop()
        self.master.destroy()

    def load_data(self) -> None:
        """
        Load the data from the Excel file.
        If the file is not found, an error message is shown and the window is closed.
        """
        try:
            self.label_data = LabelData()
            self.label_data_df = self.label_data.label_data
        except FileNotFoundError as e:
            msg = ctkmsg(self.master,
                         title="Erro ao carregar planilha",
                         message=f"Não encontrado o arquivo: ordens.xlsx com a data de hoje ({e})",
                         icon="warning", option_1="OK")
            msg.wait_window()
            if msg.get() == "OK":
                self.master.destroy()

    def create_window(self) -> None:
        """
        Create the window.
        """
        padding: dict = {
            'padx': 5,
            'pady': 10
        }

        labels = [
            {
                'label_name': 'op_label', 
                'label_text': 'Número da OP:', 
                'row': 0, 'column': 1, 
                'padding': padding
            },
            {
                'label_name': 'code_label', 
                'label_text': 'Código:', 
                'row': 1, 
                'column': 1, 
                'padding': padding
            },
            {
                'label_name': 'client_label', 
                'label_text': 
                'Cliente:', 
                'row': 2, 
                'column': 1, 
                'padding': padding
            },
            {
                'label_name': 'description_label', 
                'label_text': 'Descrição:', 
                'row': 4, 'column': 1, 'padding': padding
            },
            {
                'label_name': 'barcode_label', 
                'label_text': 'Código de barras:', 
                'row': 6, 'column': 1, 'padding': padding
            },
            {
                'label_name': 'quantity_label', 
                'label_text': 'Quantidade Total:', 
                'row': 7, 'column': 1, 'padding': padding
            },
            {
                'label_name': 'box_label', 
                'label_text': 'Caixas:', 'row': 6, 
                'column': 3, 'padding': padding
            },
            {
                'label_name': 'weight_label', 
                'label_text': 'Peso (Kg):', 'row': 7, 
                'column': 3, 'padding': padding
            },
            {
                'label_name': 'author', 
                'label_text': 'Autor: Rafael Costa', 
                'row': 11, 
                'column': 4,
                'padding': padding,
                'bind': ('<Button-1>', lambda event: self.author_callback())
            },
        ]

        inputs = [
            {
                'input_name': 'op_input',
                'place_holder': 'Insira o número da OP',
                'width': 300, 
                'height': 28, 'row': 0, 
                'column': 2, 'columnspan': 1, 
                'bind': ('<Return>', self.search_id)
            },
            {
                'input_name': 'code_input',
                'place_holder': 'Insira o código do produto',
                'width': 300, 'height': 35, 'row': 1, 'column': 2,
                'columnspan': 1,
                'padding': padding
            },
            {
                'input_name': 'client_input',
                'place_holder': 'Insira o nome do cliente',
                'width': 550,
                'height': 35,
                'row': 2,
                'column': 2,
                'columnspan': 3,
                'padding': padding
            },
            {
                'input_name': 'description_input',
                'place_holder': 'Insira a descrição do produto',
                'width': 550,
                'height': 35,
                'row': 4,
                'column': 2,
                'columnspan': 3,
                'padding': padding
            },
            {
                'input_name': 'barcode_input',
                'place_holder': 'Insira o código de barras',
                'width': 300,
                'height': 35,
                'row': 6,
                'column': 2,
                'columnspan': 1,
                'padding': padding
            },
            {
                'input_name': 'quantity_input',
                'place_holder': 'Insira a quantidade total',
                'width': 300,
                'height': 35,
                'row': 7,
                'column': 2,
                'columnspan': 1
            },
            {
                'input_name': 'box_input',
                'place_holder': 'Insira o número de caixas',
                'width': 140,
                'height': 28,
                'row': 6,
                'column': 4,
                'columnspan': 1
            },
            {
                'input_name': 'weight_input',
                'place_holder': 'Insira o peso', 
                'width': 140,
                'height': 28,
                'row': 7,
                'column': 4,
                'columnspan': 1
            },
        ]

        buttons = [
            {
                'button_name': 'search_button',
                'button_text': 'Buscar',
                'width': 140,
                'height': 35, 'row': 0,
                'column': 3,
                'columnspan': 1,
                'corner_radius': 10,
                'padding': padding,
                'command': self.search_id,
                'bind': ('<Return>', self.search_id)
            },
            {
                'button_name': 'clear_inputs_button',
                'button_text': 'Limpar',
                'width': 140,
                'height': 35,
                'row': 1,
                'column': 3,
                'columnspan': 1,
                'corner_radius': 10,
                'padding': padding,
                'command': self.clear_inputs,
                'bind': ('<Return>', self.clear_inputs), 'fg_color': 'red'
            },
            {
                'button_name': 'print_button',
                'button_text': 'Imprimir',
                'width': 150,
                'height': 50,
                'row': 10,
                'column': 2,
                'columnspan': 3,
                'corner_radius': 10,
                'pady': 20,
                'command': self.print_label
            }
        ]

        # Instanciando as labels, inputs e buttons e configurando grids
        for ctk_label in labels:
            setattr(self, ctk_label['label_name'],
                    ctk.CTkLabel(self.master, text=ctk_label['label_text']))

            if 'bind' in ctk_label:
                getattr(self, ctk_label['label_name']).configure(text_color='#0000EE')
                getattr(self, ctk_label['label_name']).bind(ctk_label['bind'][0],
                                                            ctk_label['bind'][1])

            getattr(self, ctk_label['label_name']).grid(row=ctk_label['row'],
                                                        column=ctk_label['column'],
                                                        **ctk_label['padding'])

        for ctk_input in inputs:
            setattr(self, ctk_input['input_name'],
                    ctk.CTkEntry(self.master,
                                  placeholder_text=ctk_input['place_holder'],
                                  width=ctk_input['width'],
                                  height=ctk_input['height']))

            if 'bind' in ctk_input:
                getattr(self, ctk_input['input_name']).bind(ctk_input['bind'][0],
                                                            ctk_input['bind'][1])
            if 'padding' in ctk_input:
                getattr(self, ctk_input['input_name']).grid(row=ctk_input['row'],
                                                            column=ctk_input['column'],
                                                            columnspan=ctk_input['columnspan'],
                                                            **ctk_input['padding'])

            getattr(self, ctk_input['input_name']).grid(row=ctk_input['row'],
                                                        column=ctk_input['column'],
                                                        columnspan=ctk_input['columnspan'])

        for ctk_button in buttons:
            setattr(self, ctk_button['button_name'],
                          ctk.CTkButton(self.master,
                                        text=ctk_button['button_text'],
                                        width=ctk_button['width'],
                                        height=ctk_button['height'],
                                        corner_radius=ctk_button['corner_radius'],
                                        command=ctk_button['command']))
            if 'fg_color' in ctk_button:
                getattr(self, ctk_button['button_name']).configure(fg_color=ctk_button['fg_color'])

            if 'bind' in ctk_button:
                getattr(self, ctk_button['button_name']).bind(ctk_button['bind'][0],
                                                              ctk_button['bind'][1])

            if not 'pady' in ctk_button:
                getattr(self, ctk_button['button_name']).grid(row=ctk_button['row'],
                                                              column=ctk_button['column'],
                                                              columnspan=ctk_button['columnspan'],
                                                              **ctk_button['padding'])
            else:
                getattr(self, ctk_button['button_name']).grid(row=ctk_button['row'],
                                                              column=ctk_button['column'],
                                                              columnspan=ctk_button['columnspan'],
                                                              pady=ctk_button['pady'])

        self.serial_menu = ctk.CTkOptionMenu(
                          self.master,
                          values=["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7"],
                          command=self.serial_port_callback).grid(row=0, column=4, **padding
        )

        self.manual_weight_var = ctk.StringVar(value="off")

        self.manual_weight_checkbox = ctk.CTkCheckBox(self.master,
                                                text="Inserir Peso Manualmente",
                                                onvalue="on",
                                                offvalue="off",
                                                variable=self.manual_weight_var,
                                                command=self.manual_weight_callback
                                                ).grid(row=8, column=3)

    def author_callback(self):
        """
        Callback for the author button.
        """
        web.open_new("https://www.linkedin.com/in/rafaeros/")

    def serial_port_callback(self, choice: str) -> None:
        """
        Callback for the serial port menu.
        """
        self.serial_com.set_port(choice)
        response = self.serial_com.connect()
        ctkmsg(self.master, title="Comunicação Serial", message=response, option_1="OK")

    def manual_weight_callback(self) -> None:
        """
        Callback for the manual weight checkbox.
        """
        print("Manual weight chekbox value: ", self.manual_weight_var.get())

    def search_id(self, event=None) -> None:
        """
        Callback for the search button.
        """
        self.op = f"OP-{self.op_input.get().zfill(7)}"

        if not (self.label_data_df['Código'] == self.op).any():
            ctkmsg(title="Não encontrado",
                   message=f"Valor: {self.op} não foi encontrado",
                   option_1="OK", icon="warning")
            return
        try:
            info = self.label_data.get_data(self.op, 1, "")
            self.client_var.set(info.client)
            self.code_var.set(info.code)
            self.description_var.set(info.description)
            self.barcode_var.set(info.barcode)
            self.quantity_var.set(info.quantity)
            self.box_var.set(1)

            if self.client_input.get() != "":
                ctkmsg(self.master, title="Aviso",
                       message="Insira outra OP", option_1="OK", icon="warning")
                return

            self.client_input.insert(0, self.client_var.get())
            self.code_input.insert(0, self.code_var.get())
            self.description_input.insert(0, self.description_var.get())
            self.barcode_input.insert(0, self.barcode_var.get())
            self.quantity_input.insert(0, self.quantity_var.get())
            self.box_input.insert(0, self.box_var.get())

            if self.manual_weight_var.get() == "off":
                time.sleep(0.1)
                weight = self.serial_com.get_weight()
                str_weight: str = f"{weight:.2f}"
                str_weight: str = str_weight.replace(".", ",")
                self.weight_var.set(str_weight)
                self.weight_input.insert(0, self.weight_var.get())
        except Exception as e:
            ctkmsg(title="Erro", message=e ,option_1="OK", icon='cancel')
    def clear_inputs(self, event=None) -> None:
        """
        Callback for the clear inputs button.
        """
        self.op_input.delete(0, ctk.END)
        self.client_input.delete(0, ctk.END)
        self.code_input.delete(0, ctk.END)
        self.description_input.delete(0, ctk.END)
        self.barcode_input.delete(0, ctk.END)
        self.quantity_input.delete(0, ctk.END)
        self.weight_input.delete(0, ctk.END)
        self.box_input.delete(0, ctk.END)

    def print_label(self) -> None:
        """
        Callback for the print button.
        """
        if self.code_input.get() == "":
            ctkmsg(self.master,
                   title="Aviso",
                   message="Insira alguma OP para imprimir",
                   icon='warning',
                   option_1="OK")
            return

        quantity = int(self.quantity_input.get())
        lot = int(self.box_input.get())

        if quantity % lot == 0:
            self.lot_quantity = int(quantity/lot)

            if self.weight_input.get() == "":
                ctkmsg(self.master,
                       title="Aviso",
                       message="Campo de peso está vazio, por favor preencha!",
                       icon='warning',
                       option_1="OK")
                return

            try:
                for i in range(int(self.box_input.get())):
                    boxes = f"{i+1}/{self.box_input.get()}"
                    label_info: LabelInfo = LabelInfo(
                        self.op_input.get(),
                        self.client_input.get(),
                        self.code_input.get(),
                        self.description_input.get(),
                        self.lot_quantity,
                        boxes,
                        self.weight_input.get()
                    )
                    label: LabelPrint = LabelPrint(label_info)

                    if label_info.code.startswith("MWM"):
                        label.label_info.boxes = i+1
                        label.create_mwm_label()
                        time.sleep(0.5)
                        label.print_label()
                    else:
                        label.create_label()
                        time.sleep(0.5)
                        label.print_label()

            except RuntimeError as e:
                ctkmsg(self.master,
                       message=f"Erro ao imprimir: {e}",
                       title="Erro",
                       icon="cancel",
                       option_1="OK")
            finally:
                self.clear_inputs()
        else:
            ctkmsg(self.master,
                   title="Erro",
                   message="Quantidade total não pode ser divisível pelo número de caixas",
                   icon='warning',
                   option_1="OK")
