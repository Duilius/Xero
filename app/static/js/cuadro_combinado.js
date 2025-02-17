// Función para actualizar el rango de fechas
function updateDateRange(startDate, endDate) {
    console.log('Actualizando fechas:', startDate, endDate);
    
    window.lendingState.setDateRange(startDate, endDate);
}


// Actualiza el estado del botón de procesar
function updateProcessButton() {
    const button = document.getElementById('processButton');
    const hasValidDateRange = dateRange.start && dateRange.end;
    button.disabled = selectedOrganizations.size < 2 || !hasValidDateRange || !selectedAccount;
    
    if (!button.hasEventListener) {
        button.addEventListener('click', processBalances);
        button.hasEventListener = true;
    }
}

// Procesa y muestra los saldos
async function processBalances() {
    const balanceCells = document.querySelectorAll('.balance-cell');
    
    for (const cell of balanceCells) {
        const type = cell.dataset.type;
        const orgId = cell.dataset.org;
        const accountId = cell.dataset.account;
        
        const amount = await getBalanceFromXero(orgId, accountId);
        
        const link = document.createElement('a');
        link.href = '#';
        link.className = `balance-link ${type === 'lender' ? 'text-blue-600' : 'text-red-600'}`;
        link.textContent = new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'DOL'
        }).format(amount);
        
        // Tooltip con información de la cuenta
        link.title = type === 'lender' ? 
            `Cuenta préstamo: ${selectedOrgs.lenderAccount.name}` :
            `Cuenta pagos: ${selectedOrgs.borrowerAccount.name}`;
        
        link.onclick = (e) => {
            e.preventDefault();
            showTransactionDetails(orgId, accountId, dateRange.start, dateRange.end);
        };
        
        cell.innerHTML = '';
        cell.appendChild(link);
    }
}


//app/static/js/cuadro_combinado.js


// Función para mostrar detalles de transacciones
async function showTransactionDetails(orgId, accountId, startDate, endDate) {
    try {
        const response = await fetch(`/auth/transactions/${orgId}/${accountId}?start_date=${startDate}&end_date=${endDate}`);
        
        if (!response.ok) {
            throw new Error('Error fetching transactions');
        }
        
        const data = await response.json();
        displayTransactionDetails(data.transactions);
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
 }

 function displayTransactionDetails(transactions) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    const content = `
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold">Detalle de Transacciones</h3>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <table class="min-w-full">
                <thead>
                    <tr>
                        <th class="p-2">Fecha</th>
                        <th class="p-2">Tipo</th>
                        <th class="p-2">Descripción</th>
                        <th class="p-2 text-right">Monto</th>
                    </tr>
                </thead>
                <tbody>
                    ${transactions.map(t => `
                        <tr class="border-t">
                            <td class="p-2">${new Date(t.date).toLocaleDateString()}</td>
                            <td class="p-2">${t.type}</td>
                            <td class="p-2">${t.description}</td>
                            <td class="p-2 text-right ${t.amount < 0 ? 'text-red-600' : 'text-green-600'}">
                                ${new Intl.NumberFormat('es-ES', {
                                    style: 'currency',
                                    currency: 'DOL'
                                }).format(t.amount)}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    modal.innerHTML = content;
    document.body.appendChild(modal);
 }


function validateSearch(input) {
    if (input.value.length >= 3) {
        setTimeout(() => {
            htmx.trigger(input, 'searchValidated');
        }, 300);
    }
}

// Nueva función para calcular totales
function calculateTotals(table) {
    if (!table) {
        console.error('Table element not found');
        return;
    }

    try {
        const rows = table.getElementsByTagName('tr');
        if (!rows || rows.length === 0) {
            console.error('No rows found in table');
            return;
        }

        // Eliminar fila de totales existente si hay
        const existingTotalRow = table.querySelector('tr.total-row');
        if (existingTotalRow) {
            existingTotalRow.remove();
        }

        const numRows = rows.length;
        if (numRows < 2) return; // No hay suficientes datos para calcular

        // Crear fila de totales
        const totalRow = document.createElement('tr');
        totalRow.classList.add('total-row');

        // Primera celda (texto "Totales")
        const firstCell = document.createElement('td');
        firstCell.textContent = 'Totales';
        firstCell.style.fontWeight = 'bold';
        totalRow.appendChild(firstCell);

        // Calcular totales por columna
        for (let col = 1; col < rows[0].cells.length; col++) {
            let total = 0;
            
            // Sumar valores de cada columna, excluyendo la fila de encabezado
            for (let row = 1; row < numRows; row++) {
                const cell = rows[row].cells[col];
                if (!cell) continue;

                const cellText = cell.textContent;
                if (cellText && cellText !== '-') {
                    // Remover símbolos de moneda y convertir a número
                    const value = parseFloat(cellText.replace(/[^\d,-]/g, '').replace(',', '.'));
                    if (!isNaN(value)) {
                        total += value;
                    }
                }
            }

            // Crear celda de total
            const totalCell = document.createElement('td');
            totalCell.style.fontWeight = 'bold';
            
            // Formatear el total como moneda
            totalCell.textContent = new Intl.NumberFormat('es-CL', {
                style: 'currency',
                currency: 'CLP'
            }).format(total);

            totalRow.appendChild(totalCell);
        }

        // Añadir fila de totales a la tabla
        table.appendChild(totalRow);

    } catch (error) {
        console.error('Error calculating totals:', error);
    }
}


async function getBalanceFromXero(orgId, accountId) {
    try {
        if (!dateRange?.start || !dateRange?.end) {
            console.error('dateRange:', dateRange);
            return 0;
        }
 
        const params = new URLSearchParams({
            start_date: dateRange.start,
            end_date: dateRange.end,
            account_id: accountId
        });
        
        const url = `/auth/balances/${orgId}?${params}`;
        console.log('Requesting balance:', url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: { 
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
 
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error response:', errorData);
            throw new Error(JSON.stringify(errorData));
        }
        
        const data = await response.json();
        return data.balance || 0;
    } catch (error) {
        console.error('Balance fetch error:', error);
        return 0;
    }
 }