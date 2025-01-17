// Función para abrir el modal
function openAdjustmentModal(lenderName, lenderId, borrowerName, borrowerId, loanAmount) {
    // Log al inicio de la función
    console.log('Modal Parameters:', { lenderName, lenderId, borrowerName, borrowerId, loanAmount });

    if (!lenderId || !borrowerId) {
        console.error('Missing IDs:', { lenderId, borrowerId });
        return;
    }

    const modal = document.getElementById('adjustment-modal');
    const lenderElem = document.getElementById('lender-name');
    const borrowerElem = document.getElementById('borrower-name');
    const loanDetails = document.getElementById('loan-details');
    const paymentHistory = document.getElementById('payment-history');
    const authForm = document.getElementById('authorization-form');

    // Log de elementos encontrados
    console.log('Elements found:', {
        modal: !!modal,
        lenderElem: !!lenderElem,
        borrowerElem: !!borrowerElem,
        loanDetails: !!loanDetails,
        paymentHistory: !!paymentHistory,
        authForm: !!authForm
    });

    // Reset y limpieza (sin cambios)
    if (loanDetails) loanDetails.innerHTML = '';
    if (paymentHistory) paymentHistory.innerHTML = '';
    if (authForm) authForm.classList.add('hidden');

    // Actualizar nombres (sin cambios)
    if (lenderElem) lenderElem.textContent = lenderName;
    if (borrowerElem) borrowerElem.textContent = borrowerName;

    // Log antes del fetch
    const url = `/api/loans/details/${lenderId}/${borrowerId}`.replace(/\/$/, ''); // Elimina barra final si existe
    console.log('Fetching URL:', url);

    fetch(url, {
        credentials: 'include'
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('Received data:', data);
        updateLoanDetails(data, loanAmount);
        updatePaymentHistory(data.payments);
    })
    .catch(error => {
        console.error('Error details:', error);
        showError('Error loading loan details');
    });

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// Actualizar detalles del préstamo
function updateLoanDetails(data) {
    const loanDetails = document.getElementById('loan-details');
    if (!loanDetails) return;

    loanDetails.innerHTML = `
        <div class="grid grid-cols-3 gap-4">
            <div class="bg-gray-50 p-4 rounded-lg">
                <h3 class="text-sm font-medium text-gray-500">Original Loan Amount</h3>
                <p class="mt-2 text-xl font-bold">$${data.originalAmount.toLocaleString()}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
                <h3 class="text-sm font-medium text-gray-500">Total Payments</h3>
                <p class="mt-2 text-xl font-bold">$${data.totalPayments.toLocaleString()}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
                <h3 class="text-sm font-medium text-gray-500">Current Balance</h3>
                <p class="mt-2 text-xl font-bold ${data.currentBalance > 0 ? 'text-red-600' : ''}">
                    $${data.currentBalance.toLocaleString()}
                </p>
            </div>
        </div>
    `;
}

// Actualizar historial de pagos
function updatePaymentHistory(payments) {
    const paymentHistory = document.getElementById('payment-history');
    if (!paymentHistory) return;
    
    if (!payments || payments.length === 0) {
        paymentHistory.innerHTML = '<p class="text-gray-500 italic">No payments recorded yet.</p>';
        return;
    }

    const rows = payments.map(payment => `
        <tr>
            <td class="px-4 py-2">${payment.date}</td>
            <td class="px-4 py-2">$${payment.amount.toLocaleString()}</td>
            <td class="px-4 py-2">${payment.type}</td>
            <td class="px-4 py-2">${payment.status}</td>
        </tr>
    `).join('');

    paymentHistory.innerHTML = `
        <h3 class="text-lg font-semibold mb-4">Payment History</h3>
        <div class="overflow-x-auto">
            <table class="min-w-full">
                <thead>
                    <tr class="bg-gray-50">
                        <th class="px-4 py-2 text-left">Date</th>
                        <th class="px-4 py-2 text-left">Amount</th>
                        <th class="px-4 py-2 text-left">Type</th>
                        <th class="px-4 py-2 text-left">Status</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

// Funciones para el formulario de autorización
function showAuthorizationForm() {
    const authForm = document.getElementById('authorization-form');
    if (authForm) {
        authForm.classList.remove('hidden');
    }
}

function hideAuthorizationForm() {
    const authForm = document.getElementById('authorization-form');
    if (authForm) {
        authForm.classList.add('hidden');
    }
}

function showError(message) {
    // Implementar manejo de errores según necesites
    console.error(message);
}