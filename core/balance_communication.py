"""
Serial communication with balance
"""

import io
import threading
import time
import logging
import serial

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

class BalanceCommunication(serial.Serial):
    """
    Serial communication with balance
    """

    def __init__(self) -> None:
        """
        Initializes the BalanceCommunication object, setting up default parameters
        for serial communication and starting the reading thread.

        This constructor initializes the serial communication settings for the 
        balance by setting the baudrate and timeout. It also initializes the 
        weight to zero and starts a separate thread for reading data from the 
        serial port.

        Attributes:
            running (bool): A flag to indicate if the serial reading is active.
            weight (int): The current weight value read from the balance.
            thread (threading.Thread): The thread responsible for reading serial data.
        """

        super().__init__()
        self.set_baudrate()
        self.set_timeout()
        self.running = True
        self.weight = 0
        self.thread = threading.Thread(target=self.read_serial)

    def set_port(self, port: str = "COM3") -> None:
        """Sets the serial port for communication with the balance."""
        logging.info("Port set to %s", port)
        self.port = port

    def set_baudrate(self, baudrate: int = 9600) -> None:
        """Sets the baudrate for serial communication with the balance."""
        logging.info("Baudrate set to %d", baudrate)
        self.baudrate = baudrate

    def set_timeout(self, timeout: int = 1) -> None:
        """Sets the timeout for serial communication with the balance."""
        logging.info("Timeout set to %d", timeout)
        self.timeout = timeout

    def connect(self) -> bool:
        """Connects to the serial port and starts the reading thread."""
        logging.info("Connecting to %s", self.port)
        try:
            self.open()
            logging.info("Connected to %s, starting thread", self.port)
            self.thread.start()
            return True
        except serial.SerialException:
            return False

    def read_serial(self) -> int | str:
        """Reads data from the serial port and updates the weight value."""
        sio = io.TextIOWrapper(io.BufferedRWPair(self, self))
        while self.running:
            try:
                line = sio.readline().strip()
                if line.startswith("D"):
                    self.weight = int(line[1:].replace(".", ""))
                    sio.flush()
                sio.flush()
                time.sleep(0.5)
            except serial.SerialException:
                logging.error("Serial communication error, reconnecting...")
                self.reconnect()

    def reconnect(self) -> None:
        """Reconnects to the serial port and starts the reading thread."""
        try:
            self.stop_serial()
            self.connect()
        except serial.SerialException:
            logging.error("Failed to reconnect to %s", self.port)

    def stop_serial(self) -> None:
        """Stops the reading thread and closes the serial port."""
        logging.info("Stopping thread and closing serial port")
        self.close()
        self.running = False
        self.thread.join()


if __name__ == "__main__":
    balance = BalanceCommunication()
    balance.set_port("COM3")
    balance.set_baudrate()
    balance.set_timeout()
    balance.connect()
