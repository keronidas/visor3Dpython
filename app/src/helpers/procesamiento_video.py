from src.conexion.conexion_camara_torreta import IP_CAMARA
from src.conexion.conexion_joystick import *
from env.environment import *
from src.funciones import *
import cv2
import datetime
import os
import queue
import threading
import time


def generar_frames():
    global program_is_running,init_tracker,state,tracker_rgb_mode
    global normal, modo_automatico,  cnt_msg
    global  record_thread, salida_video, buffer_joystick, deadzone1
    global deadzone2, max_speed, eje_x_previo, eje_y_previo
    msg_habilitar(1)
    msg_habilitar(3)
    init_tracker=0
    record = False
    tracker = None
    roi_height = 100
    roi_width = 100
    font = cv2.FONT_HERSHEY_SIMPLEX
    prev_frame_time = 0
    new_frame_time = 0
    fps_history = []
    window_size = 30
    os.environ['OPENCV_LOG_LEVEL']='OFF'


    cap = cv2.VideoCapture(f'rtsp://admin:123456@{IP_CAMARA}/video1', cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    while True:
      
        success, frame = cap.read()
        
        if not success:
            break

       
        center_y = frame.shape[0] // 2
        center_x = frame.shape[1] // 2
        bbox = None
        if state == tracker_rgb_mode:
            if init_tracker == 1 :
                init_tracker = 2
 
        
                tracker = cv2.TrackerCSRT_create()
                bbox = (center_x - roi_width//2 , center_y - roi_height//2 , roi_width , roi_height)
                tracker.init(frame, bbox)


            elif init_tracker == 2 :
                print("llego3")
                ok, bbox = tracker.update(frame)

                frame_no_overlay = frame.copy()  # Copia del frame

                # Parámetros para la ampliación
                zoom_width = 150  # Ancho de la región que quieres ampliar
                zoom_height = 150  # Alto de la región que quieres ampliar
                zoom_scale = 3  # Factor de ampliación
                zoom_x = 0  # Posición horizontal (negativo para mover a la izquierda)
                zoom_y = 0   # Posición vertical (positivo para bajar)

                # DIBUJAR CUADRO TRACKER
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)

                # CREAR UN ZOOM DEL TRACKER
                center_tracker_x = int(bbox[0] + bbox[2] // 2)
                center_tracker_y = int(bbox[1] + bbox[3] // 2)

                # Calcular los límites del recorte
                x1 = max(0, center_tracker_x - zoom_width // 2)
                y1 = max(0, center_tracker_y - zoom_height // 2)
                x2 = min(frame.shape[1], center_tracker_x + zoom_width // 2)
                y2 = min(frame.shape[0], center_tracker_y + zoom_height // 2)

                # Extraer el ROI centrado en el tracker
                roi_zoom = frame_no_overlay[y1:y2, x1:x2]

                # Ampliar la imagen del ROI
                zoom_resized = cv2.resize(roi_zoom, (zoom_width * zoom_scale, zoom_height * zoom_scale), interpolation=cv2.INTER_CUBIC)

                # Colocar el zoom en la esquina superior derecha
                pos_x = frame.shape[1] - zoom_resized.shape[1] + zoom_x  # Ajustar horizontalmente
                pos_y = zoom_y  # Ajustar verticalmente

                # Dibujar el zoom en la imagen principal
                frame[pos_y:pos_y + zoom_resized.shape[0], pos_x:pos_x + zoom_resized.shape[1]] = zoom_resized

                # Dibujar el marco del zoom
                cv2.rectangle(frame, (pos_x, pos_y), (pos_x + zoom_resized.shape[1], pos_y + zoom_resized.shape[0]), (0, 0, 255), 2)

                # Texto para indicar el zoom
                #cv2.putText(frame, "Zoom", (pos_x, pos_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


            # DIBUJAR CUADRO FIJO
            p1_fix = (center_x - roi_width//2 , center_y - roi_height//2)
            p2_fix = (center_x - roi_width//2 + roi_width, center_y - roi_height//2 + roi_height)
            cv2.rectangle(frame, p1_fix, p2_fix, (0,255,0), 2, 1)

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
        frame = cv2.resize(frame,(1920,1080))

        if state == normal:
            cv2.putText(frame,'DAY CAM', (10,970), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #if state == thermal:
        #   cv2.putText(frame,'THERMAL', (10,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #if state == t_zoom:
        #   cv2.putText(frame,'THERMAL MEASURE', (10,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #   cv2.putText(frame, str(med / 100 -273.15), (900,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if state == tracker_rgb_mode:
            cv2.putText(frame,'TRACKER', (10,970), font, 2, (0,255,0), 2, cv2.LINE_AA)
        #if state == tracker_thermal_mode:
         #   cv2.putText(frame,'THERMAL TRACKER', (10,700), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if modo_automatico == True:
            cv2.putText(frame,'AUTOMATIC MODE', (10,920), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if modo_automatico == False:
            cv2.putText(frame,'MANUAL MODE', (10,920), font, 2, (0,255,0), 2, cv2.LINE_AA)
        if record == True:
            cv2.putText(frame, 'PRESS F TO STOP RECORDING', (30, 30),font, 1, (0, 255, 0), 2, cv2.LINE_AA)

        new_frame_time = time.time()
    
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time

    
        fps_history.append(fps)
        if len(fps_history) > window_size:
            fps_history.pop(0)
    
        avg_fps = np.mean(fps_history)

        cv2.putText(frame, f"FPS: {round(avg_fps, 2)}", (10, 60), font, 1, (0, 255, 0), 2)

        #cv2.putText(frame, f"FPS: {round(thermal_avg_fps, 2)}", (10, 90), font, 1, (0, 255, 0), 2)
        

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
                record_queue.put_nowait(frame)
            except queue.Full:
                # Si la cola está llena, se descarta el frame para mantener el FPS
                pass

            #cv2.putText(frame, 'PRESS F TO STOP RECORDING', (30, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, 'PRESS R TO START RECORDING', (30, 30),
                        font, 1, (0, 255, 0), 2, cv2.LINE_AA)
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
            





        # Codificar la imagen en formato JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        # Retornar el frame en formato multipart/x-mixed-replace
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

