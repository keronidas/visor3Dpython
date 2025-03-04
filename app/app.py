from flask import Flask
from flask_cors import CORS
from src.routes.video import video_bp
from src.routes.joystick import joystick_bp

app = Flask(__name__, template_folder='src/templates')
CORS(app)

# Registrar los Blueprints
app.register_blueprint(video_bp)
app.register_blueprint(joystick_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
