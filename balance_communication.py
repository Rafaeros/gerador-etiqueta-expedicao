import serial
import threading
from time import sleep

class Serial(serial.Serial):
    running: bool
    weight: float
    baud_rate: int
    port: str
    timeout: int
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

    def set_timeout(self, timeout=0.01):
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
                sleep(0.2)
                # Obtendo resposta da balança e formatando o o peso
                response = self.serial.read(9).decode('utf-8').split('\r')[0]
                
                if response[0] == "D":
                    try:
                        weight = float(response[1:])
                        self.weight = weight
                        self.serial.reset_input_buffer()
                    except ValueError:
                        print(f'Erro ao converter "{response}" para float.')

                self.serial.reset_input_buffer()

    def get_weight(self):
        return self.weight

    def stop(self):
        self.running = False
        self.serial.close()
        self.thread.join()
    
    def close(self):
        self.serial.close()