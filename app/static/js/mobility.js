function openModal() {
    document.getElementById('chatbot-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('chatbot-modal').style.display = 'none';
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (message) {
        const chatMessages = document.getElementById('chat-messages');
        const newMessage = document.createElement('div');
        newMessage.textContent = message;
        chatMessages.appendChild(newMessage);
        input.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

document.getElementById('consultation-form').addEventListener('submit', function(event) {
    event.preventDefault();
    alert('Thank you for your submission. We will get back to you within 24 hours.');
});