import os
import sys
import asyncio
import logging
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
import qasync

from src.core.config import ConfigManager
from src.core.session_manager import SessionManager
from src.core.balance import BalanceCommunication
from src.utils.printer import PrinterManager
from src.frontend.interface import ShippingInterface
from src.frontend.dialogs.login_dialog import LoginDialog

def load_stylesheet(app: QApplication) -> None:
    """Loads the global QSS stylesheet for the application."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(base_dir, "src", "frontend", "theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        logging.warning("Theme file not found at %s", qss_path)

async def startup_logic(config_manager: ConfigManager, session_manager: SessionManager) -> bool:
    """Handles initial authentication."""
    session_cfg = config_manager.get_session_config()

    # 1. Prompt for credentials if none are saved
    if not session_cfg.get("username") or not session_cfg.get("password"):
        login_dialog = LoginDialog(config_manager)
        if login_dialog.exec() != QDialog.Accepted:
            sys.exit(0) # Exit app if user closes login dialog

    # 2. Attempt Authentication
    is_connected = await session_manager.login()
    
    if not is_connected:
        QMessageBox.warning(
            None,
            "Modo Offline",
            "Não foi possível conectar ao CargaMáquina (Falha de rede ou credencial).\n\n"
            "As buscas de OP tentarão usar o último cache local salvo em seu computador."
        )
        
    return is_connected

def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    load_stylesheet(app)

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Initialize Core Managers
    config_manager = ConfigManager()
    session_manager = SessionManager(config_manager)
    printer_manager = PrinterManager()
    balance = BalanceCommunication()

    # Run background startup logic (Login)
    is_connected = loop.run_until_complete(startup_logic(config_manager, session_manager))

    # Initialize Main Interface
    window = ShippingInterface(
        config_manager=config_manager, 
        printer_manager=printer_manager, 
        balance=balance, 
        session_manager=session_manager, 
        is_connected=is_connected
    )
    window.show()

    app.setQuitOnLastWindowClosed(True)
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()