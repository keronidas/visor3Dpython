# clases.py

class ccitt_crc_xmodem:
    def __init__(self, seed, init_crc_value):
        self.seed = seed
        self.init_crc_value = init_crc_value


    def ccitt_crc16(self, data: bytes) -> int:

        # Inicializamos el CRC con el valor inicial predeterminado
        crc = self.init_crc_value

        # Iteramos sobre cada byte de datos
        for byte in data:
            # Aplicamos una operacion XOR en el byte actual y el CRC actual
            crc ^= byte << 8

            # Realizamos un bucle de 8 iteraciones para calcular el CRC
            for _ in range(8):
                # Si el valor mas significativo del CRC es 1, entonces aplicamos la
                # formula de CCITT para calcular el CRC
                if crc & 0x8000:
                    crc = (crc << 1) ^ self.seed
                # Si el valor mas significativo del CRC es 0, entonces solo
                # desplazamos el CRC a la izquierda
                else:
                    crc <<= 1

        # Aplicamos una mascara al CRC final para obtener solo los 16 bits más significativos
        return crc & 0xFFFF

    def int2bytes(self, data):
        return data.to_bytes(2, 'big')

    def mostrar_CRC(self, bytes):
        print([bytes.hex()[x:x+2] for x in range(0, len(bytes.hex()), 2)])

class PID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0
        self.integral = 0

    def reset_integral(self):
        self.integral = 0

    def compute(self, error):
        if error == 0:
            self.integral = 0
        self.integral += error 
        derivative = (error - self.prev_error) 
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative 
        self.prev_error = error

        
        print(f'Proporcional={self.Kp*error}, integral={self.Ki*self.integral}, derivativo={self.Kd*derivative}, output={output}')
        return output
