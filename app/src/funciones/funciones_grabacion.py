# funciones_grabacion.py

### GRABACIÓN
import queue


record_queue = queue.Queue(maxsize=100)   # Cola para los frames de grabación
record_thread = None                      # Hilo que se encargará de grabar
out = None                                # VideoWriter global

def record_worker():
    global out
    while True:
        frame = record_queue.get()
        if frame is None:  # Sentinel para detener el hilo
            break
        if out is not None:
            out.write(frame)
