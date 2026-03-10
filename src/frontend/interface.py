import asyncio
import logging
from PySide6.QtWidgets import QMainWindow, QTabWidget
from PySide6.QtGui import QCloseEvent

from src.core.config import ConfigManager
from src.core.session_manager import SessionManager
from src.core.balance import BalanceCommunication
from src.utils.printer import PrinterManager
from src.frontend.tabs.shipping_tab import ShippingTab
from src.frontend.tabs.configs_tab import ConfigsTab

class ShippingInterface(QMainWindow):
    def __init__(
        self,
        config_manager: ConfigManager,
        printer_manager: PrinterManager,
        balance: BalanceCommunication,
        session_manager: SessionManager,  # <-- ADICIONADO
        is_connected: bool = True
    ):
        super().__init__()
        self.config_manager = config_manager
        self.printer_manager = printer_manager
        self.balance = balance
        self.session_manager = session_manager
        self.is_connected = is_connected

        self.setWindowTitle("Gerador de Etiquetas - Expedição")
        self.setup_ui()

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Repassando o session_manager e a flag is_connected
        self.shipping_tab = ShippingTab(
            self.config_manager, 
            self.printer_manager, 
            self.balance, 
            self.session_manager, 
            self.is_connected
        )
        self.config_tab = ConfigsTab(self.config_manager, self.printer_manager)

        self.tabs.addTab(self.shipping_tab, "Expedição")
        self.tabs.addTab(self.config_tab, "Configurações")

    def closeEvent(self, event: QCloseEvent):
        logging.info("Shutting down application...")
        if self.balance and self.balance.is_open:
            self.balance.stop_serial()
            self.balance.close()
        
        if self.session_manager and hasattr(self.session_manager, "session"):
            asyncio.create_task(self.session_manager.session.close())
            
        event.accept()