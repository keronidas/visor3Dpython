import re
import cv2
import numpy as np
import requests
import os
from datetime import datetime
from conexion.conexion_camara_torreta import IP_CAMARA

def obtener_uid():
    url = f"http://{IP_CAMARA}/cgi-bin/getuid?username=admin&password=123456"
    response = requests.get(url)

    if response.status_code == 200:
        uid = response.text
        match = re.search(r'<uid>(\w+)</uid>', uid)
        return match.group(1) if match else None
    return None

def capturar_imagen():
    cap = cv2.VideoCapture(f'rtsp://admin:123456@{IP_CAMARA}/video1', cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        return None

    ret, frame = cap.read()
    cap.release()

    if ret:
        filename = f"static/captured_images/captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, frame)
        return filename
    return None
