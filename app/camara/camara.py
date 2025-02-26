import cv2
import atexit
import time

# Cargar el clasificador en cascada para detección de caras
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Inicializar la cámara
cap = cv2.VideoCapture(0)

def release_camera():
    """Libera la cámara al cerrar la aplicación."""
    if cap.isOpened():
        cap.release()

atexit.register(release_camera)  # Asegura que se libere al cerrar

def change_camera(camera_id):
    """Cambia la cámara por la seleccionada"""
    global cap
    cap.release()  # Liberar la cámara actual
    time.sleep(1)  # Espera un segundo para asegurar que se libere la cámara correctamente
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)  # Selecciona la cámara por id y usa DirectShow en Windows
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir la cámara {camera_id}")

def gen_frames(camera_id=0):
    """Genera frames de la cámara en formato MJPEG con detección de caras."""
    change_camera(camera_id)  # Cambiar la cámara antes de generar los frames

    while True:
        success, frame = cap.read()
        if not success:
            continue  # En lugar de romper, seguimos intentando

        # Convertir la imagen a escala de grises para mejorar el rendimiento
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detectar caras en la imagen
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        # Dibujar rectángulos alrededor de las caras detectadas
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Codificar la imagen en formato JPG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
 
