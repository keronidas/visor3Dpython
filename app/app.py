from flask import Flask
from routes.routes import setup_routes

app = Flask(__name__)
setup_routes(app)

def main():
    app.run(debug=True)

if __name__ == "__main__":
    main()
