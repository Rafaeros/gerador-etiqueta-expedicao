from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QSpacerItem,
    QSizePolicy
)
from PySide6.QtCore import Qt

from src.core.config import ConfigManager
from src.utils.printer import PrinterManager


class ConfigsTab(QWidget):
    """
    Configuration tab widget.
    Allows the user to update CargaMaquina credentials and select the default printer.
    """

    def __init__(self, config_manager: ConfigManager, printer_manager: PrinterManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.printer_manager = printer_manager

        self.setup_ui()
        self.load_current_configs()

    def setup_ui(self):
        """Builds the UI layout for the configuration tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # --- Section 1: CargaMaquina Credentials ---
        credentials_group = QGroupBox("Credenciais do CargaMáquina")
        credentials_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #0f172a;
            }
        """)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Digite seu usuário")
        self.input_username.setMinimumWidth(300)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Digite sua senha")
        self.input_password.setMinimumWidth(300)
        self.input_password.setEchoMode(QLineEdit.Password) # Masks the password

        form_layout.addRow(QLabel("Usuário:"), self.input_username)
        form_layout.addRow(QLabel("Senha:"), self.input_password)
        
        credentials_layout = QVBoxLayout()
        credentials_layout.addLayout(form_layout)
        credentials_group.setLayout(credentials_layout)

        # --- Section 2: Printer Selection ---
        printer_group = QGroupBox("Configuração de Impressão")
        printer_group.setStyleSheet(credentials_group.styleSheet()) # Reuse the same style
        
        printer_layout = QVBoxLayout()
        printer_layout.setSpacing(10)

        lbl_printer_desc = QLabel("Selecione a impressora padrão para as etiquetas de expedição:")
        lbl_printer_desc.setStyleSheet("color: #475569;")
        
        self.combo_printers = QComboBox()
        self.combo_printers.setMinimumWidth(300)
        self.combo_printers.setMinimumHeight(35)
        
        # Populate printers using PrinterManager
        available_printers = self.printer_manager.list_printers()
        if available_printers:
            self.combo_printers.addItems(available_printers)
        else:
            self.combo_printers.addItem("Nenhuma impressora encontrada")
            self.combo_printers.setEnabled(False)

        printer_layout.addWidget(lbl_printer_desc)
        printer_layout.addWidget(self.combo_printers)
        printer_group.setLayout(printer_layout)

        # --- Section 3: Save Button ---
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("Salvar Configurações")
        self.btn_save.setMinimumHeight(45)
        self.btn_save.setMinimumWidth(200)
        self.btn_save.setObjectName("primary") # Applies the purple/blue gradient from your theme
        self.btn_save.clicked.connect(self.save_configs)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)

        # Assemble Main Layout
        main_layout.addWidget(credentials_group)
        main_layout.addWidget(printer_group)
        main_layout.addStretch() # Pushes everything to the top
        main_layout.addLayout(btn_layout)

    def load_current_configs(self):
        """Loads the current configuration from the ConfigManager into the UI."""
        # Load Credentials
        session_cfg = self.config_manager.get_session_config()
        self.input_username.setText(session_cfg.get("username", ""))
        self.input_password.setText(session_cfg.get("password", ""))

        # Load Printer
        saved_printer = self.config_manager.get("printer_name", "")
        if saved_printer:
            index = self.combo_printers.findText(saved_printer)
            if index >= 0:
                self.combo_printers.setCurrentIndex(index)

    def save_configs(self):
        """Saves the inputs back into the ConfigManager and alerts the user."""
        # Get values
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()
        selected_printer = self.combo_printers.currentText()

        # Save to JSON
        self.config_manager.set_session_config({
            "username": username,
            "password": password
        })
        
        if self.combo_printers.isEnabled():
            self.config_manager.set("printer_name", selected_printer)

        # Visual Feedback
        QMessageBox.information(
            self, 
            "Sucesso", 
            "Configurações salvas com sucesso!\n\n"
            "Nota: As alterações de usuário/senha exigirão a reinicialização do aplicativo para fazerem efeito."
        )