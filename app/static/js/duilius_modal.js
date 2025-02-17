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
// Enviar mensaje al chatbot
async function sendDuiliusMessage() {
    const userInput = document.getElementById('duiliusUserInput');
    const message = userInput.value.trim();

    if (message === "") return;
    appendMessage('user', message);
    userInput.value = "";

    try {
        const response = await fetch('/chatbot/process-query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const result = await response.json();
        
        if (result.success) {
            // Mostrar datos si hay query ejecutado
            if (result.data) {
                // Mostrar tabla o gráfico según metadata
                displayResponse(result.data, result.metadata);
            } else {
                // Mostrar solo respuesta general
                appendMessage('duilius', result.metadata.response);
            }
            
            // Mostrar insights y tips
            if (result.metadata.insights) {
                displayInsights(result.metadata.insights);
            }
            if (result.metadata.tips) {
                displayTips(result.metadata.tips);
            }
        } else {
            appendMessage('duilius', 'Sorry, I could not process your request.');
        }
    } catch (error) {
        appendMessage('duilius', 'Oops! Something went wrong.');
    }
}

// Función para mostrar datos y gráficos
function displayResponse(data, metadata) {
    const chatWindow = document.getElementById('duiliusMessages');
    const responseDiv = document.createElement('div');
    responseDiv.classList.add('duilius-response');

    // Agregar título
    const title = document.createElement('h3');
    title.textContent = metadata.title;
    responseDiv.appendChild(title);

    // Mostrar datos según el tipo
    if (metadata.response_type === 'table') {
        responseDiv.appendChild(createTable(data));
    }

    // Mostrar gráfico si es necesario
    if (metadata.graph_type !== 'none') {
        const chartDiv = document.createElement('div');
        chartDiv.id = 'chart-' + Date.now();
        responseDiv.appendChild(chartDiv);
        createChart(chartDiv.id, data, metadata.graph_type);
    }

    chatWindow.appendChild(responseDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Función para mostrar insights
function displayInsights(insights) {
    const chatWindow = document.getElementById('duiliusMessages');
    const insightsDiv = document.createElement('div');
    insightsDiv.classList.add('duilius-insights');
    
    Object.entries(insights).forEach(([key, value]) => {
        const p = document.createElement('p');
        p.textContent = `${key}: ${value}`;
        insightsDiv.appendChild(p);
    });

    chatWindow.appendChild(insightsDiv);
}

// Función para mostrar tips
function displayTips(tips) {
    const chatWindow = document.getElementById('duiliusMessages');
    const tipsDiv = document.createElement('div');
    tipsDiv.classList.add('duilius-tips');
    
    tips.forEach(tip => {
        const p = document.createElement('p');
        p.textContent = `💡 ${tip}`;
        tipsDiv.appendChild(p);
    });

    chatWindow.appendChild(tipsDiv);
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


/* QUERYS  */
document.getElementById('enableSQLQuery').addEventListener('change', function() {
    const sqlInput = document.getElementById('sqlQueryInput');
    const sqlExamples = document.getElementById('sqlExamples');

    if (this.checked) {
        sqlInput.removeAttribute('disabled');
        sqlExamples.style.display = 'block';
    } else {
        sqlInput.setAttribute('disabled', 'true');
        sqlExamples.style.display = 'none';
    }
});
