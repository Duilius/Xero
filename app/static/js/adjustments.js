// Función para abrir el modal
function openAdjustmentModal(lenderName, lenderId, borrowerName, borrowerId, loanAmount) {
    // Log al inicio de la función
    console.log('Opening modal with:', { lenderName, lenderId, borrowerName, borrowerId, loanAmount });
    
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

    fetch(`/api/loans/details/${lenderId}/${borrowerId}`, {
        credentials: 'include'
    })
    .then(response => {
        console.log('2. API Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('3. Data received:', data);
        console.log('4. Payment dates:', data.payments.comparison.map(p => p.date));  // Cambio aquí
        updateLoanDetails(data);
        updatePaymentHistory(data.payments);
    })
    .catch(error => {
        console.error('Error in fetch:', error);
    });

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// Actualizar detalles del préstamo
function updateLoanDetails(data) {
    console.log('Updating loan details:', data);
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
                    $${Math.abs(data.currentBalance).toLocaleString()}
                </p>
            </div>
        </div>
    `;
}

// Actualizar historial de pagos
function updatePaymentHistory(paymentsData) {
    const paymentHistory = document.getElementById('payment-history');
    if (!paymentHistory) return;

    if (!paymentsData || !paymentsData.comparison || paymentsData.comparison.length === 0) {
        paymentHistory.innerHTML = '<p class="text-gray-500 italic">No payments recorded yet.</p>';
        return;
    }

    const rows = paymentsData.comparison.map(payment => `
        <tr class="${!payment.lender_amount ? 'bg-yellow-50' : 'hover:bg-gray-50'}">
            <td class="px-4 py-2">${formatDate(payment.date)}</td>
            <td class="px-4 py-2 text-right font-medium ${payment.borrower_amount ? 'text-green-600' : 'text-gray-400'}">
                ${payment.borrower_amount ? 
                    `$${payment.borrower_amount.toLocaleString()}` : 
                    '-'}
            </td>
            <td class="px-4 py-2 text-right font-medium ${payment.lender_amount ? 'text-green-600' : 'text-red-600'}">
                ${payment.lender_amount ? 
                    `$${payment.lender_amount.toLocaleString()}` : 
                    'No registrado'}
            </td>
            <td class="px-4 py-2">
                <span class="px-2 py-1 rounded-full text-sm ${
                    !payment.lender_amount ? 
                    'bg-yellow-100 text-yellow-800' : 
                    'bg-green-100 text-green-600'
                }">
                    ${!payment.lender_amount ? 'Pendiente de Reconciliar' : 'Registrado'}
                </span>
            </td>
        </tr>
    `).join('');

    paymentHistory.innerHTML = `
        <div class="border rounded-lg overflow-hidden">
            <h3 class="text-lg font-semibold p-4 bg-gray-50 border-b">Payment History</h3>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-4 py-2 text-left text-sm font-medium text-gray-500">Date</th>
                            <th class="px-4 py-2 text-right text-sm font-medium text-gray-500">Paid by Demo2</th>
                            <th class="px-4 py-2 text-right text-sm font-medium text-gray-500">Received by Demo Company</th>
                            <th class="px-4 py-2 text-left text-sm font-medium text-gray-500">Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        ${rows}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="mt-6 flex justify-end">
            <button 
                onclick="showReconciliationForm()"
                class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg flex items-center gap-2"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
                Reconciliar Pago
            </button>
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