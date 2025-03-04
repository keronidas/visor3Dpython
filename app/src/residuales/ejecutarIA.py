import datetime
import os
import queue
import threading
import time
import cv2
from funciones import map_range, msg_velocidad, ptz_stop, zoom_in
from camara.capturar_imagen import cap_rgb
from evdev import ecodes
from env.environment import *
from funciones import *
from conexion.conexion_joystick import *
from helpers.iniciar_panel_mando import iniciar_panel_mando

def ejecutarIA():
    global program_is_running,init_tracker,state,tracker_rgb_mode
    global normal, tracker_rgb_mode, state, modo_automatico, program_is_running, cnt_msg
    global init_tracker, record_thread, salida_video, buffer_joystick, deadzone1
    global deadzone2, max_speed, eje_x_previo, eje_y_previo
    msg_habilitar(1)
    msg_habilitar(3)
    init_tracker=0

    ############################################################################
    #                          INICIALIZACIÓN DE VARIABLES                     #
    ############################################################################

    
    t_zoom = 1
    #thermal = 2
    
    #init_tracker = 0
    #tracker_thermal_mode = 4
    capture_mode = 5
    record = False
    
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



    
    while program_is_running:
        keep_alive()
        ret, frame_rgb = cap_rgb.read()
        if not ret:
            break



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
 
        
                tracker = cv2.TrackerCSRT_create()
                bbox = (center_x - roi_width//2 , center_y - roi_height//2 , roi_width , roi_height)
                tracker.init(frame_rgb, bbox)


            elif init_tracker == 2 :
                print("llego3")
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
        

                    control(dx,dy)
                    
                    
    
 
   
        # Ajustar a pantalla
        frame_rgb = cv2.resize(frame_rgb,(1920,1080))


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
            if salida_video is None:
                # Inicializar el VideoWriter al iniciar la grabación
                current_time = datetime.datetime.now()
                timestamp = current_time.strftime("%H-%M-%S_%d-%m-%Y")
                # Aquí eliges el códec y formato que prefieras, por ejemplo:
                salida_video = cv2.VideoWriter(f"record_{timestamp}.avi",
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
            program_is_running = False
        elif key == ord('r'):
            record = True
        elif key == ord('f'):
            record = False
            if salida_video is not None:
                # Enviar valor centinela para detener el hilo
                record_queue.put(None)
                record_thread.join()
                salida_video.release()
                salida_video = None
                # Vaciar la cola para la siguiente grabación
                with record_queue.mutex:
                    record_queue.queue.clear()
        
        current_time = time.time()
    
  
    cap_rgb.release()
    #cap_thermal.release()
    cv2.destroyAllWindows()
    os._exit(0)
thread_main = threading.Thread(target=ejecutarIA)
thread_main.start()


def gamepad_loop():
    global eje_x_previo, eje_y_previo, buffer_joystick
    while True:
        
        for event in gamepad.read_loop():
            if event.ev_type == 3:  # EV_ABS
                if event.ev_code in axis_mapping:
                    if axis_mapping[event.ev_code] == 'Eje X':
                        if event.ev_value <= deadzone1:
                            if eje_x_previo != 'izquierda':
                                print(f"Izquierda")
                                eje_x_previo = 'izquierda'
                                velocidad = map_range(event.ev_value, 0, deadzone1, max_speed, 0)
                                buffer_joystick[0] = -velocidad
                                msg_velocidad(buffer_joystick)
                        elif (deadzone1 < event.ev_value <= deadzone2):
                            if eje_x_previo != 'centro':
                                print(f"Centro X")
                                eje_x_previo = 'centro'
                                buffer_joystick[0] = 0
                                msg_velocidad(buffer_joystick)
                        elif event.ev_value > deadzone2:
                            if eje_x_previo != 'derecha':
                                print(f"Derecha")
                                eje_x_previo = 'derecha'
                                velocidad = map_range(event.ev_value, deadzone2, 1023, 0, max_speed)
                                buffer_joystick[0] = velocidad
                                msg_velocidad(buffer_joystick)

                    elif axis_mapping[event.ev_code] == 'Eje Y':
                        if event.ev_value > deadzone2:
                            if eje_y_previo != 'abajo':
                                print(f"Abajo")
                                eje_y_previo = 'abajo'
                                velocidad = map_range(event.ev_value, deadzone2, 1023, 0, max_speed)
                                buffer_joystick[1] = -velocidad
                                msg_velocidad(buffer_joystick)
                        elif deadzone1 < event.ev_value <= deadzone2:
                            if eje_y_previo != 'centro':
                                print(f"Centro Y")
                                eje_y_previo = 'centro'
                                buffer_joystick[1] = 0
                                msg_velocidad(buffer_joystick)
                        elif event.ev_value <= deadzone1:
                            if eje_y_previo != 'arriba':
                                print(f"Arriba")
                                eje_y_previo = 'arriba'
                                velocidad = map_range(event.ev_value, 0, deadzone1, max_speed, 0)
                                buffer_joystick[1] = velocidad
                                msg_velocidad(buffer_joystick)

            # Lectura de botones
            elif event.ev_type == 1:  # EV_KEY
                if event.ev_code in button_mapping:
                    button_name = button_mapping[event.ev_code]
                    print(f"{button_name}: {event.ev_value}")
                    # Lógica de cambio de estado y control
                    if button_name == 'THUMB' and event.ev_value == 1:
                        print("Estado cambiado.")
                    # Puedes seguir añadiendo los demás botones aquí

        time.sleep(0.1)  # Para no sobrecargar el CPU

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
                        print(tracker_rgb_mode)
                        print(state)
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
