import sys
import json
import pathlib
import asyncio
import qasync
from datetime import timedelta, datetime as dt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QMessageBox,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGridLayout,
)
from core.get_data import get_op_data_by_codigo, get_all_op_data_on_carga_maquina, OrdemDeProducao
from core.balance_communication import BalanceCommunication
from core.generate_labels import Label

start_deliver_date: str = (dt.now()-timedelta(days=35)).strftime("%d-%m-%Y")
end_deliver_date: str = (dt.now()+timedelta(days=35)).strftime("%d-%m-%Y")
TMP_PATH: pathlib.Path = pathlib.Path().parent / "tmp/"
TMP_PATH.mkdir(parents=True, exist_ok=True)
ORDER_PATH: str = f"{TMP_PATH}/ordens_{start_deliver_date}_{end_deliver_date}.json"

class LabelGenerator(QWidget):
    balance: BalanceCommunication
    is_closing: bool

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Etiquetas")
        self.setFixedSize(1200, 600)
        self.create_layout()
        self.set_styles()
        self.balance = BalanceCommunication()
        self.is_closing = False
    
    def close_event(self, event):
        if not self.is_closing:
            event.ignore()
            asyncio.create_task(self.handle_close())

    async def handle_close(self):
        self.is_closing = True
        if self.balance.is_open:
            self.balance.stop_serial()
        self.balance.close()
        self.close()
        QApplication.quit()

    def on_port_changed(self):
        self.balance.set_port(self.port_select.currentText())
        self.balance.connect()

    def on_clear_inputs_button_clicked(self):
        self.op_input.clear()
        self.code_input.clear()
        self.client_input.clear()
        self.description_input.clear()
        self.barcode_input.clear()
        self.quantity_input.clear()
        self.box_count_input.clear()
        self.weight_input.clear()

    @qasync.asyncSlot()
    async def on_search_button_clicked(self):
        if(self.op_input.text() == ""):
            QMessageBox.warning(self, "Erro", "Por favor, insira o número da OP")
            return
        if not pathlib.Path(ORDER_PATH).exists():
            op = await get_op_data_by_codigo(self.op_input.text())
            if op is not None:
                self.code_input.setText(op.material_code)
                self.client_input.setText(op.client)
                self.description_input.setText(op.description)
                self.barcode_input.setText(op.barcode)
                self.quantity_input.setText(str(op.quantity))
                self.box_count_input.setText(str(op.box_count))
                self.weight_input.setText(str(op.weight))
                return
            QMessageBox.warning(self, "Erro", "OP não encontrada na API, puxando dados do Carga Máquina")
            op = await get_all_op_data_on_carga_maquina()
            if op is None:
                QMessageBox.warning(self, "Erro", "Erro ao gerar arquivo dom as OPS")
                
        with open(ORDER_PATH, "r") as file:
            op = json.load(file)
            op_data = op.get(self.op_input.text(), None)
            if op_data is not None:
                print("CLIENTE CODE: ", op_data["client_code"])
                print("NEW BARCODE: ", op_data["barcode"])
                self.code_input.setText(op_data["material_code"])
                self.client_input.setText(op_data["client"])
                self.description_input.setText(op_data["description"])
                self.barcode_input.setText(op_data["barcode"])
                self.quantity_input.setText(str(op_data["quantity"]))
                self.box_count_input.setText(str(op_data["box_count"]))
                self.weight_input.setText(str(op_data["weight"]))
                if not self.weight_checkbox.isChecked():
                    weight: str = str(self.balance.weight/100).replace(".", ",")
                    self.weight_input.setText(weight)
                return
            QMessageBox.warning(self, "Erro", "OP não encontrada")
            return

    @qasync.asyncSlot()
    async def on_print_button_clicked(self):
        if self.op_input.text() == "":
            QMessageBox.warning(self, "Erro", "Por favor, insira o número da OP")
            return

        if self.weight_input.text() == "":
            QMessageBox.warning(self, "Erro", "Por favor, insira o peso do produto")
            return

        if not self.quantity_input.text().isnumeric():
            QMessageBox.warning(self, "Erro", "Por favor, insira a quantidade corretamente")
            return

        op = OrdemDeProducao(
            code=int(self.op_input.text()),
            material_code=self.code_input.text(),
            client=self.client_input.text(),
            description=self.description_input.text(),
            barcode=self.barcode_input.text(),
            quantity=int(self.quantity_input.text()),
            box_count=int(self.box_count_input.text()),
            weight= self.weight_input.text()
        )

        label = Label(op)
        err, err_msg = label.generate_label()
        if err == False:
            QMessageBox.warning(self, "Erro", err_msg)
            return

        QMessageBox.information(self, "Sucesso", "Etiqueta impressa com sucesso")


    def set_styles(self):
        # Global styles
        self.setStyleSheet("""

            QWidget {
                background-color: #f0f0f0;
                color: #000000
            }

            QLabel {
                font-weight: bold;
                font-size: 14px;
            }

            QLineEdit {
                font-size: 12px;
                border: 1px solid #000000;
                border-radius: 5px;
                padding: 5px;
                margin: 10px;
                width: 200px;
                height: 25px;
            }

            QPushButton {
                background-color: #3674B5;
                color: #fff;
                border-radius: 5px;
                padding: 5px 10px;
                margin: 10px;
                width: 100px;
                height: 25px;
            }

            QPushButton:pressed {
                background-color: #2D6187;
                border: 1px solid #000000;
            }
        """)

        self.clear_inputs_button.setStyleSheet("background-color: #B82132")

    def create_layout(self):
        # Layouts
        self.v_layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.grid_layout = QGridLayout()
        self.h_layout = QHBoxLayout()
        self.grid_layout.setSpacing(10)

        # Checkbox
        self.weight_checkbox = QCheckBox("Inserir peso manualmente?")
        
        # Dropdown menu
        self.port_select = QComboBox()

        # Labels and inputs
        labels: list[dict] = [
            {"label": "op_label", "text": "Número da OP:", "row": 0, "col": 0},
            {"label": "code_label", "text": "Código do produto:", "row": 1, "col": 0},
            {"label": "client_label", "text": "Nome do cliente:"},
            {"label": "description_label", "text": "Descrição do produto:"},
            {"label": "barcode_label", "text": "Código de barras:"},
            {"label": "quantity_label", "text": "Quantidade total:"},
            {"label": "box_count_label", "text": "Quantidade de caixas:"},
            {"label": "weight_label", "text": "Peso do produto:"}
        ]
        inputs: list[dict] = [
            {"input": "op_input", "placeholder": "Número da OP", "row": 0, "col": 1, "width": 200},
            {"input": "code_input", "placeholder": "Código do produto", "row": 1, "col": 1, "width": 200},
            {"input": "client_input", "placeholder": "Nome do cliente", "width": 600},
            {"input": "description_input", "placeholder": "Descrição do produto", "width": 600},
            {"input": "barcode_input", "placeholder": "Código de barras", "width": 600},
            {"input": "quantity_input", "placeholder": "Quantidade total", "width": 200},
            {"input": "box_count_input", "placeholder": "Quantidade de caixas", "width": 200},
            {"input": "weight_input", "placeholder": "Peso do produto", "width": 200}
        ]
        # Buttons
        buttons: list[dict] = [
            {"button": "search_button", "text": "Buscar", "row": 0, "col": 2},
            {"button": "clear_inputs_button", "text": "Limpar", "row": 1, "col": 2},
            {"button": "print_button", "text": "Imprimir",}
        ]

        for label, input in zip(labels, inputs):
            setattr(self, label["label"], QLabel(label["text"]))
            getattr(self, label["label"]).setFixedWidth(200)

            setattr(self, input["input"], QLineEdit()) 
            getattr(self, input["input"]).setPlaceholderText(input["placeholder"])
            getattr(self, input["input"]).setFixedWidth(input["width"])

            if "row" and "col" not in label:
                self.form_layout.addRow(getattr(self, label["label"]), getattr(self, input["input"]))

            if "row" and "col" in label:
                self.grid_layout.addWidget(getattr(self, label["label"]), label["row"], label["col"])
                self.grid_layout.addWidget(getattr(self, input["input"]), input["row"], input["col"])
            
            if "row" and "col" in input:
                self.grid_layout.addWidget(getattr(self, label["label"].replace("label", "input")), input["row"], input["col"])
            

        for i, button in enumerate(buttons):
            setattr(self, button["button"], QPushButton(button["text"]))
            if "row" and "col" in button:
                self.grid_layout.addWidget(getattr(self, button["button"]), button["row"], button["col"])
        
        # COM ports
        for i in range(1, 10):
            self.port_select.addItem(f"COM{i}")
        self.port_select.setCurrentIndex(0)
        self.port_select.setFixedHeight(30)
        self.port_select.currentIndexChanged.connect(self.on_port_changed)

        # Button actions
        self.search_button.clicked.connect(self.on_search_button_clicked)
        self.clear_inputs_button.clicked.connect(self.on_clear_inputs_button_clicked)  
        self.print_button.clicked.connect(self.on_print_button_clicked)

        # Layouts
        self.grid_layout.addWidget(self.port_select, 0, 3)
        self.v_layout.addLayout(self.grid_layout)
        self.v_layout.addLayout(self.form_layout)
        self.h_layout.addStretch()
        self.h_layout.addWidget(self.print_button)
        self.h_layout.addWidget(self.weight_checkbox)
        self.h_layout.addStretch()
        self.v_layout.addStretch()
        self.v_layout.addLayout(self.h_layout)
        self.v_layout.addStretch()
        self.setLayout(self.v_layout)

async def app():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = LabelGenerator()
    window.show()
    async with loop:
        loop.run_forever()

if __name__ == "__main__":
    asyncio.run(app())
    