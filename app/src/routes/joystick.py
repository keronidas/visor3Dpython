from flask import Blueprint, request, jsonify

joystick_bp = Blueprint('joystick', __name__)

@joystick_bp.route('/update-joystick', methods=['POST'])
def update_joystick():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    buttons = data.get('buttons')
    if x != 0 or y != 0:
        print(f"Joystick - Eje X: {x}, Eje Y: {y}, Botones: {buttons}")


    return jsonify({'status': 'Datos recibidos correctamente'})
