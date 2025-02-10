import qasync
import asyncio
from PySide6.QtWidgets import QApplication
from core.interface import LabelGenerator

if __name__ == "__main__":
    app = QApplication([])
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = LabelGenerator()
    window.show()
    with loop:
        loop.run_forever()