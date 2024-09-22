import serial
import threading
from time import sleep

class Serial(serial.Serial): 
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 0.01) -> None:
        super(Serial, self).__init__(port=port, baudrate=baudrate, timeout=timeout)

        self.running = True
        self.weight = None
        self.thread = threading.Thread(target=self.read_serial)

    def set_port(self, port) -> None:
        self.port: str = port

    def connect(self) -> str:
        try:
            # Abrindo a conexão serial
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            self.thread.start()
            sleep(0.5)
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

    def get_weight(self) -> float:
        return self.weight

    def stop(self) -> None:
        self.running = False
        if self.is_open:
             super().close()  # Fecha a porta serial
        if self.thread.is_alive():
            self.thread.join()  # Aguarda o término da thread