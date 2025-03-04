# funciones_movimiento.py

from src.conexion.conexion_camara_torreta import sock_tx, IP_TORRETA, PORT_ENVIO_TORRETA
from src.clases.CcittCrcXmodem import CcittCrcXmodem

import numpy as np
import struct
from env.environment import cnt_msg


def msg_habilitar(var_buffer_habilitacion): # var_buffer_habilitacion -> [(acimut -- 0 = deshabilitado -- 1 = habilitado) , (elevacion -- 0 = deshabilitado -- 1 = habilitado)]
    #time.sleep(0.1) # Eliminar si no

    global cnt_msg                          # Si no se define como global da error
    '''
    Habilitacion acimut         --> 0x 00 03
    Habilitacion elevacion      --> 0x 00 04
    Inhabilitacion acimut       --> 0x 00 05
    Inhabilitacion elevacion    --> 0x 00 06
    '''
    if var_buffer_habilitacion == 0:
        operacion = '0x05'
    elif var_buffer_habilitacion == 1:
        operacion = '0x03'
    elif var_buffer_habilitacion == 2:
        operacion = '0x06'
    elif var_buffer_habilitacion == 3:
        operacion = '0x04'

    msg_a =    (struct.pack('B', int('0xEA', 16))+      # Preambulo
                struct.pack('B', int('0x00', 16))+      # Longitud MSB
                struct.pack('B', int('0x00', 16)))      # Longitud LSB
    
    msg_crc =  (struct.pack('B', cnt_msg)+              # Contador mensaje
                struct.pack('B', int('0x00', 16))+      # Comando 0x00 / Peticion 0x01
                struct.pack('B', int('0x00', 16))+      # Control MSB
                struct.pack('B', int(operacion, 16)))   # Control LSB | 0x 00 07 --> velocidad

    #print(msg_crc)

    obj = CcittCrcXmodem(0x1021, 0x0000)  # El CRC se genera siguiendo el estandar CCITT-CRC16 (0x1021) 
                                            # siguiendo un valor inicial de 0x0000
        
    crc_int = obj.ccitt_crc16(msg_crc)      # El CRC se calcula desde el byte contador de mensaje (byte número 3) 
                                            # hasta el ultimo byte de la carga de pago (byte numero 7+N)
        
    crc_bytes = obj.int2bytes(crc_int)      # Convertir CRC a tipo Byte

    bytesToSend =  (msg_a       +
                    msg_crc     +
                    crc_bytes)

    cnt_msg = np.uint8(cnt_msg +1)          # Incrementar contador de mensaje

    sock_tx.sendto(bytesToSend,(IP_TORRETA, PORT_ENVIO_TORRETA))
