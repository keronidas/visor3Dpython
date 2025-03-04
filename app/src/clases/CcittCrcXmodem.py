# CcittCrcXmodem.py

class CcittCrcXmodem:
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

