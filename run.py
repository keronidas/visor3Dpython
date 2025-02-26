import subprocess
import time
import os

# Ruta del entorno virtual
venv_path = os.path.join(os.getcwd(), 'venv', 'Scripts', 'activate')

# Abre una nueva consola para activar el entorno virtual y ejecutar Flask
flask_command = f'cmd.exe /k "{venv_path} && python app/app.py"'
subprocess.Popen(flask_command, shell=True)

# Da tiempo para que Flask se inicie antes de lanzar Electron
time.sleep(15)  # Ajusta el tiempo según sea necesario

# Abre una nueva consola para ejecutar Electron
electron_command = 'cmd.exe /k "npx electron ."'
subprocess.Popen(electron_command, shell=True)
