// Espera a que el DOM esté listo
window.onload = function() {
    // Accede al video en el HTML
    const video = document.getElementById('video');

    // Solicita acceso a la cámara
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            // Asocia el flujo de la cámara al elemento video
            video.srcObject = stream;
        })
        .catch(function(error) {
            console.error("No se pudo acceder a la cámara: ", error);
        });
};
