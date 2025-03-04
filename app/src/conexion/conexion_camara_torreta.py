# conexion_camara_torreta.py

import socket

# Recepción
IP_CAMARA = "10.100.5.4"
PORT_RECEPCION_CAMARA = 5005 # Quizás sobre

# Envío
IP_TORRETA = '192.168.100.80'
PORT_ENVIO_TORRETA = 5678  
#ipMSP25 = '192.168.100.80' #MSP25 conection PCU
#serverAddressPort = (IP_TORRETA,5678)  

# Crear socket de recepción
#sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock_rx.bind((IP_CAMARA, PORT_RECEPCION_CAMARA))

# Crear socket de envío
sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)