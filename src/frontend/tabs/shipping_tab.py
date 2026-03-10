import pathlib
import json
import logging
import webbrowser
import qasync
from datetime import datetime as dt, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from src.core.api import get_all_op_data_on_carga_maquina
from src.models.schema import OrdemDeProducao
from src.utils.labels import ShippingLabelGenerator


class ShippingTab(QWidget):
    def __init__(self, config_manager, printer_manager, balance, session_manager, is_connected=True, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.printer_manager = printer_manager
        self.balance = balance
        self.session_manager = session_manager
        self.is_connected = is_connected
        
        # Cache em memória para OPs já buscadas na sessão
        self.cached_ops = None 
        
        # Calcula o nome exato do arquivo baseado na janela de 50 dias
        start_date = (dt.now() - timedelta(days=50)).strftime("%d-%m-%Y")
        end_date = (dt.now() + timedelta(days=50)).strftime("%d-%m-%Y")
        self.order_data_path = pathlib.Path(f"./tmp/ordens_{start_date}_{end_date}.json")

        self.create_layout()

    def create_layout(self) -> None:
        """Constructs the UI layout."""
        self.v_layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.grid_layout = QGridLayout()
        self.h_layout = QHBoxLayout()
        self.grid_layout.setSpacing(10)

        self.weight_checkbox = QCheckBox("Inserir peso manualmente?")
        self.port_select = QComboBox()

        labels: list[dict] = [
            {"label": "op_label", "text": "Número da OP:", "row": 0, "col": 0},
            {"label": "code_label", "text": "Código do produto:", "row": 1, "col": 0},
            {"label": "client_label", "text": "Nome do cliente:"},
            {"label": "description_label", "text": "Descrição do produto:"},
            {"label": "barcode_label", "text": "Código de barras:"},
            {"label": "quantity_label", "text": "Quantidade total:"},
            {"label": "box_count_label", "text": "Quantidade de caixas:"},
            {"label": "weight_label", "text": "Peso do produto:"},
        ]
        
        inputs: list[dict] = [
            {"input": "op_input", "placeholder": "Número da OP", "row": 0, "col": 1, "width": 200},
            {"input": "code_input", "placeholder": "Código do produto", "row": 1, "col": 1, "width": 200},
            {"input": "client_input", "placeholder": "Nome do cliente", "width": 600},
            {"input": "description_input", "placeholder": "Descrição do produto", "width": 600},
            {"input": "barcode_input", "placeholder": "Código de barras", "width": 600},
            {"input": "quantity_input", "placeholder": "Quantidade total", "width": 200},
            {"input": "box_count_input", "placeholder": "Quantidade de caixas", "width": 200},
            {"input": "weight_input", "placeholder": "Peso do produto", "width": 200},
        ]

        buttons: list[dict] = [
            {"button": "search_button", "text": "Buscar", "row": 0, "col": 2, "primary": True},
            {"button": "clear_inputs_button", "text": "Limpar", "row": 1, "col": 2, "primary": False},
            {"button": "print_button", "text": "Imprimir Etiqueta", "primary": True},
        ]

        for label, input_data in zip(labels, inputs):
            setattr(self, label["label"], QLabel(label["text"]))
            getattr(self, label["label"]).setFixedWidth(200)

            setattr(self, input_data["input"], QLineEdit())
            getattr(self, input_data["input"]).setPlaceholderText(input_data["placeholder"])
            getattr(self, input_data["input"]).setFixedWidth(input_data["width"])

            if "row" not in label and "col" not in label:
                self.form_layout.addRow(getattr(self, label["label"]), getattr(self, input_data["input"]))

            if "row" in label and "col" in label:
                self.grid_layout.addWidget(getattr(self, label["label"]), label["row"], label["col"])
                self.grid_layout.addWidget(getattr(self, input_data["input"]), input_data["row"], input_data["col"])

        for button in buttons:
            btn = QPushButton(button["text"])
            if button.get("primary"):
                btn.setObjectName("primary")
            setattr(self, button["button"], btn)
            if "row" in button and "col" in button:
                self.grid_layout.addWidget(getattr(self, button["button"]), button["row"], button["col"])

        self.clear_inputs_button.setStyleSheet("background-color: #B82132; color: white; border: none;")
        self.author_button = QPushButton("Feito por: Rafael Costa")
        self.author_button.setStyleSheet("color: #475569; border: none; font-size: 12px; text-align: left;")
        
        for i in range(1, 10):
            self.port_select.addItem(f"COM{i}")
        self.port_select.setCurrentIndex(0)
        self.port_select.setFixedWidth(150)
        self.port_select.currentIndexChanged.connect(self.on_port_changed)

        self.search_button.clicked.connect(self.on_search_button_clicked)
        self.clear_inputs_button.clicked.connect(self.on_clear_inputs_button_clicked)
        self.print_button.clicked.connect(self.on_print_button_clicked)
        self.author_button.clicked.connect(self.on_author_button_clicked)

        if not self.is_connected:
            self.search_button.setText("Busca Offline")

        self.grid_layout.addWidget(self.port_select, 0, 3)
        self.v_layout.addLayout(self.grid_layout)
        self.v_layout.addSpacing(10)
        self.v_layout.addLayout(self.form_layout)
        self.h_layout.addStretch()
        self.h_layout.addWidget(self.weight_checkbox)
        self.h_layout.addSpacing(20)
        self.h_layout.addWidget(self.print_button)
        self.h_layout.addStretch()
        self.v_layout.addSpacing(20)
        self.v_layout.addLayout(self.h_layout)
        self.v_layout.addStretch()
        self.v_layout.addWidget(self.author_button)
        self.setLayout(self.v_layout)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Return and getattr(self, "weight_input").hasFocus():
            self.on_print_button_clicked()
            getattr(self, "code_input").setFocus()
        elif event.key() == Qt.Key.Key_Return:
            self.on_search_button_clicked()
        elif event.key() == Qt.Key.Key_Delete:
            self.on_clear_inputs_button_clicked()

    def on_port_changed(self) -> None:
        self.balance.set_port(self.port_select.currentText())
        self.balance.connect()
        if not self.balance.is_open:
            QMessageBox.warning(self, "Erro", f"Erro ao conectar na porta {self.balance.port}")
        else:
            QMessageBox.information(self, "Sucesso", f"Conectado à {self.balance.port}")

    def on_clear_inputs_button_clicked(self) -> None:
        getattr(self, "op_input").clear()
        getattr(self, "code_input").clear()
        getattr(self, "client_input").clear()
        getattr(self, "description_input").clear()
        getattr(self, "barcode_input").clear()
        getattr(self, "quantity_input").clear()
        getattr(self, "box_count_input").clear()
        getattr(self, "weight_input").clear()

    def on_author_button_clicked(self):
        webbrowser.open("https://github.com/Rafaeros")

    @qasync.asyncSlot()
    async def on_search_button_clicked(self) -> None:
        op_str = getattr(self, "op_input").text().strip()
        if not op_str:
            QMessageBox.warning(self, "Aviso", "Insira o número da OP")
            return

        try:
            op_number = int(op_str)
        except ValueError:
            QMessageBox.warning(self, "Erro", "O número da OP deve conter apenas números.")
            return

        self.search_button.setText("Buscando...")
        self.search_button.setEnabled(False)

        try:
            # 1. Verifica se já não temos os dados na memória (Cache da Sessão)
            if self.cached_ops is None:
                
                # 2. Verifica se o arquivo do dia existe
                if self.order_data_path.exists():
                    logging.info("Arquivo local encontrado: %s. Carregando dados...", self.order_data_path.name)
                    with open(self.order_data_path, "r", encoding="utf-8") as f:
                        self.cached_ops = {int(k): v for k, v in json.load(f).items()}
                
                # 3. Se não existir o arquivo, então aciona a API para baixar
                else:
                    logging.info("Arquivo local %s NÃO encontrado. Baixando da API...", self.order_data_path.name)
                    if self.is_connected:
                        self.cached_ops = await get_all_op_data_on_carga_maquina(self.session_manager)
                    else:
                        QMessageBox.warning(self, "Modo Offline", "Você está offline e o arquivo de dados de hoje não foi encontrado.")
                        return
                
                # Proteção final caso a API tenha falhado
                if not self.cached_ops:
                    QMessageBox.warning(self, "Erro", "Falha ao obter os dados das OPs.")
                    return

            # Busca no cache da memória
            op_data = self.cached_ops.get(op_number)
            
            if not op_data:
                QMessageBox.warning(self, "Erro", "OP não encontrada na base de dados (Verifique se não é muito antiga).")
                return

            # Preenche a Interface
            getattr(self, "code_input").setText(op_data.get("material_code", ""))
            getattr(self, "client_input").setText(op_data.get("client", ""))
            getattr(self, "description_input").setText(op_data.get("description", ""))
            getattr(self, "barcode_input").setText(op_data.get("barcode", ""))
            getattr(self, "quantity_input").setText(str(op_data.get("quantity", "")))
            getattr(self, "box_count_input").setText(str(op_data.get("box_count", 1)))

            # Lógica da Balança
            weight_inp = getattr(self, "weight_input")
            if self.weight_checkbox.isChecked() or not self.balance.is_open:
                weight_inp.setText("")
                weight_inp.setFocus()
            else:
                weight = str(self.balance.weight / 100).replace(".", ",")
                weight_inp.setText(weight)

        except Exception as e:
            logging.error(f"Failed to load OP: {e}")
            QMessageBox.critical(self, "Erro", "Ocorreu um erro ao processar a busca da OP.")
        finally:
            self.search_button.setText("Buscar OP" if self.is_connected else "Busca Offline")
            self.search_button.setEnabled(True)

    @qasync.asyncSlot()
    async def on_print_button_clicked(self):
        op_text = getattr(self, "op_input").text()
        qty_text = getattr(self, "quantity_input").text()
        weight_text = getattr(self, "weight_input").text()

        if not op_text:
            QMessageBox.warning(self, "Erro", "Por favor, insira o número da OP")
            return
        if not weight_text:
            QMessageBox.warning(self, "Erro", "Por favor, insira o peso do produto")
            return
        if not qty_text.isnumeric():
            QMessageBox.warning(self, "Erro", "Por favor, insira a quantidade corretamente")
            return

        try:
            op = OrdemDeProducao(
                code=int(op_text),
                material_code=getattr(self, "code_input").text(),
                client=getattr(self, "client_input").text(),
                description=getattr(self, "description_input").text(),
                barcode=getattr(self, "barcode_input").text(),
                quantity=int(qty_text),
                box_count=int(getattr(self, "box_count_input").text() or 1),
                weight=weight_text,
            )

            generator = ShippingLabelGenerator(op)
            success, error, paths = generator.generate()

            if not success:
                QMessageBox.warning(self, "Erro", error)
                return

            target_printer = self.config_manager.get("printer_name", "") or self.printer_manager.get_default_printer()
            
            all_printed = True
            for path in paths:
                if not self.printer_manager.print_document(path, target_printer):
                    all_printed = False

            if all_printed:
                QMessageBox.information(self, "Sucesso", "Etiqueta impressa com sucesso")
                self.on_clear_inputs_button_clicked()
            else:
                QMessageBox.warning(self, "Erro", "Falha ao enviar documento para a impressora.")

        except ValueError as e:
            QMessageBox.warning(self, "Aviso", f"Erro nos dados: {e}")