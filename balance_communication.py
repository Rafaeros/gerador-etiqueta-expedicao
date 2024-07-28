import serial

# Configuração da porta serial
port = 'COM3'  # Substitua por sua porta COM correta
baud_rate = 9600  # Defina a taxa de transmissão conforme necessário
timeout = 1  # Tempo de espera para leitura em segundos

try:
    # Abrindo a conexão serial
    ser = serial.Serial(port, baud_rate, timeout=timeout)
    print(f'Conectado à porta {port} com baud rate {baud_rate}')

    # Enviando comando para a balança, se necessário
    command = b'COMMAND_HERE\r\n'  # Comando específico para a balança
    ser.write(command)

    # Lendo a resposta da balança
    response = ser.readline().decode().strip()
    print(f'Resposta da balança: {response}')

except serial.SerialException as e:
    print(f'Erro na comunicação: {e}')
finally:
    # Fechando a conexão serial
    if ser.is_open:
        ser.close()
        print('Conexão serial fechada.')