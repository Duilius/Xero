// Función para abrir el modal del chatbot
function openChatbot() {
    const modal = document.getElementById("chatbot-modal");
    modal.style.display = "flex";
}

// Función para enviar mensajes
function sendMessage() {
    const input = document.getElementById("chatbot-input");
    const message = input.value.trim();

    if (message) {
        const messagesDiv = document.getElementById("chatbot-messages");

        // Mostrar la pregunta del usuario
        const userMessage = document.createElement("div");
        userMessage.className = "message user";
        userMessage.textContent = message;
        messagesDiv.appendChild(userMessage);

        // Enviar la pregunta al backend (simulado aquí)
        setTimeout(() => {
            const botMessage = document.createElement("div");
            botMessage.className = "message bot";
            botMessage.textContent = "Esta es una respuesta de ejemplo.";
            messagesDiv.appendChild(botMessage);

            // Desplazar el scroll al final
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }, 1000);

        // Limpiar el input
        input.value = "";
    }
}

// Cerrar el modal al hacer clic fuera de él
window.onclick = function (event) {
    const modal = document.getElementById("chatbot-modal");
    if (event.target === modal) {
        modal.style.display = "none";
    }
};


// ********************** ENVIAR PREGUNTA A OpenAI ***************************
// Función para enviar mensajes
async function sendMessage() {
    const input = document.getElementById("chatbot-input");
    const message = input.value.trim();

    if (message) {
        const messagesDiv = document.getElementById("chatbot-messages");

        // Mostrar la pregunta del usuario
        const userMessage = document.createElement("div");
        userMessage.className = "message user";
        userMessage.textContent = message;
        messagesDiv.appendChild(userMessage);

        // Limpiar el input
        input.value = "";

        // Deshabilitar el botón de enviar mientras se procesa la respuesta
        const sendButton = document.getElementById("send-button");
        sendButton.disabled = true;

        try {
            // Enviar la pregunta al backend
            const response = await fetch("/chatbot/chatDeep", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message })
                //body: JSON.stringify({ question: message }),
            });

            if (!response.ok) {
                throw new Error("Error al obtener la respuesta del servidor");
            }

            const data = await response.json();

            // Mostrar la respuesta del chatbot
            const botMessage = document.createElement("div");
            botMessage.className = "message bot";
            botMessage.textContent = data.response;
            messagesDiv.appendChild(botMessage);
        } catch (error) {
            console.error("Error:", error);
            const errorMessage = document.createElement("div");
            errorMessage.className = "message bot";
            errorMessage.textContent = "Hubo un error al procesar tu pregunta. Inténtalo de nuevo.";
            messagesDiv.appendChild(errorMessage);
        } finally {
            // Habilitar el botón de enviar
            sendButton.disabled = false;

            // Desplazar el scroll al final
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    }
}