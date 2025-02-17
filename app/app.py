from flask import Flask, render_template

app = Flask(__name__)

# Ruta principal que muestra el menú
@app.route("/")
def menu():
    return render_template("menu.html")

# Ruta para la cámara
@app.route("/camara")
def camara():
    return render_template("camara.html")

# Ruta para la información
@app.route("/info")
def info():
    return render_template("info.html")

if __name__ == "__main__":
    app.run(debug=True)
