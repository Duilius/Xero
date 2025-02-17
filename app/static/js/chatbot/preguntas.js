document.addEventListener("DOMContentLoaded", function () {
    const preguntas = document.querySelectorAll(".pregunta-sugerida");
    const inputChat = document.querySelector("#chat-input");

    preguntas.forEach((pregunta) => {
        pregunta.addEventListener("click", function () {
            escribirTexto(inputChat, this.innerText);
        });
    });

    function escribirTexto(elemento, texto) {
        elemento.value = ""; // Limpiar input
        let i = 0;
        const intervalo = setInterval(() => {
            if (i < texto.length) {
                elemento.value += texto.charAt(i);
                i++;
            } else {
                clearInterval(intervalo);
            }
        }, 50); // Velocidad de escritura
    }
});
