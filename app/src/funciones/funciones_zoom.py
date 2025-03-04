# funciones_zoom.py

from src.conexion.conexion_camara_torreta import IP_CAMARA
from src.camara.capturar_imagen import uid_number

import requests
import struct

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
    