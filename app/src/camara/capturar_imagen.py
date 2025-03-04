# capturar_imagen.py

import re
import cv2
import numpy as np
import requests
from src.conexion.conexion_camara_torreta import IP_CAMARA


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
1