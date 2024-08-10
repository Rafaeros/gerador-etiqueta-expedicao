import serial
from time import sleep

class serial_com():
    def __init__(self):
        self.port: str
        self.baud_rate: int = 9600
        self.timeout: int = 2 # Tempo de espera para leitura

    def set_port(self, port):
        self.port = port

    def connection(self):
        try:
            # Abrindo a conexão serial
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            print(f'Conectado à porta {self.port} com baud rate {self.baud_rate}')
        except serial.SerialException as e:
            print(f'Erro na comunicação: {e}')

    def read_serial(self) -> str:
        sleep(5)
        # Lendo a resposta da balança
        response = self.serial.readline().decode().strip()
        print(f'Resposta da balança: {response}')
        self.serial.close()
        return response

con = serial_com()
con.set_port('COM5')
con.connection()
con.read_serial()