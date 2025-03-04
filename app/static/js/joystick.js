const topLeftShooter = document.getElementById("topLeftShooter");
const topRightShooter = document.getElementById("topRightShooter");
const botLeftShooter = document.getElementById("botLeftShooter");
const botRightShooter = document.getElementById("botRightShooter");
const tiggerShooter = document.getElementById("tiggerShooter");

function setupButton(button, action) {
    // Ratón (mouse)
    button.addEventListener('mousedown', function () {
        sendJoystickData(0, 0, action);
    });

    button.addEventListener('mouseup', function () {
        sendJoystickData(0, 0, [false, false, false, false, false]);
    });

    // Táctil (touch)
    button.addEventListener('touchstart', function (event) {
        event.preventDefault();  // Evitar comportamiento por defecto (como el scroll)
        sendJoystickData(0, 0, action);
    });

    button.addEventListener('touchend', function (event) {
        event.preventDefault();  // Evitar comportamiento por defecto
        sendJoystickData(0, 0, [false, false, false, false, false]);
    });
}

// Configuración de los botones
setupButton(topLeftShooter, [false, true, false, false, false]);
setupButton(topRightShooter, [false, false, true, false, false]);
setupButton(botLeftShooter, [false, false, false, true, false]);
setupButton(botRightShooter, [false, false, false, false, true]);
setupButton(tiggerShooter, [true, false, false, false, false]);

function showJoystickButtons(buttons) {
    if (buttons[0]) {
        tiggerShooter.classList.add("bg-red-500");
    } else {
        tiggerShooter.classList.remove("bg-red-500");
    }

    if (buttons[1]) {
        topLeftShooter.classList.add("bg-red-500");
    } else {
        topLeftShooter.classList.remove("bg-red-500");
    }

    if (buttons[2]) {
        topRightShooter.classList.add("bg-red-500");
    } else {
        topRightShooter.classList.remove("bg-red-500");
    }

    if (buttons[3]) {
        botLeftShooter.classList.add("bg-red-500");
    } else {
        botLeftShooter.classList.remove("bg-red-500");
    }

    if (buttons[4]) {
        botRightShooter.classList.add("bg-red-500");
    } else {
        botRightShooter.classList.remove("bg-red-500");
    }
}

function updateJoystick() {
    const gamepads = navigator.getGamepads();
    if (gamepads && gamepads[0]) {
        const gamepad = gamepads[0];
        const x = parseFloat(gamepad.axes[0].toFixed(2));
        const y = parseFloat(gamepad.axes[1].toFixed(2));
        const buttons = gamepad.buttons.map(button => button.pressed);
        sendJoystickData(x, y, buttons);
    }
    requestAnimationFrame(updateJoystick);
}

function sendJoystickData(x, y, buttons) {
    showJoystickButtons(buttons);
    if (x !== 0 || y !== 0 ) {
        console.log(`Los datos son x: ${x}, y: ${y}, Botones: ${buttons}`);
    }
    fetch('http://localhost:5000/update-joystick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, buttons })
    })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del servidor:', data);
        })
        .catch(error => console.error('Error al enviar datos al servidor:', error));
}

updateJoystick();
