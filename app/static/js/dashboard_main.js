document.addEventListener("DOMContentLoaded", function () {
    // Botón de Modo Oscuro/Claro
    const themeToggle = document.getElementById("toggle-theme");
    themeToggle.addEventListener("click", function () {
        document.body.classList.toggle("light-mode");
    });

    // Mostrar el Modal
    const modalButton = document.getElementById("modal-button");
    const modalContainer = document.getElementById("modal-container");
    const closeModalButton = document.getElementById("close-modal");

    modalButton.addEventListener("click", function () {
        modalContainer.style.display = "flex";
    });

    // Cerrar el Modal
    closeModalButton.addEventListener("click", function () {
        modalContainer.style.display = "none";
    });
});
