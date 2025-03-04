const topButton = document.getElementById("topButton");
const leftButton = document.getElementById("leftButton");
const rightButton = document.getElementById("rightButton");
const downButton = document.getElementById("downButton");
const centerButton = document.getElementById("centerButton");

function restartPosition(){
    sendData(0, 0);
}

function upCamera(){
    topButton.addEventListener('click', function(){
        const data = {
            x: 0,
            y: 0.3, 
        };
        sendData(data.x, data.y);
    });
}

function leftCamera(){
    leftButton.addEventListener('click', function(){
        const data = {
            x: -0.3, // x es -1 para el movimiento hacia la izquierda
            y: 0,
        };
        sendData(data.x, data.y);
    });
}

function rightCamera(){
    rightButton.addEventListener('click', function(){
        const data = {
            x: 0.3, // x es 1 para el movimiento hacia la derecha
            y: 0,
        };
        sendData(data.x, data.y);
    });
}

function downCamera(){
    downButton.addEventListener('click', function(){
        const data = {
            x: 0,
            y: -0.3, // y es -1 para el movimiento hacia abajo
        };
        sendData(data.x, data.y);
    });
}

// Función para enviar los datos al servidor Flask
function sendData(x, y) {
    fetch('http://localhost:5000/update-joystick', { // La URL del endpoint de tu backend
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            x: x,
            y: y,
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data); // Maneja la respuesta del servidor
    })
    .catch(error => {
        console.error('Error al enviar datos al servidor:', error);
    });
}

// Iniciar las funciones de los botones
upCamera();
leftCamera();
rightCamera();
downCamera();
