import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QCheckBox,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGridLayout,
    QSizePolicy
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Signal

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
        self.setStyleSheet("""
            QWidget { font-size: 16px;}
            QVBoxLayout { background-color: #F0F0F0; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
            QHBoxLayout { background-color: #F0F0F0; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
            QFormLayout { background-color: #F0F0F0; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
            QLabel { color: #333; margin-bottom: 5px; font-weight: bold; color: #fff}
            QLineEdit { margin-bottom: 10px; color: #fff}
            QPushButton { background-color: #0000FF}
        """)
        self.create_layout()

    def on_checkbox_changed(self):
        print("Checkbox state: ", self.weight_checkbox.isChecked())

    def create_layout(self):
        # Layouts
        self.v_layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.grid_layout = QGridLayout()
        self.h_layout = QHBoxLayout()

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
            {"input": "client_input", "placeholder": "Nome do cliente", "width": 500},
            {"input": "description_input", "placeholder": "Descrição do produto", "width": 500},
            {"input": "barcode_input", "placeholder": "Código de barras", "width": 500},
            {"input": "quantity_input", "placeholder": "Quantidade total", "width": 500},
            {"input": "box_count_input", "placeholder": "Quantidade de caixas", "width": 500},
            {"input": "weight_input", "placeholder": "Peso do produto", "width": 500}
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
        
        for i in range(1, 10):
            self.port_select.addItem(f"COM{i}")

        
        # Layouts
        self.grid_layout.addWidget(self.port_select, 0, 3)
        self.v_layout.addLayout(self.grid_layout)
        self.v_layout.addLayout(self.form_layout)
        self.h_layout.addWidget(self.print_button)
        self.h_layout.addWidget(self.weight_checkbox)
        self.v_layout.addLayout(self.h_layout)
        self.setLayout(self.v_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelGenerator()
    window.show()
    app.exec()