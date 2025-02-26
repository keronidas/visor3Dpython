from flask import render_template, Response
from camara.camara import gen_frames

def setup_routes(app):
    @app.route("/")
    def menu():
        return render_template("menu.html")

    @app.route("/camara_1")
    def camara_1():
        return render_template("camara_1.html")

    @app.route("/camara_2")
    def camara_2():
        return render_template("camara_2.html")

    @app.route("/video_feed/<int:camera_id>")
    def video_feed(camera_id):
        return Response(gen_frames(camera_id), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route("/info")
    def info():
        return render_template("info.html")
