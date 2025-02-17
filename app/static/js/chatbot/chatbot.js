document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM completamente cargado.");

    // Verifica la existencia del contenedor de chat
    let chatContainer = document.getElementById("chat-messages");
    if (!chatContainer) {
        console.error("❌ No se encontró el contenedor del chat (chat-messages).");
        return;
    }

    // Evento para enviar mensajes
    document.getElementById("chatbot-send").addEventListener("click", enviarMensaje);
    document.getElementById("chatbot-text").addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            enviarMensaje();
        }
    });

    cargarResumenEmpresa();

    function cargarResumenEmpresa() {
        console.log("📢 Ejecutando cargarResumenEmpresa...");
        fetch("/api/resumen_empresa")
            .then(response => response.json())
            .then(data => {
                console.log("📩 Respuesta API:", data);
                mostrarResumenEmpresa(data);
            })
            .catch(error => console.error("❌ Error al obtener resumen de la empresa:", error));
    }

    function mostrarResumenEmpresa(data) {
        let chatBody = document.getElementById("chatbot-body");
        if (!chatBody) {
            console.error("❌ No se encontró el contenedor del chat.");
            return;
        }

        chatBody.innerHTML = `
            <div class="empresa-resumen">
                <h3>${data.empresa}</h3>
                <p>${data.resumen}</p>
            </div>
            <div class="preguntas-sugeridas">
                <h4>Preguntas sugeridas:</h4>
                <ul style='list-style:none; padding:0; margin:0;'>
                    ${data.sugerencias.map(pregunta => `
                        <li>
                            <input type="radio" name="pregunta-sugerida" class="pregunta-radio" value="${pregunta}" />
                            <label>${pregunta}</label>
                        </li>`).join("")}
                </ul>
            </div>
        `;

        document.querySelectorAll(".pregunta-radio").forEach(radio => {
            radio.addEventListener("change", function () {
                escribirEnInputConEfecto(this.value);
            });
        });
    }

    function escribirEnInputConEfecto(texto) {
        let input = document.getElementById("chatbot-text");
        if (!input) return;

        input.value = "";
        let index = 0;
        let interval = setInterval(() => {
            input.value += texto[index];
            index++;
            if (index === texto.length) clearInterval(interval);
        }, 50);
    }

    document.getElementById("chatbot-send").addEventListener("click", enviarMensaje);
    document.getElementById("chatbot-text").addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            enviarMensaje();
        }
    });

    function enviarMensaje() {
        let input = document.getElementById("chatbot-text");
        let mensaje = input.value.trim();

        if (mensaje === "") return; // No enviar mensajes vacíos

        agregarMensajeUsuario(mensaje);
        input.value = ""; // Limpiar input

        // Simulación de respuesta del chatbot
        setTimeout(() => {
            agregarMensajeChatbot("🤖 Lo siento, aún estoy aprendiendo. Pregunta algo más.");
        }, 1000);
    }

    function agregarMensajeUsuario(mensaje) {
        let chatContainer = document.getElementById("chat-messages");
        let mensajeElemento = document.createElement("div");
        mensajeElemento.classList.add("chatbot-message", "usuario");
        mensajeElemento.textContent = mensaje;
        chatContainer.appendChild(mensajeElemento);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function agregarMensajeChatbot(mensajeHtml) {
        let chatContainer = document.getElementById("chat-messages");
        let mensajeElemento = document.createElement("div");
        mensajeElemento.classList.add("chatbot-message", "chatbot");
        mensajeElemento.innerHTML = mensajeHtml;
        chatContainer.appendChild(mensajeElemento);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
