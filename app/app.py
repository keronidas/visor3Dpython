# app.py
from flask import Flask
from routes import setup_routes
from camera import release_camera

app = Flask(__name__)

# Configura las rutas
setup_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
