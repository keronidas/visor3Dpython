import numpy as np


buffer_joystick= [0,0]
cnt_msg = np.uint8(0)
deadzone1 = 512 - 50
deadzone2 = 512 + 50
eje_x_previo = 'centro'
eje_y_previo = 'centro'
init_tracker = 0
max_speed = 40
modo_automatico = False
normal = 0
program_is_running = True
record_thread = None
salida_video = None
state = normal
tracker_rgb_mode = 3