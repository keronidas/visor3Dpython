# functions.py

# Hacer zoom
import queue
from conexion.conexion_camara_torreta import IP_CAMARA, sock_tx, IP_TORRETA, PORT_ENVIO_TORRETA
from camara.capturar_imagen import uid_number
from clases.clases import PID, ccitt_crc_xmodem
from conexion.conexion_joystick import *

import requests
import numpy as np
import struct


def zoom_in():
    url = f"http://{IP_CAMARA}/cgi-bin/ptz_ctrl?zoom=1&uid={uid_number}"
    requests.get(url)

# Deshacer zoom
def zoom_out():
    url = f"http://{IP_CAMARA}/cgi-bin/ptz_ctrl?zoom=-1&uid={uid_number}"
    requests.get(url)

# Función para mantener la conexión con la cámara
def keep_alive():
    url = f"http://{IP_CAMARA}/cgi-bin/keep_alive?uid={uid_number}"
    requests.get(url)

# Función stop
def ptz_stop():
    url = f"http://{IP_CAMARA}/cgi-bin/ptz_ctrl?stop=1&uid={uid_number}"
    requests.get(url)


def float_to_hex(f):
    return'0x' + format(struct.unpack('<I', struct.pack('<f', float(f)))[0], '08x') #Se ha probado tambien con hex(), zfill(8) pero no funciona bien cuando el valor es 0
    
### FUNCIÓN DE VELOCIDAD ### 

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

    obj = ccitt_crc_xmodem(0x1021, 0x0000)  # El CRC se genera siguiendo el estandar CCITT-CRC16 (0x1021) 
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

### FUNCIÓN DE HABILITACION MOVIMIENTOS ### 
cnt_msg = np.uint8(0)

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

    obj = ccitt_crc_xmodem(0x1021, 0x0000)  # El CRC se genera siguiendo el estandar CCITT-CRC16 (0x1021) 
                                            # siguiendo un valor inicial de 0x0000
        
    crc_int = obj.ccitt_crc16(msg_crc)      # El CRC se calcula desde el byte contador de mensaje (byte número 3) 
                                            # hasta el ultimo byte de la carga de pago (byte numero 7+N)
        
    crc_bytes = obj.int2bytes(crc_int)      # Convertir CRC a tipo Byte

    bytesToSend =  (msg_a       +
                    msg_crc     +
                    crc_bytes)

    cnt_msg = np.uint8(cnt_msg +1)          # Incrementar contador de mensaje

    sock_tx.sendto(bytesToSend,(IP_TORRETA, PORT_ENVIO_TORRETA))

### FUNCIÓN DE CONTROL AUTOMÁTICO ###

pid_azimut = PID(Kp=0.05, Ki=0.000, Kd=0.7)
pid_elevacion = PID(Kp=0.025, Ki=0.000, Kd=0.55) # Subir algo

alpha_filter_x = 0.1
alpha_filter_y = 0.07

prev_vel_azimut = 0
prev_vel_elevacion = 0

new_vel_azimut = 0
new_vel_elevacion = 0

vel_azimut = 0
new_vel_elevacion = 0

def control(dx,dy):
    global buffer_joystick
    #buffer_joystick = [0,0]
    global vel_azimut
    global vel_elevacion
    global prev_vel_azimut
    global prev_vel_elevacion
    global new_vel_azimut
    global new_vel_elevacion

    vel_azimut = pid_azimut.compute(dx)
    vel_elevacion = pid_elevacion.compute(-dy) 

    # Limitar la velocidad
    if vel_azimut < -85:
        vel_azimut = -85  
    if vel_azimut > 85:
        vel_azimut = 85 
    if vel_elevacion < -85:
        vel_elevacion = -85 
    if vel_elevacion > 85:
        vel_elevacion = 85 


    new_vel_azimut = alpha_filter_x * vel_azimut + (1 - alpha_filter_x) * prev_vel_azimut

    new_vel_elevacion = alpha_filter_y * vel_elevacion + (1 - alpha_filter_y) * prev_vel_elevacion

    prev_vel_azimut = new_vel_azimut
    prev_vel_elevacion = new_vel_elevacion

    buffer_joystick[0] = new_vel_azimut
    buffer_joystick[1] = new_vel_elevacion

    msg_velocidad(buffer_joystick)  
    print(f'Vel. azimut: {new_vel_azimut}, Vel. elevación: {new_vel_elevacion}')    

def map_range(value, in_min, in_max, out_min, out_max, exponent=1.5):
    """
    Maps a value from one range to another, applying an exponential transformation.

    Args:
        value: The input value to map.
        in_min: The minimum value of the input range.
        in_max: The maximum value of the input range.
        out_min: The minimum value of the output range.
        out_max: The maximum value of the output range.
        exponent: The exponent to apply to the normalized input value.  exponent > 1 
                  will skew the mapping towards the out_min, while exponent < 1 will skew towards the out_max.  
                  exponent=1 results in a linear mapping.

    Returns:
        The mapped value in the output range, with the exponential transformation applied.
    """
    # Ensure the input range is valid
    if in_min >= in_max:
        raise ValueError("in_min must be less than in_max")

    # Normalize the input value to the range [0, 1]
    normalized_value = (value - in_min) / (in_max - in_min)

    # Apply the exponential transformation
    exponential_value = np.power(normalized_value, exponent)

    # Map the transformed value to the output range
    mapped_value = exponential_value * (out_max - out_min) + out_min

    return mapped_value

### GRABACIÓN
record_queue = queue.Queue(maxsize=100)   # Cola para los frames de grabación
record_thread = None                      # Hilo que se encargará de grabar
out = None                                # VideoWriter global

def record_worker():
    global out
    while True:
        frame = record_queue.get()
        if frame is None:  # Sentinel para detener el hilo
            break
        if out is not None:
            out.write(frame)

############################################################################
############################################################################
'''                                       #
# RGB camera pipeline
pipeline_rgb = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM),width=1280,height=720,format=NV12,framerate=60/1 ! "
    "nvvidconv ! "
    "video/x-raw,width=1280,height=720,format=BGRx ! "
    "videoconvert ! "
    "video/x-raw,format=BGR ! "
    "appsink drop=1"
)

# Thermal camera pipeline
pipeline_thermal = (
    "v4l2src device=/dev/video1 ! "
    "video/x-raw,format=GRAY16_LE ! "
    "videoscale ! "
    "video/x-raw,width=640,height=480 ! "
    #"videoconvert ! "
    "appsink drop=1"
)

# Open both cameras
cap_rgb = cv2.VideoCapture(pipeline_rgb, cv2.CAP_GSTREAMER)
cap_thermal = cv2.VideoCapture(pipeline_thermal, cv2.CAP_GSTREAMER)

if not cap_rgb.isOpened() or not cap_thermal.isOpened():
    print("Failed to open one or both cameras.")
    exit()
'''
