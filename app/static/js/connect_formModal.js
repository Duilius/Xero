document.addEventListener("DOMContentLoaded", function () {
    const modalButton = document.getElementById("modal-button");
    const modalContainer = document.getElementById("modal-container");
    const closeModalButton = document.getElementById("close-modal");
    const dataForm = document.getElementById("data-form");

    modalButton.addEventListener("click", async function () {
        const formData = new FormData(dataForm);
        const response = await fetch("/fetch-dashboard-data", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        console.log("Response from backend:", data);

        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        const summaryData = data.data;

         // Logs para verificar datos
        console.log("GroupedByEmisor:", summaryData.GroupedByEmisor);
        console.log("GroupedByCategory:", summaryData.GroupedByCategory);

        // Manejo seguro de valores numéricos
        const totalInvoices = summaryData.Invoices ? summaryData.Invoices.length : 0;
        const totalTaxes = summaryData.TotalTax || 0;
        const totalAmount = summaryData.TotalAmount || 0;
        const pendingAmount = summaryData.PendingAmount || 0;

        // Actualiza Resumen
        document.getElementById("total-invoices").innerText = totalInvoices;
        document.getElementById("total-taxes").innerText = totalTaxes.toFixed(2);
        document.getElementById("date-range").innerText = `${summaryData.StartDate || "N/A"} - ${summaryData.EndDate || "N/A"}`;
        document.getElementById("total-amount").innerText = `$${totalAmount.toFixed(2)}`;
        document.getElementById("pending-amount").innerText = `$${pendingAmount.toFixed(2)}`;

        // Generar Gráficas
        if (summaryData.GroupedByEmisor) {
            createBarChart(summaryData.GroupedByEmisor);
        }
        if (summaryData.GroupedByCategory) {
            createPieChart(summaryData.GroupedByCategory);
        }

        modalContainer.classList.remove("hidden");
        modalContainer.style.display = "flex";
        //document.body.classList.add("modal-active"); // Desactiva el fondo
    });

    closeModalButton.addEventListener("click", function () {
        modalContainer.style.display = "none";
        modalContainer.classList.add("hidden");
        //document.body.classList.remove("modal-active"); // Reactiva el fondo
    });

    function createBarChart(data) {
        const ctx = document.getElementById("bar-chart").getContext("2d");
    
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: Object.keys(data),
                datasets: [{
                    label: "Total by Emisor",
                    data: Object.values(data),
                    backgroundColor: "rgba(75, 192, 192, 0.2)",
                    borderColor: "rgba(75, 192, 192, 1)",
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Permite ajustar la proporción
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    }
    
    function createPieChart(data) {
        const ctx = document.getElementById("pie-chart").getContext("2d");
    
        new Chart(ctx, {
            type: "pie",
            data: {
                labels: Object.keys(data),
                datasets: [{
                    label: "Category Distribution",
                    data: Object.values(data),
                    backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56"],
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Permite ajustar la proporción
                plugins: {
                    legend: {
                        position: "top", // Ajusta la posición de la leyenda
                    },
                },
            },
        });
    }

});

