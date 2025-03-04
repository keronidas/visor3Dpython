import subprocess
import time
import os

# Cerrar el puerto 5000 si está en uso
def close_port_5000():
    try:
        # Obtener los PIDs que están usando el puerto 5000
        pids = subprocess.check_output("lsof -t -i:5000", shell=True).strip().split(b'\n')
        
        # Matar cada proceso que está usando el puerto 5000
        for pid in pids:
            pid = pid.decode('utf-8')  # Decodificar el PID a string
            subprocess.run(f"kill -9 {pid}", shell=True)
            print(f"Puerto 5000 cerrado, proceso {pid} detenido")
    except subprocess.CalledProcessError:
        print("Puerto 5000 ya está libre o no se pudo encontrar un proceso utilizando el puerto.")

# Ruta del entorno virtual
venv_path = os.path.join(os.getcwd(), 'venv', 'bin', 'activate')

# Cerrar el puerto 5000 antes de iniciar Flask
close_port_5000()

# Abre una nueva consola para activar el entorno virtual y ejecutar Flask
flask_command = f'bash -c "source {venv_path} && python app/app.py"'
subprocess.Popen(flask_command, shell=True)

# Da tiempo para que Flask se inicie antes de lanzar Electron
time.sleep(5)  # Ajusta el tiempo según sea necesario

# Abre una nueva consola para ejecutar Electron
electron_command = 'bash -c "npx electron ."' 
subprocess.Popen(electron_command, shell=True)
