window.onload = function () { 
    console.log("Script cargado correctamente.");
    // Seleccionamos los botones
    const darkButton = document.getElementById('darkButton');
    const lightButton = document.getElementById('lightButton');
    const elementosNocturnos = document.getElementsByClassName('modoNocturno');
    const inputZoom = document.getElementById("inputZoom")
    const activeButton = document.getElementById("activeButton")

    if (!darkButton || !lightButton || !inputZoom || !activeButton) {
        console.error("Uno o más elementos no fueron encontrados.");
        return;
    }
    console.log("Elementos encontrados correctamente.");
    // Función para activar el modo oscuro
    darkButton.addEventListener('click', () => {
        console.log("noche")
        document.body.classList.add('dark');
        for (elemento of elementosNocturnos) {
            elemento.classList.add("bg-gray-800/70")
        }
        inputZoom.classList.add("accent-white")
        activeButton.classList.remove("bg-gray-800/70")
        activeButton.classList.remove("bg-gray-800/90")
        activeButton.classList.add("bg-white")
        activeButton.classList.remove("text-white")
        activeButton.classList.add("text-slate-800")
        darkButton.disabled = true;
        lightButton.disabled = false;
    });

    // Función para activar el modo claro
    lightButton.addEventListener('click', () => {
        document.body.classList.remove('dark');
        for (elemento of elementosNocturnos) {
            elemento.classList.remove("bg-gray-800/70")
        }
        inputZoom.classList.remove("accent-white")
        activeButton.classList.remove("bg-white")
        activeButton.classList.add("bg-gray-800/90")
        activeButton.classList.remove("text-slate-800")
        activeButton.classList.add("text-white")

        lightButton.disabled = true;
        darkButton.disabled = false;
    });
};