import serial
from time import sleep

class Serial():
    def __init__(self):
        self.port: str
        self.baud_rate: int = 9600
        self.timeout: int = 2 # Tempo de espera para leitura

    def set_port(self, port):
        self.port = port

    def connect(self):
        try:
            # Abrindo a conexão serial
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            print(f'Conectado à porta {self.port} com baud rate {self.baud_rate}')

        except serial.SerialException as e:
            print(f'Erro na comunicação: {e}')
            return e

    def read_serial(self):
        while True:
                # Obtendo resposta da balança e formatando o o peso
                response = self.serial.readline().decode().strip()
                if(response and response[0]=="D"):
                    weight = response[1:].split('#')[0]
                    weight = float(weight)
                    formatted_weight = f"{weight:.2f}"
                    return formatted_weight
                # Leitura a cada 0.5 segundos
                sleep(0.5)