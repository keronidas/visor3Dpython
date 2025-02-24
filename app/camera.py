# camera.py
import cv2
import atexit

# Cargar el clasificador en cascada para detección de caras
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Inicializar la cámara
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara.")

def release_camera():
    """Libera la cámara al cerrar la aplicación."""
    if cap.isOpened():
        cap.release()

atexit.register(release_camera)  # Asegura que se libere al cerrar

def gen_frames():
    """Genera frames de la cámara en formato MJPEG con detección de caras."""
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
