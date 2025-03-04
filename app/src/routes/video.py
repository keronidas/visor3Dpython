from flask import Blueprint, Response, render_template

from src.helpers.procesamiento_video import generar_frames

video_bp = Blueprint('video', __name__)

@video_bp.route('/')
def index():
    return render_template('index.html')

@video_bp.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
