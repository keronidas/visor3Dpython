from flask import jsonify, request


def update_joystick():
    # Obtener los datos enviados desde el cliente
    data = request.get_json()

    x = data.get('x')
    y = data.get('y')
    buttons = data.get('buttons')

    # Puedes procesar los datos como desees aquí
    print(f"Joystick - Eje X: {x}, Eje Y: {y}, Botones: {buttons}")

    # Responder con un mensaje de éxito
    return jsonify({'status': 'Datos recibidos correctamente'})