// Abrir el modal del chatbot
/*
Interactividad del chatbot Duilius implementada. Incluye:
1. Apertura y cierre del modal con el botón flotante.
2. Envío de mensajes al servidor y
*/ 

function openDuiliusModal() {
    document.getElementById('duiliusModal').classList.remove('hidden');
}

// Cerrar el modal del chatbot
function closeDuiliusModal() {
    document.getElementById('duiliusModal').classList.add('hidden');
}

// Enviar mensaje al chatbot
async function sendDuiliusMessage() {
    const userInput = document.getElementById('duiliusUserInput');
    const message = userInput.value.trim();
    const chatWindow = document.getElementById('duiliusMessages');

    if (message === "") return;

    // Mostrar el mensaje del usuario en la ventana de chat
    appendMessage('user', message);
    userInput.value = "";

    try {
        // Enviar mensaje al servidor
        const response = await fetch('/chatbot/duilius-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        appendMessage('duilius', data.response);
    } catch (error) {
        appendMessage('duilius', 'Oops! Something went wrong. Please try again later.');
    }
}

// Agregar mensaje al chat
function appendMessage(sender, text) {
    const chatWindow = document.getElementById('duiliusMessages');
    const messageBubble = document.createElement('div');

    messageBubble.classList.add('duilius-message');
    messageBubble.classList.add(sender === 'user' ? 'user-message' : 'duilius-message');
    messageBubble.textContent = text;

    chatWindow.appendChild(messageBubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Cerrar el modal si se hace clic fuera del contenido
window.onclick = function(event) {
    const modal = document.getElementById('duiliusModal');
    if (event.target === modal) {
        closeDuiliusModal();
    }
}


// Función para que Duilius hable
// Mostrar bocadillo de Duilius
function duiliusSpeak(message) {
    const speechBubble = document.getElementById('duiliusSpeechBubble');
    const speechText = document.getElementById('duiliusSpeechText');
    speechText.textContent = message;
    speechBubble.classList.remove('hidden');

    setTimeout(() => {
        speechBubble.classList.add('hidden');
    }, 4000);
}

// Prueba inicial
duiliusSpeak("¡Hola! ¿En qué puedo ayudarte hoy?");

function sendPredefinedQuestion(questionId) {
    let message;
    switch (questionId) {
        case 1:
            message = "You selected: View FAQs.";
            break;
        case 2:
            message = "You selected: View Offered Services.";
            break;
        case 3:
            message = "You selected: View Plans.";
            break;
        default:
            message = "Unknown selection.";
    }
    addChatbotMessage(message, "bot");
}


function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (message) {
        addChatbotMessage(message, "user");
        input.value = "";

        // Simulate bot response
        setTimeout(() => {
            addChatbotMessage("I'm still learning to assist with your queries.", "bot");
        }, 1000);
    }
}


function addChatbotMessage(message, sender) {
    const messagesDiv = document.getElementById("duilius-messages");
    const messageDiv = document.createElement("div");
    messageDiv.className = sender === "user" ? "duilius-user-message" : "duilius-bot-message";
    messageDiv.textContent = message;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}