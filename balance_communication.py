import serial
import threading
from time import sleep

class Serial(serial.Serial):
    running: bool
    weight: float
    baud_rate: int
    port: str
    timeout: int
    serial: serial.Serial
    stable: bool
    
    def __init__(self):
        super(Serial, self).__init__()
        
        self.set_baud_rate()
        self.set_timeout()
        self.running = True
        self.weight = None
        self.thread = threading.Thread(target=self.read_serial)

    def set_port(self, port):
        self.port: str = port

    def set_baud_rate(self, rate=9600):
        self.baud_rate: int = rate

    def set_timeout(self, timeout=1):
        self.timeout: int = timeout

    def connect(self) -> str:
        try:
            # Abrindo a conexão serial
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            sleep(0.5)
            self.thread.start()
            return f"Conectado a porta {self.port} com sucesso:"

        except serial.SerialException as e:
            return f"Erro ao conectar com a porta {self.port}: {e}"

    def read_serial(self) -> str:
        while self.running:
                sleep(0.5)
                # Obtendo resposta da balança e formatando o o peso
                response = self.serial.readline().decode('utf-8').strip()
                if response[0] != "D":
                    stable = False
                    continue
                try:
                    stable = True
                    self.weight = float(weight[1:])
                    print(self.weight)
                except ValueError:
                    print(f'Erro ao converter "{response}" para float.')
                    stable = False
                    continue

    def get_weight(self):
        return self.weight

    def stop(self):
        self.running = False
        self.thread.join()
