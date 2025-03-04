# funciones_control_automatico.py

from src.funciones.funciones_velocidad import msg_velocidad
from src.clases.ControladorPID import ControladorPID
import numpy as np


pid_azimut = ControladorPID(Kp=0.05, Ki=0.000, Kd=0.7)
pid_elevacion = ControladorPID(Kp=0.025, Ki=0.000, Kd=0.55) # Subir algo

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
    buffer_joystick = [0,0]
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