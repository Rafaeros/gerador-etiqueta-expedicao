import serial
from time import sleep

class Serial():
    def __init__(self):
        self.set_baud_rate()
        self.set_timeout()

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
            return f"Conectado a porta {self.port} com sucesso:"

        except serial.SerialException as e:
            return f"Erro ao conectar com a porta {self.port}: {e}"

    def read_serial(self) -> str:
        while True:
                # Obtendo resposta da balança e formatando o o peso
                response = self.serial.readline().decode().strip()
                if(response and response[0]=="D"):
                    try:
                        weight = response[1:].split('#')[0]
                        weight = float(weight)
                        formatted_weight = f"{weight:.2f}".lstrip('0').rstrip('.')
                        
                        formatted_weight = formatted_weight.replace('.', ',')

                        return formatted_weight
                    except ValueError:
                        print(f'Erro ao converter "{response}" para float.')
                        continue
                # Leitura a cada 0.5 segundos
                sleep(0.5)