# funciones_velocidad.py

from src.funciones.funciones_zoom import float_to_hex
from src.conexion.conexion_camara_torreta import sock_tx, IP_TORRETA, PORT_ENVIO_TORRETA
from src.clases.CcittCrcXmodem import CcittCrcXmodem
import numpy as np
import struct
from env.environment import cnt_msg
def msg_velocidad(var_buffer_joystick):
    #time.sleep(0.1)
    hex_acimut = float_to_hex(var_buffer_joystick[0])       #Pasamos el valor de velocidad acimut flotante que nos llega desde fuera de la funcion 
                                                            #a la funcion float_to_hex que nos lo devuelve en formato 0x12345678
    hex_elevacion = float_to_hex(var_buffer_joystick[1])

    global cnt_msg                          # Si no se define como global da error
    
    #print(hex_acimut)
    #print(hex_elevacion)

    msg_a =    (struct.pack('B', int('0xEA', 16))+ # Preambulo
                struct.pack('B', int('0x00', 16))+  # Longitud MSB
                struct.pack('B', int('0x08', 16)))  # Longitud LSB
    
    msg_crc =  (struct.pack('B', cnt_msg)+          # Contador mensaje
                struct.pack('B', int('0x00', 16))+  # Comando 0x00 / Peticion 0x01
                struct.pack('B', int('0x00', 16))+  # Control MSB
                struct.pack('B', int('0x07', 16))+  # Control LSB | 0x 00 07 --> velocidad
                struct.pack('B', int('0x' + hex_acimut[2:4], 16))+      #nos quedamos con el byte que queremos de la velocidad de acimut/elevacion
                struct.pack('B', int('0x' + hex_acimut[4:6], 16))+      #  0x   --    --    --     --
                struct.pack('B', int('0x' + hex_acimut[6:8], 16))+      #      [2:4] [4:6] [6:8] [8:10]
                struct.pack('B', int('0x' + hex_acimut[8:10], 16))+     #           
                struct.pack('B', int('0x' + hex_elevacion[2:4], 16))+   #                
                struct.pack('B', int('0x' + hex_elevacion[4:6], 16))+   #                     
                struct.pack('B', int('0x' + hex_elevacion[6:8], 16))+
                struct.pack('B', int('0x' + hex_elevacion[8:10], 16)))

    #print(msg_crc)

    obj = CcittCrcXmodem(0x1021, 0x0000)  # El CRC se genera siguiendo el estandar CCITT-CRC16 (0x1021) 
                                            # siguiendo un valor inicial de 0x0000
        
    crc_int = obj.ccitt_crc16(msg_crc)      # El CRC se calcula desde el byte contador de mensaje (byte numero 3) 
                                            # hasta el ultimo byte de la carga de pago (byte numero 7+N)
        
    crc_bytes = obj.int2bytes(crc_int)      # Convertir CRC a tipo Byte

    bytesToSend =  (msg_a       +
                    msg_crc     +
                    crc_bytes)

    cnt_msg = np.uint8(cnt_msg +1)          # Incrementar contador de mensaje

    sock_tx.sendto(bytesToSend,(IP_TORRETA, PORT_ENVIO_TORRETA))
    #print(bytesToSend)