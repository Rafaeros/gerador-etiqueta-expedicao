import io
import serial
import threading

class BalanceCommunication(serial.Serial):
    port: str
    baudrate: int
    timeout: int
    weight: int
    running: bool

    def __init__(self)  -> None:
        super().__init__()
        self.set_baudrate()
        self.set_timeout()
        self.running = True
        self.weight = 0 
        self.thread = threading.Thread(target=self.read_serial)
        
    def set_port(self, port: str = "COM3") -> None:
        self.port = port
    
    def set_baudrate(self, baudrate: int = 9600) -> None:
        self.baudrate = baudrate
    
    def set_timeout(self, timeout: int = 1) -> None:
        self.timeout = timeout
        
    def connect(self) -> bool:
        try:
            if not self.is_open:
                self.open()
            self.thread.start()
            return True
        except serial.SerialException:
            return False
    
    def read_serial(self) -> int | str:
        sio = io.TextIOWrapper(io.BufferedRWPair(self, self))
        while self.running:
            try:
                line = sio.readline()
                if line.startswith("D"):
                    self.weight = int(line[1:].replace(".", ""))
                    sio.flush()
                sio.flush()
            except serial.SerialException:
                return "Serial error"
                self.reconnect()
            
    def reconnect(self) -> None:
        self.stop_serial()
        self.connect()
            
    def stop_serial(self)  -> None:
        if self.is_open:
            self.close()
        self.running = False
        self.thread.join()

if __name__ == "__main__":
    balance = BalanceCommunication()
    balance.set_port()
    balance.set_baudrate()
    balance.set_timeout()
    balance.connect()