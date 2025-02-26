import cv2
import numpy as np
import datetime
import time
import socket
import struct 
import requests
import re
import threading
import queue
import os
import glob
#from inputs import get_gamepad
#import pylepton
import evdev
from evdev import InputDevice, categorize, ecodes


############################################################################
#                       CONEXIONES CON CÁMARA Y TORRETA                    #
############################################################################
# Recepción
IP_CAMARA = "10.100.5.4"
PORT_RECEPCION_CAMARA = 5005 # Quizás sobre

# Envío
IP_TORRETA = '192.168.100.80'
PORT_ENVIO_TORRETA = 5678  
#ipMSP25 = '192.168.100.80' #MSP25 conection PCU
#serverAddressPort = (IP_TORRETA,5678)  

# Crear socket de recepción
#sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock_rx.bind((IP_CAMARA, PORT_RECEPCION_CAMARA))

# Crear socket de envío
sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

############################################################################
#                         CONEXIÓN CON JOYSTICK                            #
############################################################################
# Define el VID y PID de tu joystick
TARGET_VID = "068e"  
TARGET_PID = "00ec"  

def find_joystick_by_id():
    input_devices = glob.glob('/sys/class/input/event*/device')
    
    for device_path in input_devices:
        try:
            with open(os.path.join(device_path, "id/vendor"), "r") as vid_file:
                vid = vid_file.read().strip()
            with open(os.path.join(device_path, "id/product"), "r") as pid_file:
                pid = pid_file.read().strip()
            
            if vid == TARGET_VID and pid == TARGET_PID:
                event_path = "/dev/input/" + os.path.basename(os.path.dirname(device_path))
                return event_path
        except FileNotFoundError:
            continue  # Si no encuentra los archivos, pasa al siguiente

    return None

device_path = find_joystick_by_id()
if device_path:
    print(f"Joystick detectado en: {device_path}")
    gamepad = evdev.InputDevice(device_path)
else:
    print("No se encontró el joystick con la ID especificada.") 

velocidad = 0               #Definimos velociad inicial 0
buffer_joystick = [0,0]     #Aqui se almacenan las velocidades de [acimut, elevacion] para pasarlas de una funcion a otra

button_mapping = {
    ecodes.BTN_TRIGGER:   'TRIGGER',
    ecodes.BTN_THUMB:     'THUMB',
    ecodes.BTN_THUMB2:    'THUMB2',
    ecodes.BTN_TOP:       'TOP',
    ecodes.BTN_TOP2:      'TOP2',
}

axis_mapping = {
    ecodes.ABS_X: 'Eje X',
    ecodes.ABS_Y: 'Eje Y',
}

eje_x_previo = 'centro'
eje_y_previo = 'centro'

############################################################################
#                             CAPTURAR IMÁGEN                              #
############################################################################
cap_rgb = cv2.VideoCapture(f'rtsp://admin:123456@{IP_CAMARA}/video1', cv2.CAP_FFMPEG)
cap_rgb.set(cv2.CAP_PROP_BUFFERSIZE, 1)


if not cap_rgb.isOpened():
    print("No se pudo iniciar la cámara")
    exit()

# URL para obtener el UID
url = f"http://{IP_CAMARA}/cgi-bin/getuid?username=admin&password=123456"

# Request GET para obtener el UID
response = requests.get(url)

# Comprobar si la respuesta es correcta
if response.status_code == 200:
    uid = response.text
    print(f"El UID de la cámara es : {uid}")
    uid_number = re.search(r'<uid>(\w+)</uid>', uid).group(1)
    print(f"El número de la UID de la cámara es : {uid_number}")
else:
    print("Error en la obtención de la UID de la cámara")

zoom_level = 0


############################################################################
#                                 CLASES                                   #
############################################################################

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


############################################################################
#                              FUNCIONES                                   #
############################################################################

### FUNCIONES DE LA CÁMARA ###
# Hacer zoom
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

############################################################################
#                             VARIABLES GLOBALES                           #
############################################################################
normal = 0
tracker_rgb_mode = 3
state = normal
modo_automatico = False
running = True

