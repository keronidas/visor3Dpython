# routes.py
from flask import render_template, Response
from camera import gen_frames

def setup_routes(app):
    @app.route("/")
    def menu():
        return render_template("menu.html")

    @app.route("/camara")
    def camara():
        return render_template("camara.html")

    @app.route("/video_feed")
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route("/info")
    def info():
        return render_template("info.html")
