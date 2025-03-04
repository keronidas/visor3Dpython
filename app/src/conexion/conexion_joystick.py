# conexion_joystick.py
import os
import glob
import evdev
from evdev import ecodes

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