############################################################################
#                             BUCLE PRINCIPAL                              #
############################################################################
def main():

    msg_habilitar(1)
    msg_habilitar(3)
    global running
    global init_tracker
    init_tracker = 0
    #global tracker

    ############################################################################
    #                          INICIALIZACIÓN DE VARIABLES                     #
    ############################################################################

    
    t_zoom = 1
    #thermal = 2
    
    #init_tracker = 0
    #tracker_thermal_mode = 4
    capture_mode = 5
    global out, record_thread
    record = False
    out = None
    
    tracker = None

    #displacement_x = 0
    #displacement_y = 0

    roi_height = 100
    roi_width = 100
    font = cv2.FONT_HERSHEY_SIMPLEX

    prev_frame_time = 0
    new_frame_time = 0

    fps_history = []
    #thermal_fps_history = []
    window_size = 30

    start_time = 0
    timeout = 0.07
    #prev_frame_time_thermal = 0

    #frame_thermal = cap_thermal.read()

    global buffer_joystick
    buffer_joystick = [0,0]

    buffer_habilitacion = 0 # Aquí se almacena el estado de habilitacion de [acimut, elevacion] para pasarlas de una funcion a otra

    
    prev_control_time = time.time()
    
    # TRACKER

    #params = cv2.TrackerKCF.Params()
    #params.sigma = 0.5
    #params.detect_thresh = 0.5
    #tracker = cv2.TrackerKCF().create(params)

    ###tracker = cv2.TrackerBoosting_create()
    #tracker = cv2.TrackerMIL_create()
    #tracker = cv2.TrackerKCF_create()
    ###tracker = cv2.TrackerTLD_create()
    ###tracker = cv2.TrackerMedianFlow_create()
    ###tracker = cv2.TrackerGOTURN_create()
    ###tracker = cv2.TrackerMOSSE_create()
    #tracker = cv2.TrackerCSRT_create()

    #params = tracker.getParams()
    #tracker.set_detect_thresh(0.4)
    #tracker.set_sigma(0.5)

    
    while running:
        keep_alive()
        ret, frame_rgb = cap_rgb.read()
        if not ret:
            break

        '''
        if time.time() - start_time > timeout:
        ret_thermal, frame_thermal = cap_thermal.read()  
        frame_thermal = frame_thermal[:-10]
        start_time = time.time()

    
        thermal_fps = 1 / (start_time - prev_frame_time_thermal)
        prev_frame_time_thermal = start_time

        thermal_fps_history.append(thermal_fps)
        if len(thermal_fps_history) > window_size:
            thermal_fps_history.pop(0)
    
        thermal_avg_fps = np.mean(thermal_fps_history)
        else:
        print("NO HAY FRAME")    
    

        #if not ret_rgb or not ret_thermal:
        #    print("Failed to grab frame from one or both cameras")
        #    break

        # Resize thermal frame to be smaller (e.g., 1/4 of the RGB frame size)
        #thermal_width = frame_rgb.shape[1] * 6 // 10
        #thermal_height = frame_rgb.shape[0] * 6 // 10

        if True:
        frame_thermal_resized = cv2.resize(frame_thermal, (thermal_width, thermal_height))
        frame_thermal_resized_color = frame_thermal_resized.copy()

        # Convert grayscale thermal image to BGR
        cv2.normalize(frame_thermal_resized_color , frame_thermal_resized_color , 0 , 65535, cv2.NORM_MINMAX)
        np.right_shift(frame_thermal_resized_color, 8, frame_thermal_resized_color)
        frame_thermal_resized_color = cv2.cvtColor(frame_thermal_resized_color, cv2.COLOR_GRAY2BGR)
        #frame_thermal_color = cv2.convertScaleAbs(frame_thermal_color)

        # Apply color map to thermal image (optional)
        #frame_thermal_resized_color = cv2.applyColorMap(frame_thermal_resized_color, cv2.COLORMAP_JET)
    

        # Calculate the position to place the thermal image in the center
        center_y = frame_rgb.shape[0] // 2
        center_x = frame_rgb.shape[1] // 2
        top_left_y = center_y - thermal_height // 2
        top_left_x = center_x - thermal_width // 2

        # Create a ROI in the center of the RGB image
        roi = frame_rgb[top_left_y : top_left_y+thermal_height , top_left_x : top_left_x+thermal_width]

        # Blend the thermal image with the ROI
        alpha = 1
        blended_roi = cv2.addWeighted(roi, 1-alpha, frame_thermal_resized_color, alpha, 0, dtype=cv2.CV_32F)


        # Place the blended ROI back into the RGB image
        if state == thermal:
        frame_rgb[top_left_y + displacement_y :top_left_y+thermal_height + displacement_y, top_left_x + displacement_x :top_left_x+thermal_width + displacement_x] = blended_roi

        # Crear un ROI del centro de la termica
        if state == t_zoom:    
        med = 0
        roi_thermal_color = frame_thermal_resized_color[thermal_height//2 - roi_height//2 - displacement_y: thermal_height//2 + roi_height//2 - displacement_y, thermal_width//2 - roi_width//2 - displacement_x: thermal_width//2 + roi_width//2 - displacement_x ]

        # CREAR OTRO PARA CALCULOS
        roi_thermal = frame_thermal_resized[thermal_height//2 - roi_height//2 - displacement_y: thermal_height//2 + roi_height//2 - displacement_y, thermal_width//2 - roi_width//2 - displacement_x: thermal_width//2 + roi_width//2 - displacement_x ]
        for i in range(roi_width-1):
            for j in range(roi_height-1):
                med = med + roi_thermal[j, i]
    
        med = med // (roi_width * roi_height)
        #print(f"-------")
        print(roi_thermal)
        #print (len(roi_thermal))
        #print (len(roi_thermal[0]))
        #print(med)

        # Resize del ROI termico

        roi_height_resize = roi_thermal.shape[0] * 3
        roi_width_resize = roi_thermal.shape[1] * 3
        roi_thermal_resized = cv2.resize(roi_thermal_color, (roi_width_resize, roi_height_resize))

        #Colocar ROI termico en una esquina

        alpha = 1
        #blended_roi_thermal = cv2.addWeighted(roi, 1-alpha, roi_thermal_resized , alpha, 0 )#, dtype=cv2.CV_32F)
        frame_rgb[0 : roi_height_resize ,0: roi_width_resize] = roi_thermal_resized

        # Dibujar rectangulo ampliacion

        cv2.rectangle(frame_rgb,(center_x - roi_width//2, center_y - roi_height//2),(center_x + roi_width//2, center_y + roi_height//2),(0,255,0),1)
        '''

        # Centro de la imagen 
        center_y = frame_rgb.shape[0] // 2
        center_x = frame_rgb.shape[1] // 2
        #top_left_y = center_y - thermal_height // 2
        #top_left_x = center_x - thermal_width // 2

    ################################################################################################
    #                                          TRACKER RGB                                         #
    ################################################################################################
        bbox = None

        if state == tracker_rgb_mode:
            if init_tracker == 1 :
                init_tracker = 2
            
                '''
                params = cv2.TrackerKCF.Params()
                params.sigma = 0.3
                params.output_sigma_factor = 0.10
                params.detect_thresh = 0.5
                params.interp_factor = 0.10
                params.pca_learning_rate = 0.2
                tracker = cv2.TrackerKCF().create(params)
                '''
                #params = cv2.TrackerMOSSE.Params()
                #tracker = cv2.TrackerKCF().create(params)

                tracker = cv2.TrackerCSRT_create()
   
                bbox = (center_x - roi_width//2 , center_y - roi_height//2 , roi_width , roi_height)
                tracker.init(frame_rgb, bbox)


            elif init_tracker == 2 :

                ok, bbox = tracker.update(frame_rgb)

                frame_no_overlay = frame_rgb.copy()  # Copia del frame

                # Parámetros para la ampliación
                zoom_width = 150  # Ancho de la región que quieres ampliar
                zoom_height = 150  # Alto de la región que quieres ampliar
                zoom_scale = 3  # Factor de ampliación
                zoom_x = 0  # Posición horizontal (negativo para mover a la izquierda)
                zoom_y = 0   # Posición vertical (positivo para bajar)

                # DIBUJAR CUADRO TRACKER
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame_rgb, p1, p2, (255,0,0), 2, 1)

                # CREAR UN ZOOM DEL TRACKER
                center_tracker_x = int(bbox[0] + bbox[2] // 2)
                center_tracker_y = int(bbox[1] + bbox[3] // 2)

                # Calcular los límites del recorte
                x1 = max(0, center_tracker_x - zoom_width // 2)
                y1 = max(0, center_tracker_y - zoom_height // 2)
                x2 = min(frame_rgb.shape[1], center_tracker_x + zoom_width // 2)
                y2 = min(frame_rgb.shape[0], center_tracker_y + zoom_height // 2)

                # Extraer el ROI centrado en el tracker
                roi_zoom = frame_no_overlay[y1:y2, x1:x2]

                # Ampliar la imagen del ROI
                zoom_resized = cv2.resize(roi_zoom, (zoom_width * zoom_scale, zoom_height * zoom_scale), interpolation=cv2.INTER_CUBIC)

                # Colocar el zoom en la esquina superior derecha
                pos_x = frame_rgb.shape[1] - zoom_resized.shape[1] + zoom_x  # Ajustar horizontalmente
                pos_y = zoom_y  # Ajustar verticalmente

                # Dibujar el zoom en la imagen principal
                frame_rgb[pos_y:pos_y + zoom_resized.shape[0], pos_x:pos_x + zoom_resized.shape[1]] = zoom_resized

                # Dibujar el marco del zoom
                cv2.rectangle(frame_rgb, (pos_x, pos_y), (pos_x + zoom_resized.shape[1], pos_y + zoom_resized.shape[0]), (0, 0, 255), 2)

                # Texto para indicar el zoom
                #cv2.putText(frame_rgb, "Zoom", (pos_x, pos_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


            # DIBUJAR CUADRO FIJO
            p1_fix = (center_x - roi_width//2 , center_y - roi_height//2)
            p2_fix = (center_x - roi_width//2 + roi_width, center_y - roi_height//2 + roi_height)
            cv2.rectangle(frame_rgb, p1_fix, p2_fix, (0,255,0), 2, 1)

            # DIFERENCIA ENTRE CENTRO DE IMAGEN Y TRACKER
            if bbox is not None:
                # Centro del tracker
                center_bbox_x = bbox[0] + bbox[2] // 2
                center_bbox_y = bbox[1] + bbox[3] // 2

                # Centro de la imagen
                center_roi_x = center_x
                center_roi_y = center_y

                # Diferencias entre los centros
                dx = center_bbox_x - center_roi_x
                dy = center_bbox_y - center_roi_y

                if abs(dx) < 80:
                    dx = 0
                if abs(dy) < 40:
                   dy = 0

            
                # Control automático
                if modo_automatico == True:
                    # Diferencia de áreas para hacer zoom
                    area_tracker = bbox[2] * bbox[3]
                    area_roi = roi_width * roi_height
                    
                    threshold_area = 0.05 * area_roi
                    diff_area = area_tracker - area_roi
                    print(diff_area)
                    print(dx,dy)
                    # Comparar áreas y ajustar zoom
                    '''
                    if diff_area < -threshold_area:
                        # El tracker es más pequeño; se necesita hacer zoom in
                        zoom_in()
                    elif diff_area > threshold_area:
                        # El tracker es más grande; se necesita hacer zoom out
                        zoom_out()
                    else:
                        # Si la diferencia es pequeña, detener el zoom
                        ptz_stop()
                    '''

                    control(dx,dy)
                    
                    
    
    ################################################################################################
    #                                          TRACKER TÉRMICO                                     # 
    ################################################################################################
        '''
        if state == tracker_thermal_mode:

            frame_thermal_resized_color = cv2.resize(frame_thermal_resized_color, (frame_rgb.shape[1], frame_rgb.shape[0]))
            frame_rgb[:,:] = frame_thermal_resized_color
 

        if init_tracker == 1 :

            init_tracker = 2
            #del tracker
            
            
            params = cv2.TrackerKCF.Params()
            params.sigma = 0.3
            params.output_sigma_factor = 0.10
            params.detect_thresh = 0.5
            params.interp_factor = 0.10
            params.pca_learning_rate = 0.2
            tracker = cv2.TrackerKCF().create(params)
            
            params = cv2.TrackerCSRT.Params()
            tracker = cv2.TrackerCSRT().create(params)

   
            bbox = (center_x - roi_width//2 , center_y - roi_height//2 , roi_width , roi_height)
            tracker.init(frame_rgb, bbox)

        elif init_tracker == 2 :

            print(bbox)
            ok, bbox = tracker.update(frame_rgb)
            print(bbox)

            # DIBUJAR CUADRO
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame_rgb, p1, p2, (255,0,0), 2, 1)

        # DIBUJAR CUADRO FIJO
        p1_fix = (center_x - roi_width//2 , center_y - roi_height//2)
        p2_fix = (center_x - roi_width//2 + roi_width, center_y - roi_height//2 + roi_height)
        cv2.rectangle(frame_rgb, p1_fix, p2_fix, (0,255,0), 2, 1)
 
        '''
   
        # Ajustar a pantalla
        #frame_rgb = cv2.resize(frame_rgb,(1920,1080))


    ######################################################################################
    #                               INTERFAZ DE USUARIO                                  #
    ######################################################################################

        if state == normal:
            cv2.putText(frame_rgb,'DAY CAM', (10,970), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #if state == thermal:
        #   cv2.putText(frame_rgb,'THERMAL', (10,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #if state == t_zoom:
        #   cv2.putText(frame_rgb,'THERMAL MEASURE', (10,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #   cv2.putText(frame_rgb, str(med / 100 -273.15), (900,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if state == tracker_rgb_mode:
            cv2.putText(frame_rgb,'TRACKER', (10,970), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #if state == tracker_thermal_mode:
         #   cv2.putText(frame_rgb,'THERMAL TRACKER', (10,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if modo_automatico == True:
            cv2.putText(frame_rgb,'AUTOMATIC MODE', (10,920), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if modo_automatico == False:
            cv2.putText(frame_rgb,'MANUAL MODE', (10,920), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if record == True:
            cv2.putText(frame_rgb, 'PRESS F TO STOP RECORDING', (30, 30),font, 1, (0, 255, 0), 2, cv2.LINE_AA)

        new_frame_time = time.time()
    
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time

    
        fps_history.append(fps)
        if len(fps_history) > window_size:
            fps_history.pop(0)
    
        avg_fps = np.mean(fps_history)

        cv2.putText(frame_rgb, f"FPS: {round(avg_fps, 2)}", (10, 60), font, 1, (0, 255, 0), 2)

        #cv2.putText(frame_rgb, f"FPS: {round(thermal_avg_fps, 2)}", (10, 90), font, 1, (0, 255, 0), 2)

    #######################################################################################
    #                                       GRABAR                                        #
    #######################################################################################

        #if state == capture_mode:
        if record:
            if out is None:
                # Inicializar el VideoWriter al iniciar la grabación
                current_time = datetime.datetime.now()
                timestamp = current_time.strftime("%H-%M-%S_%d-%m-%Y")
                # Aquí eliges el códec y formato que prefieras, por ejemplo:
                out = cv2.VideoWriter(f"record_{timestamp}.avi",
                                      cv2.VideoWriter_fourcc(*'DIVX'),
                                      25, (1920, 1088))
                # Iniciar el hilo de grabación
                record_thread = threading.Thread(target=record_worker, daemon=True)
                record_thread.start()

            # Encolar el frame actual para que el hilo lo escriba
            try:
                record_queue.put_nowait(frame_rgb)
            except queue.Full:
                # Si la cola está llena, se descarta el frame para mantener el FPS
                pass

            #cv2.putText(frame_rgb, 'PRESS F TO STOP RECORDING', (30, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame_rgb, 'PRESS R TO START RECORDING', (30, 30),
                        font, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # ... (resto de la visualización, procesamiento de FPS, etc.)

        cv2.imshow("INTERFACE", frame_rgb) 

    ########################################################################################
    #                                      PANEL DE MANDO                                  #
    ########################################################################################
        
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            running = False
        elif key == ord('r'):
            record = True
        elif key == ord('f'):
            record = False
            if out is not None:
                # Enviar valor centinela para detener el hilo
                record_queue.put(None)
                record_thread.join()
                out.release()
                out = None
                # Vaciar la cola para la siguiente grabación
                with record_queue.mutex:
                    record_queue.queue.clear()
        
        current_time = time.time()
  
    cap_rgb.release()
    #cap_thermal.release()
    cv2.destroyAllWindows()
    os._exit(0)

thread_main = threading.Thread(target=main)
thread_main.start()

deadzone1 = 512 - 50
deadzone2 = 512 + 50
max_speed = 40

########################################################################################
#                                      PANEL DE MANDO                                  #
########################################################################################
for event in gamepad.read_loop():
    if event.type == ecodes.EV_ABS:   #EV_ABS es el tipo de entrada, joystick
        if event.code in axis_mapping:
            if axis_mapping[event.code] == 'Eje X':
                if event.value <= deadzone1 :
                        print(f"Izquierda")
                        eje_x_previo = 'izquierda'          #establecemos un eje previo para que solo mande mensaje cuando haya un cambio
                        velocidad = map_range( event.value, 0, deadzone1 , max_speed , 0)
                        buffer_joystick[0]= -velocidad       #ya que estamos en el eje x modificamos el componente acimut 
                        msg_velocidad(buffer_joystick)
                elif (deadzone1 < event.value <= deadzone2):

                        print(f"Centro X")
                        eje_x_previo = 'centro'
                        buffer_joystick[0]= 0
                        msg_velocidad(buffer_joystick)
                elif event.value > deadzone2:

                        print(f"Derecha")                   
                        eje_x_previo = 'derecha'
                        velocidad = map_range( event.value, deadzone2, 1023, 0, max_speed )            
                        buffer_joystick[0] = velocidad     #velocidad negativa   
                        msg_velocidad(buffer_joystick)
            
            elif axis_mapping[event.code] == 'Eje Y':
                if event.value > deadzone2:

                        print(f"Abajo")
                        eje_y_previo = 'abajo'
                        velocidad = map_range( event.value, deadzone2, 1023, 0, max_speed )
                        buffer_joystick[1] = -velocidad
                        msg_velocidad(buffer_joystick)
                elif deadzone1 < event.value <=deadzone2:

                        print(f"Centro Y")
                        eje_y_previo = 'centro' 
                        buffer_joystick[1]= 0
                        msg_velocidad(buffer_joystick)
                elif event.value <= deadzone1 :

                        print(f"Arriba")
                        velocidad = map_range( event.value, 0, deadzone1 , max_speed , 0)
                        eje_y_previo = 'arriba'
                        buffer_joystick[1] = velocidad
                        msg_velocidad(buffer_joystick)        
    
    ### LECTURA DE BOTONES ###

    elif event.type == ecodes.EV_KEY:   #EV_KEY es el tipo de entrada, boton
        if event.code in button_mapping:
            button_name = button_mapping[event.code]
            print(f"{button_name}: {event.value}")
            
            # CAMBIO DE ESTADOS
            if button_mapping[event.code] == 'THUMB':
                if (event.value == 1) & (state == normal):
                    state = tracker_rgb_mode
                elif (event.value == 1) & (state == tracker_rgb_mode):
                    state = normal

            # MODO MANUAL / AUTOMÁTICO
            if button_mapping[event.code] == 'TOP':
                if (event.value == 1) & (modo_automatico == False):
                    modo_automatico = True
                    pid_azimut.reset_integral()
                    pid_elevacion.reset_integral()

                elif (event.value == 1) & (modo_automatico == True):
                    buffer_joystick[0] = 0
                    buffer_joystick[1] = 0
                    msg_velocidad(buffer_joystick)
                    ptz_stop() 
                    modo_automatico = False 

            # ZOOM IN / ZOOM OUT
            if button_mapping[event.code] == 'THUMB2':
                if event.value == 1:
                    zoom_in()
                elif event.value == 0:
                    ptz_stop()

            if button_mapping[event.code] == 'TOP2':
                if event.value == 1:
                    zoom_out()
                elif event.value == 0:
                    ptz_stop()

            # INICIAR EL TRACKER
            if button_mapping[event.code] == 'TRIGGER':
                if (event.value == 1) & (init_tracker == 0):
                    init_tracker = 1
                elif (event.value == 1) & (init_tracker == 2):
                    init_tracker = 0







