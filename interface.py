import sys
import asyncio
import qasync
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
from get_data import get_data_by_codigo

class LabelGenerator(QWidget):
    op_label: QLabel
    op_input: QLineEdit
    code_label: QLabel
    code_input: QLineEdit
    client_label: QLabel
    client_input: QLineEdit
    description_label: QLabel
    description_input: QLineEdit
    barcode_label: QLabel
    barcode_input: QLineEdit
    quantity_label: QLabel
    quantity_input: QLineEdit
    box_count_label: QLabel
    box_count_input: QLineEdit
    weight_label: QLabel
    weight_input: QLineEdit
    port_select: QComboBox
    search_button: QPushButton
    clear_inputs_button: QPushButton
    print_button: QPushButton
    weight_checkbox: QCheckBox

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Etiquetas")
        self.setFixedSize(1200, 600)
        self.create_layout()
        self.set_styles()

    def on_checkbox_changed(self):
        print("Checkbox state: ", self.weight_checkbox.isChecked())

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
        
        op = await get_data_by_codigo(self.op_input.text())
        if op is None:
            QMessageBox.warning(self, "Erro", "Erro ao buscar OP na API")
            return
        else:            
            self.code_input.setText(op.code)
            self.client_input.setText(op.client)
            self.description_input.setText(op.description)
            self.barcode_input.setText(op.barcode)
            self.quantity_input.setText(str(op.quantity))
            self.box_count_input.setText(str(op.box_count))
            self.weight_input.setText(str(op.weight))
            QMessageBox.information(self, "Sucesso", "OP encontrada com sucesso")
    
    @qasync.asyncSlot()
    async def on_print_button_clicked(self):
        pass

    def set_styles(self):
        # Global styles
        self.setStyleSheet("""

            QWidget {
                background-color: #f0f0f0;
                color: #000000
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
        self.weight_checkbox.stateChanged.connect(self.on_checkbox_changed)
        
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
            {"input": "op_input", "placeholder": "Número da OP", "row": 0, "col": 1, "width": 500},
            {"input": "code_input", "placeholder": "Código do produto", "row": 1, "col": 1, "width": 500},
            {"input": "client_input", "placeholder": "Nome do cliente", "width": 800},
            {"input": "description_input", "placeholder": "Descrição do produto", "width": 800},
            {"input": "barcode_input", "placeholder": "Código de barras", "width": 800},
            {"input": "quantity_input", "placeholder": "Quantidade total", "width": 800},
            {"input": "box_count_input", "placeholder": "Quantidade de caixas", "width": 800},
            {"input": "weight_input", "placeholder": "Peso do produto", "width": 800}
        ]
        # Buttons
        buttons: list[dict] = [
            {"button": "search_button", "text": "Buscar", "row": 0, "col": 2},
            {"button": "clear_inputs_button", "text": "Limpar", "row": 1, "col": 2},
            {"button": "print_button", "text": "Imprimir"}
        ]

        for i, label in enumerate(labels):
            setattr(self, label["label"], QLabel(label["text"]))
            getattr(self, label["label"]).setFixedWidth(200)

            setattr(self, inputs[i]["input"], QLineEdit()) 
            getattr(self, inputs[i]["input"]).setPlaceholderText(inputs[i]["placeholder"])
            getattr(self, inputs[i]["input"]).setFixedWidth(inputs[i]["width"])

            if "row" and "col" not in label:
                self.form_layout.addRow(getattr(self, label["label"]), getattr(self, inputs[i]["input"]))

            if "row" and "col" in label:
                self.grid_layout.addWidget(getattr(self, label["label"]), label["row"], label["col"])
                self.grid_layout.addWidget(getattr(self, inputs[i]["input"]), inputs[i]["row"], inputs[i]["col"])
            
            if "row" and "col" in inputs[i]:
                self.grid_layout.addWidget(getattr(self, label["label"].replace("label", "input")), inputs[i]["row"], inputs[i]["col"])
            
        for i, button in enumerate(buttons):
            setattr(self, button["button"], QPushButton(button["text"]))
            if "row" and "col" in button:
                self.grid_layout.addWidget(getattr(self, button["button"]), button["row"], button["col"])
        
        # COM ports
        for i in range(1, 10):
            self.port_select.addItem(f"COM{i}")

        # Button actions
        self.search_button.clicked.connect(self.on_search_button_clicked)
        self.clear_inputs_button.clicked.connect(self.on_clear_inputs_button_clicked)  

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

if __name__ == "__main__":
    app = QApplication([])
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = LabelGenerator()
    window.show()
    with loop:
        loop.run_forever()