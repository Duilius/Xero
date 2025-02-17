document.addEventListener("DOMContentLoaded", function () {
    const suggestedQuestions = document.querySelectorAll(".suggested-question");
    const chatInput = document.querySelector("#chat-input");

    suggestedQuestions.forEach(question => {
        question.addEventListener("click", function () {
            chatInput.value = this.textContent;
            chatInput.focus();
        });
    });
});
