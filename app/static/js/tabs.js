// 1. dateRangeManager (se mantiene como está)
// Sistema de manejo de fechas y menú
const dateRangeManager = {
    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupEventListeners();
            });
        } else {
            this.setupEventListeners();
        }
    },

    // En tabs.js
    setupEventListeners() {
        const periodSelector = document.getElementById('period-select');
        const customDateContainer = document.getElementById('custom-date');
        const customStartInput = customDateContainer?.querySelector('input:first-child');
        const customEndInput = customDateContainer?.querySelector('input:last-child');

        if (periodSelector) {
            periodSelector.addEventListener('change', (e) => {
                const value = e.target.value;
                console.log('Period changed:', value);
                
                if (value === 'custom') {
                    customDateContainer?.classList.remove('hidden');
                } else {
                    customDateContainer?.classList.add('hidden');
                    this.updateSelectedDates(value);
                }
            });
        }

        if (customStartInput && customEndInput) {
            [customStartInput, customEndInput].forEach(input => {
                input.addEventListener('change', () => {
                    if (customStartInput.value && customEndInput.value) {
                        this.validateAndSendCustomDates();
                    }
                });
            });
        }
    },

    // Agregar función getFinancialYearEnd
    getFinancialYearEnd() {
        try {
            const sessionToken = document.cookie
                .split('; ')
                .find(row => row.startsWith('session_xero='))
                ?.split('=')[1];
                
            if (!sessionToken) {
                console.error('❌ No se encontró cookie session_xero');
                return null;
            }

            const decodedData = JSON.parse(atob(sessionToken.split('.')[1]));
            const organizations = decodedData.session_xero.organizations.connections;
            
            return {
                day: organizations[0].fy_end_day,
                month: organizations[0].fy_end_month,
                currency: organizations[0].currency
            };
        } catch (error) {
            console.error('❌ Error leyendo datos fiscales:', error);
            return null;
        }
    },

    updateSelectedDates(period) {
        console.log('====> updateSelectedDates called with:', period);
        const dates = this.getDates();
        let startDate, endDate;
     
        switch (period) {
            case 'today':
                startDate = endDate = this.formatDateISO(dates.today);
                break;
            case 'month-end':
                startDate = this.formatDateISO(dates.today);
                endDate = this.formatDateISO(dates.monthEnd);
                break;
            case 'last-month':
                startDate = this.formatDateISO(new Date(dates.lastMonthEnd.getFullYear(), dates.lastMonthEnd.getMonth(), 1));
                endDate = this.formatDateISO(dates.lastMonthEnd);
                break;
            case 'last-quarter':
                startDate = this.formatDateISO(new Date(dates.lastQuarterEnd.getFullYear(), dates.lastQuarterEnd.getMonth() - 2, 1));
                endDate = this.formatDateISO(dates.lastQuarterEnd);
                break;
            case 'last-year':
                const fyEnd = this.getFinancialYearEnd();
                if (fyEnd) {
                    const today = new Date();
                    const currentYear = today.getFullYear();
                    
                    // Si estamos después del fin de año fiscal, usamos el año actual
                    // Si no, usamos el año anterior
                    const fiscalYear = (today.getMonth() + 1 > fyEnd.month || 
                                     (today.getMonth() + 1 === fyEnd.month && today.getDate() > fyEnd.day)) 
                                     ? currentYear 
                                     : currentYear - 1;
                    
                    endDate = this.formatDateISO(new Date(fiscalYear, fyEnd.month - 1, fyEnd.day));
                    startDate = this.formatDateISO(new Date(fiscalYear - 1, fyEnd.month - 1, fyEnd.day + 1));
                } else {
                    // Si no podemos obtener el año fiscal, usar año calendario
                    startDate = this.formatDateISO(new Date(dates.lastYearEnd.getFullYear(), 0, 1));
                    endDate = this.formatDateISO(dates.lastYearEnd);
                }
                break;
        }
     
        if (startDate && endDate) {
            const start = this.formatDateISO(new Date(startDate));
            const end = this.formatDateISO(new Date(endDate));
     
            console.log('Dates selected:', {startDate, endDate});
            
            // Actualizar estado global
            if (typeof window.updateDateRange === 'function') {
                window.updateDateRange(start, end);
            }
            
            // Retornar fechas formateadas
            return { startDate: start, endDate: end };
        }
        
        return null;
     },

    validateAndSendCustomDates() {
        const customDateContainer = document.getElementById('custom-date');
        const fromDateInput = customDateContainer.querySelector('input[type="date"]:first-child');
        const toDateInput = customDateContainer.querySelector('input[type="date"]:last-child');
    
        // Solo proceder si ambas fechas están seleccionadas
        if (fromDateInput.value && toDateInput.value) {
            const startDate = this.formatDateISO(new Date(fromDateInput.value));
            const endDate = this.formatDateISO(new Date(toDateInput.value));
    
            // Validar que la fecha final sea mayor o igual a la inicial
            if (new Date(endDate) >= new Date(startDate)) {
                window.updateDateRange(startDate, endDate);
            } else {
                // Mostrar notificación de error
                this.showDateRangeError();
                
                // Limpiar los inputs
                fromDateInput.value = '';
                toDateInput.value = '';
                
                // Enviar fechas nulas para deshabilitar el botón de procesar
                window.updateDateRange(null, null);
            }
        }
    },

    showDateRangeError() {
        // Crear un elemento de notificación visible
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.textContent = 'La fecha final debe ser mayor o igual a la fecha inicial';
        
        document.body.appendChild(notification);
        
        // Eliminar la notificación después de 3 segundos
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    },

    formatDateISO(date) {
        const d = new Date(date);
        // Ajustar timezone a UTC
        d.setUTCHours(12, 0, 0, 0);
        return d.toISOString().split('T')[0];
    },

    formatDate(date) {
        // Asegurarnos de que la fecha se muestre correctamente
        const d = new Date(date);
        // Ajustar timezone a UTC para evitar problemas con la zona horaria
        d.setUTCHours(12, 0, 0, 0);
        
        return d.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    },

    getDates() {
        const today = new Date();
        console.log('🗓️ Calculando fechas desde:', today);
        
        // Obtener último día del mes actual
        const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        
        // Obtener último día del mes anterior
        const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
        
        // Último día del trimestre anterior
        const lastQuarterEnd = this.getLastQuarterEnd();
        
        // Último día del año anterior
        const lastYearEnd = new Date(today.getFullYear() - 1, 11, 31);
    
        const dates = {
            today: today,
            monthEnd: monthEnd,
            lastMonthEnd: lastMonthEnd,
            lastQuarterEnd: lastQuarterEnd,
            lastYearEnd: lastYearEnd
        };
    
        console.log('📅 Fechas calculadas:', {
            today: this.formatDate(dates.today),
            monthEnd: this.formatDate(dates.monthEnd),
            lastMonthEnd: this.formatDate(dates.lastMonthEnd),
            lastQuarterEnd: this.formatDate(dates.lastQuarterEnd),
            lastYearEnd: this.formatDate(dates.lastYearEnd)
        });
    
        return dates;
    },

    getLastQuarterEnd() {
        const today = new Date();
        const currentQuarter = Math.floor((today.getMonth() + 3) / 3);
        const yearOffset = currentQuarter === 1 ? -1 : 0;
        const lastQuarterMonth = currentQuarter === 1 ? 12 : (currentQuarter - 1) * 3;
        
        return new Date(today.getFullYear() + yearOffset, lastQuarterMonth, 0);
    },

    generatePeriodSelectorHTML() {
        const dates = this.getDates(); // Obtener las fechas relevantes
        return `
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Period
                </label>
                <select id="period-select" class="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                    <option value="no-date">A Range Date</option>
                    <option value="today">Today (${this.formatDate(dates.today)})</option>
                    <option value="month-end">End of this month (${this.formatDate(dates.monthEnd)})</option>
                    <option value="last-month">End of last month (${this.formatDate(dates.lastMonthEnd)})</option>
                    <option value="last-quarter">End of last quarter (${this.formatDate(dates.lastQuarterEnd)})</option>
                    <option value="last-year">End of last financial year (${this.formatDate(dates.lastYearEnd)})</option>
                    <option value="custom">Custom date</option>
                </select>
                <div id="custom-date" class="hidden mt-2 flex space-x-4 items-end">
                    <div class="flex flex-col">
                        <label class="text-sm mb-1">From</label>
                        <input id="custom-date-from" type="date" class="border rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white inline-block w-auto">
                    </div>
                    <div class="flex flex-col">
                        <label class="text-sm mb-1">To</label>
                        <input id="custom-date-to" type="date" class="border rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white inline-block w-auto">
                    </div>
                </div>
            </div>
        `;
    },

    updateDateRange(startDate, endDate) {
        // Validar fechas
        try {
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            if (isNaN(start.getTime()) || isNaN(end.getTime())) {
                throw new Error('Invalid date format');
            }
    
            // Llamar a la función global de cuadro_combinado.js
            window.updateDateRange(startDate, endDate);
            
            this.updateDateDisplay(startDate, endDate);
        } catch (error) {
            console.error('Error processing dates:', error);
        }
    },

    

    updateDateDisplay(startDate, endDate) {
        let display = document.getElementById('date-range-display');
        if (!display) {
            display = this.createDateDisplay();
        }
        
        // Crear nuevas instancias de Date y ajustar timezone
        const start = new Date(startDate);
        start.setUTCHours(12, 0, 0, 0);
        const end = new Date(endDate);
        end.setUTCHours(12, 0, 0, 0);
        
        display.textContent = `Rango seleccionado: ${this.formatDate(start)} - ${this.formatDate(end)}`;
    },

    createDateDisplay() {
        const display = document.createElement('div');
        display.id = 'date-range-display';
        display.className = 'text-sm text-gray-600 mt-2';
        
        const periodSelect = document.getElementById('period-select');
        if (periodSelect?.parentNode) {
            periodSelect.parentNode.insertBefore(display, periodSelect.nextSibling);
        }
        
        return display;
    }
};



// 2. Menú HTML (debe ir primero)
const menuHTML = `
   <div style="width: 96%; margin: 10 auto; border: 1px solid rgb(143, 144, 146); border-radius: 0.5rem; padding: 1rem; font-size:75%;">
       <!-- Organización Prestamista -->
       <div class="mb-4 pt-6">
           <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
               Organización Prestamista
           </label>
           <div class="relative">
               <input type="text" 
                   id="lender-org-search"
                   class="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                   placeholder="Buscar organización prestamista...">
               <div id="lender-search-results" 
                   class="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 shadow-xl rounded-lg max-h-96 overflow-y-auto hidden">
               </div>
           </div>
           <!-- Tabla de cuentas prestamista (aparece al seleccionar organización) -->
           <div id="lender-accounts-container" class="mt-4 hidden">
               <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                   Seleccione cuenta prestamista
               </h3>
               <div id="lender-accounts-list" 
                   class="max-h-60 overflow-y-auto border rounded-lg bg-white dark:bg-gray-800">
               </div>
               <div id="lender-selected-account" class="mt-2"></div>
           </div>
       </div>

       <!-- Organización Prestataria -->
       <div class="mb-4">
           <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
               Organización Prestataria
           </label>
           <div class="relative">
               <input type="text" 
                   id="borrower-org-search"
                   class="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                   placeholder="Buscar organización prestataria...">
               <div id="borrower-search-results" 
                   class="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 shadow-xl rounded-lg max-h-96 overflow-y-auto hidden">
               </div>
           </div>
           <!-- Tabla de cuentas prestataria (aparece al seleccionar organización) -->
           <div id="borrower-accounts-container" class="mt-4 hidden">
               <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                   Seleccione cuenta prestataria
               </h3>
               <div id="borrower-accounts-list" 
                   class="max-h-60 overflow-y-auto border rounded-lg bg-white dark:bg-gray-800">
               </div>
               <div id="borrower-selected-account" class="mt-2"></div>
           </div>
       </div>

       <!-- Period Selector -->
       ${dateRangeManager.generatePeriodSelectorHTML()}

       <!-- Hidden inputs para códigos de cuenta -->
       <input type="hidden" id="lender-account-code" value="">
       <input type="hidden" id="borrower-account-code" value="">

       <!-- Botón de Procesar -->
       <div id="process-button-container" class="mb-4 mt-8">
           <button id="processButton" 
                   class="w-full px-4 py-2 bg-gray-400 text-white rounded-lg cursor-not-allowed"
                   disabled>
               Seleccione organizaciones y cuentas
           </button>
       </div>
   </div>
`;


// ******************** FUNCIONES PARA MANEJAR CUENTAS **************** FUNCIONES PARA MANEJAR CUENTAS ******  FUNCIONES PARA MANEJAR CUENTAS
// Almacenamiento de planes contables
window.accountPlans = {
    organizations: new Map()
};

// Función para cargar el plan contable cuando se selecciona una organización
// Función para cargar y mostrar el plan contable
window.loadAccountPlan = async function(orgId, orgType) {
    alert("load Account Plan 😛");
    console.log(`====> ===> Loading account plan for ${orgType} organization:`, orgId);
    
    try {
        const url = `/auth/accounts/plan/${orgId}`;
        console.log('Requesting URL:', url);
        
        const response = await fetch(url);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server response:', response.status, errorText);
            throw new Error(`Error loading account plan: ${errorText}`);
        }
        
        const accountPlan = await response.json();
        console.log('Account plan received:', accountPlan);
        
        // Guardar en memoria
        window.accountPlans.organizations.set(orgId, accountPlan);
        
        // Mostrar en UI
        displayAccountPlan(orgId, orgType, accountPlan);
        
    } catch (error) {
        console.error('Error in loadAccountPlan:', error);
        throw error;
    }
};

async function loadAccounts(orgId, containerType) {
    console.log('📚 Cargando cuentas para:', {orgId, containerType});
    
    try {
        // Mostrar el contenedor antes de hacer el fetch
        const accountsContainer = document.getElementById(`${containerType}-accounts-container`);
        if (accountsContainer) {
            accountsContainer.classList.remove('hidden');
            console.log('📦 Contenedor de cuentas visible');
        }

        const response = await fetch(`/auth/accounts/${orgId}`);
        if (!response.ok) {
            console.error('❌ Error response:', response.status);
            throw new Error('Error al cargar cuentas');
        }
        
        const accounts = await response.json();
        console.log('✅ Cuentas recibidas:', accounts.length);
        
        displayAccounts(accounts, containerType);
        
    } catch (error) {
        console.error('❌ Error cargando cuentas:', error);
        showAccountsError(containerType);
    }
}
 
 // Función para mostrar cuentas en la tabla
 function displayAccounts(accounts, containerType) {
    console.log('🎯 displayAccounts llamado con:', { 
        accountsLength: accounts?.length, 
        containerType 
    });
    
    const listContainer = document.getElementById(`${containerType}-accounts-list`);
    console.log('📋 Container encontrado:', !!listContainer);
    
    if (!listContainer) {
        console.error('❌ No se encontró el contenedor:', `${containerType}-accounts-list`);
        return;
    }
    
    const hue = Math.floor(Math.random() * 360);
    const backgroundColor = `hsl(${hue}, 70%, 95%)`;
    
    listContainer.style.backgroundColor = backgroundColor;
    listContainer.style.transition = 'background-color 0.3s ease';
    
    if (!accounts || !accounts.length) {
        console.log('⚠️ No hay cuentas para mostrar');
        listContainer.innerHTML = '<div class="p-4 text-center text-gray-500">No se encontraron cuentas</div>';
        return;
    }
    
    try {
        listContainer.innerHTML = accounts.map(account => `
            <div class="account-row p-3 border-b cursor-pointer
                        hover:bg-gray-800 hover:text-amber-300"
                 onclick="window.selectAccount('${account.code}', '${account.name}', '${containerType}')"
                 data-code="${account.code}">
                <div class="flex justify-between items-center">
                    <span class="font-medium">${account.code}</span>
                    <span>${account.name}</span>
                </div>
            </div>
        `).join('');
        console.log('✅ Lista renderizada exitosamente');
    } catch (error) {
        console.error('❌ Error al renderizar lista:', error);
    }
}

 
window.selectAccount = function(code, name, containerType) {
    console.log('Cuenta seleccionada:', {code, name, containerType});
    
    if (containerType === 'lender' && window.selectedLender) {
        // Buscar si ya existe una tabla para este lender
        const existingTableId = `table-${window.selectedLender.id}`;
        const existingTable = document.querySelector(`[id^="${existingTableId}"]`);
        
        if (existingTable) {
            console.log('Tabla existente encontrada, actualizando código');
            // Solo actualizar el código
            window.selectedLender.accountCode = code;
            window.selectedLender.accountName = name;
            
            // Actualizar el código en todas las filas de la tabla existente
            const rows = existingTable.querySelectorAll('tbody tr:not(:last-child)');
            rows.forEach(row => {
                const accountCell = row.querySelector('td:nth-child(3)');
                if (accountCell) {
                    accountCell.textContent = code + " - " + name;
                }
            });
            
            // Ocultar lista de cuentas
            const listContainer = document.getElementById(`${containerType}-accounts-list`);
            if (listContainer) {
                listContainer.classList.add('hidden');
            }
            
            return; // No crear nueva tabla
        }
    }

    // Mostrar selección con botón para cambiar
    const selectedDiv = document.getElementById(`${containerType}-selected-account`);
    if (selectedDiv) {
        selectedDiv.innerHTML = `
            <div class="p-2 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-800">
                <div class="flex justify-between items-center">
                    <span class="font-medium text-blue-700 dark:text-blue-300">${code}</span>
                    <span class="text-blue-600 dark:text-blue-400">${name}</span>
                </div>
                <button onclick="window.showAccountsList('${containerType}')" 
                        class="w-full mt-2 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 
                            dark:hover:text-blue-300 text-left">
                    ↺ Cambiar cuenta seleccionada
                </button>
            </div>
        `;
    }

    // Ocultar lista de cuentas
    const listContainer = document.getElementById(`${containerType}-accounts-list`);
    if (listContainer) {
        listContainer.classList.add('hidden');
    }

    // Llamar al callback correspondiente (solo para nuevas tablas o borrowers)
    window.selectAccountCallback(code, name, `${containerType}-accounts-list`);
};

// Función separada para mostrar la lista
window.showAccountsList = function(containerType) {
    const listContainer = document.getElementById(`${containerType}-accounts-list`);
    if (listContainer) {
        listContainer.classList.remove('hidden');
    }
};
 
  
 // Función para mostrar error en la carga de cuentas
function showAccountsError(containerType) {
    const listContainer = document.getElementById(`${containerType}-accounts-list`);
    listContainer.innerHTML = `
        <div class="p-4 text-center text-red-500 dark:text-red-400">
            Error al cargar las cuentas. Intente nuevamente.
        </div>
    `;
 }

// Función para mostrar el plan contable
function displayAccountPlan(orgId, orgType, accountPlan) {
    console.log('🎯 Mostrando plan contable para:', orgType);
    console.log(`Displaying account plan for ${orgType}:`, accountPlan);
    
    const tableContainer = document.getElementById(`${orgType}-accounts-table`);
    const accountsList = document.getElementById(`${orgType}-accounts-list`);
    
    if (!tableContainer || !accountsList) {
        console.error('❌ No se encontró el contenedor para:', orgType);
        return;
    }
    
    accountsList.innerHTML = accountPlan.accounts.map(account => `
        <div class="account-row p-2 hover:bg-gray-50 cursor-pointer border-b"
             onclick="selectAccount('${orgType}', '${account.code}', '${account.name}')"
             title="${account.type || ''}">
            <div class="flex justify-between">
                <span class="font-medium">${account.code}</span>
                <span class="text-gray-600">${account.name}</span>
            </div>
        </div>
    `).join('');
    
    // Mostrar la tabla
    tableContainer.classList.remove('hidden');
    console.log('✅ Tabla visible, llenando datos...');
    
    // Configurar búsqueda
    setupAccountSearch(orgType);
}

// Configurar búsqueda local en la tabla de cuentas
function setupAccountSearch(orgType) {
    const searchInput = document.getElementById(`${orgType}-account-search`);
    const rows = document.querySelectorAll(`#${orgType}-accounts-list .account-row`);
    
    if (!searchInput) {
        console.error(`Search input not found for ${orgType}`);
        return;
    }
    
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        console.log(`Searching ${orgType} accounts for:`, searchTerm);
        
        rows.forEach(row => {
            const code = row.querySelector('.font-medium').textContent.toLowerCase();
            const name = row.querySelector('.text-gray-600').textContent.toLowerCase();
            
            const matches = code.includes(searchTerm) || name.includes(searchTerm);
            row.style.display = matches ? '' : 'none';
        });
    });
}

// Función para ordenar cuentas
window.sortAccounts = function(orgType, field) {
    console.log(`Sorting ${orgType} accounts by ${field}`);
    
    const container = document.getElementById(`${orgType}-accounts-list`);
    if (!container) {
        console.error(`Container not found for ${orgType}`);
        return;
    }
    
    const rows = Array.from(container.children);
    
    rows.sort((a, b) => {
        const aValue = field === 'code' ? 
            a.querySelector('.font-medium').textContent :
            a.querySelector('.text-gray-600').textContent;
            
        const bValue = field === 'code' ? 
            b.querySelector('.font-medium').textContent :
            b.querySelector('.text-gray-600').textContent;
        
        return aValue.localeCompare(bValue);
    });
    
    // Limpiar y reagregar elementos ordenados
    container.innerHTML = '';
    rows.forEach(row => container.appendChild(row));
};

// Función para seleccionar una cuenta
function selectAccount(code, name, isLender) {
    console.log('🎯 Cuenta seleccionada:', { code, name, isLender });
    
    // Actualizar input hidden correspondiente
    const orgType = isLender ? 'lender' : 'borrower';
    document.getElementById(`${orgType}-account-code`).value = code;
    
    // Actualizar UI
    const displayDiv = document.getElementById(`${orgType}-selected-account`);
    if (displayDiv) {
        displayDiv.innerHTML = `
            <div class="mt-2 p-2 bg-blue-50 dark:bg-blue-900 rounded">
                <span class="font-medium">${code}</span> - ${name}
            </div>
        `;
    }
    
    // Verificar si podemos habilitar el botón de procesar
    //checkEnableProcessButton();
}

/*
window.checkEnableProcessButton = function() {
    console.log('🔍 Verificando condiciones para habilitar botón');
    
    const processButton = document.getElementById('processButton');
    if (!processButton) {
        console.error(' Botón de proceso no encontrado');
        return;
    }

    // Verificar todas las condiciones necesarias
    const lenderAccount = document.getElementById('lender-account-code')?.value;
    const borrowerAccount = document.getElementById('borrower-account-code')?.value;
    const dateStart = window.dateRange?.start;
    const dateEnd = window.dateRange?.end;

    console.log(' Estado actual:', {
        lenderAccount,
        borrowerAccount,
        dateStart,
        dateEnd
    });

    const isValid = lenderAccount && 
                   borrowerAccount && 
                   dateStart && 
                   dateEnd;

    if (isValid) {
        processButton.disabled = false;
        processButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
        processButton.classList.add('bg-blue-600', 'hover:bg-blue-700');
        processButton.textContent = 'Procesar Saldos';
    } else {
        processButton.disabled = true;
        processButton.classList.add('bg-gray-400', 'cursor-not-allowed');
        processButton.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        processButton.textContent = getFeedbackMessage(
            lenderAccount, 
            borrowerAccount, 
            dateStart, 
            dateEnd
        );
    }
};
*/
function getFeedbackMessage(lenderAccount, borrowerAccount, dateStart, dateEnd) {
    if (!lenderAccount && !borrowerAccount) {
        return 'Seleccione cuentas de ambas organizaciones';
    }
    if (!lenderAccount) {
        return 'Seleccione cuenta prestamista';
    }
    if (!borrowerAccount) {
        return 'Seleccione cuenta prestataria';
    }
    if (!dateStart || !dateEnd) {
        return 'Seleccione rango de fechas';
    }
    return 'Seleccione todos los campos requeridos';
 }

 function getFeedbackMessage(lenderAccount, borrowerAccount, dateStart, dateEnd) {
    if (!lenderAccount) return 'Seleccione cuenta prestamista';
    if (!borrowerAccount) return 'Seleccione cuenta prestataria';
    if (!dateStart || !dateEnd) return 'Seleccione rango de fechas';
    return 'Seleccione todos los campos requeridos';
 }

// 3. tabSystem ************** // 3. tabSystem ************** // 3. tabSystem ***************** // 3. tabSystem
// Sistema de pestañas
const tabSystem = {
    state: {
        activeMainTab: 'balance',
        activeSubTab: null,
        quickMenuVisible: false
    },
 
    init() {
        console.log('Initializing tabSystem');
        this.setupTabListeners();
        this.setupQuickMenu();
        this.setupKeyboardShortcuts();
        dateRangeManager.init();
        
        // Asegurar que el menú esté creado antes de inicializar la búsqueda
        setTimeout(() => {
            initializeSearch();
        }, 100);
        this.setupCustomDateValidation();
    },

    setupTabListeners() {
        document.querySelectorAll('.primary-tabs button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevenir propagación
                this.switchMainTab(btn.dataset.tab);
            });
        });
    },

    switchMainTab(tabId) {
        /* Actualizar tab principal*/
        document.querySelectorAll('.primary-tabs button').forEach(btn => {
            if (btn.dataset.tab === tabId) {
                btn.className = "min-w-max px-4 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600";
            } else {
                btn.className = "min-w-max px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400";
            }
        });
     
        /* Actualizar subtabs y hacerlos visibles*/
        const subTabsContainer = document.querySelector('.secondary-tabs');
        subTabsContainer.style.display = 'flex';
        this.updateSubTabs(tabId);
     
        /* Actualizar visibilidad contenido*/
        this.switchContent(tabId);
     },
 
     /* Actualizar estilo de subtabs*/
   updateSubTabs(mainTab) {
    const subTabsConfig = {
        balance: ['Assets', 'Liabilities', 'Equity'],
        pl: ['Revenue', 'Expenses', 'Summary'],
        payroll: ['Employees', 'Payments', 'Reports']
    };

    const subTabsContainer = document.querySelector('.secondary-tabs');
    subTabsContainer.innerHTML = subTabsConfig[mainTab]
        .map(sub => `
            <button data-subtab="${sub.toLowerCase()}" 
                class="min-w-max px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400">
                ${sub}
            </button>
        `).join('');
    },

    setupQuickMenu() {
        console.log('Setting up quick menu');
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'menu-toggle fixed right-0 top-1/2 -translate-y-1/2 bg-blue-600 text-white p-2 rounded-l-lg shadow-lg z-40 transition-all duration-300';
        toggleBtn.innerHTML = '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>';
        toggleBtn.onclick = () => this.toggleQuickMenu();
    
        document.body.appendChild(toggleBtn);
        
        // Crear el menú
        const menu = document.createElement('div');
        menu.id = 'quick-menu';
        menu.className = 'fixed right-0 top-0 h-full w-[400px] bg-white dark:bg-gray-800 shadow-lg transform translate-x-full transition-transform duration-300 ease-in-out z-50';
        menu.innerHTML = menuHTML;
        document.body.appendChild(menu);
        //htmx.process(menu);
        // Cargar organizaciones al storage
        //loadOrganizationsToStorage();
    
        console.log('Quick menu setup complete');
    },

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            console.log('Key pressed:', e.key, 'Alt:', e.altKey);
            if (e.key === 'F2') {
                e.preventDefault();
                this.toggleQuickMenu();
            } else if (e.altKey && /^[1-3]$/.test(e.key)) {
                e.preventDefault();
                const tabs = ['balance', 'pl', 'payroll'];
                this.switchMainTab(tabs[e.key - 1]);
            }
        });
    },

    switchContent(tabId) {
        const panes = document.querySelectorAll('.tab-pane');
        panes.forEach(pane => {
            pane.classList.toggle('hidden', pane.id !== `${tabId}-content`);
        });
    },

    toggleQuickMenu() {
        const menu = document.getElementById('quick-menu');
        const toggleBtn = document.querySelector('.menu-toggle');
        
        if (menu && toggleBtn) {
            const isVisible = !menu.classList.contains('translate-x-full');
            
            // Manejar menú
            if (isVisible) {
                menu.classList.add('translate-x-full');
                menu.classList.remove('translate-x-0');
            } else {
                menu.classList.remove('translate-x-full');
                menu.classList.add('translate-x-0');
            }
            
            // Manejar botón
            toggleBtn.style.right = isVisible ? '0' : '400px';
            toggleBtn.style.display = 'block'; // Asegurar que el botón siempre sea visible
            toggleBtn.style.zIndex = '9999';   // Asegurar que esté por encima
        }
    },

    setupCustomDateValidation() {
        const fromInput = document.getElementById('custom-date-from');
        const toInput = document.getElementById('custom-date-to');
    
        function validateAndUpdateDates() {
            const fromDate = fromInput.value;
            const toDate = toInput.value;
    
            // Solo actualizar si ambas fechas existen
            if (fromDate && toDate) {
                if (fromDate > toDate) {
                    alert('Start date must be less than or equal to end date');
                    return false;
                }
                // Actualizar fechas en las tablas
                window.updateDateRange(fromDate, toDate);
                return true;
            }
            return false;
        }
    
        // Manejar cambios en ambos inputs
        fromInput.addEventListener('change', function() {
            if (this.value) {
                toInput.min = this.value; // Establecer fecha mínima en "To"
                validateAndUpdateDates();
            }
        });
    
        toInput.addEventListener('change', function() {
            if (this.value) {
                fromInput.max = this.value; // Establecer fecha máxima en "From"
                validateAndUpdateDates();
            }
        });
    }
};


// 4. Variables y funciones globales *************** // 4. Variables y funciones globales ************* // 4. Variables y funciones globales
// Estado global
window.selectedOrgs = {
    lender: null,
    borrower: null,
    lenderAccount: null,
    borrowerAccount: null
};

window.dateRange = {
    start: null,
    end: null
};

window.updateDateRange = function(startDate, endDate) {
    console.log('Updating dates:', startDate, endDate);
    window.dateRange = {
        start: startDate,
        end: endDate
    };

    // Verificar estado del botón para todas las tablas existentes
    const tables = document.querySelectorAll('[id^="table-"]');
    tables.forEach(table => {
        window.tablesManager.checkProcessButtonStatus(table.id);
    });
};



// Funciones de selección globales *************// Funciones de selección globales // // Funciones de selección globales
// Al inicio del archivo, antes de cualquier otra función
// 3. En window.selectLenderOrg
/*
window.selectLenderOrg = function(id, name) {
    console.log(' Lender seleccionado:', {id, name});
    window.selectedLender = {
        id: id,
        name: name,
        accountCode: null
    };
    // Actualizar UI
    document.getElementById('lender-org-search').value = name;
    document.getElementById('lender-search-results').classList.add('hidden');
};
*/

window.selectBorrowerOrg = function(id, name) {
    console.log('🎯 Borrower seleccionado:', {id, name});
    try {
        // Verificar si hay una tabla activa
        const currentTableId = window.currentLendingTableId;
        if (!currentTableId) {
            console.error('❌ No hay tabla activa para agregar borrower');
            return;
        }

        // Obtener last_sync del sessionStorage
        const organizations = JSON.parse(sessionStorage.getItem('organizations') || '[]');
        const org = organizations.find(org => org.id === id);
        const lastSync = org ? org.last_sync : new Date().toISOString();

        // Crear objeto con datos del borrower
        const borrowerData = {
            id: id,
            name: name,
            accountCode: null,
            accountName: null,
            lastSync: lastSync
        };

        // Ocultar resultados de búsqueda y menú
        document.getElementById('borrower-org-search').value = "";
        document.getElementById('borrower-search-results').classList.add('hidden');

        // Agregar a la tabla usando tablesManager
        window.tablesManager.addBorrowerToTable(currentTableId, borrowerData);
        
        //window.lendingUI.hideQuickMenu();
    } catch (error) {
        console.error('❌ Error en selectBorrowerOrg:', error);
    }
};


window.selectBorrowerAccount = function(code, name) {
    // Se implementará cuando tengamos la tabla creada
};


/*
window.updateTable = function() {
    console.log('Updating table with:', window.selectedOrgs);
    const resultsDiv = document.querySelector('.results-combinado');
    
    if (!resultsDiv) {
        console.error('Results div not found');
        return;
    }

    const hasValidSelection = window.selectedOrgs.lender && 
                            window.selectedOrgs.borrower && 
                            window.selectedOrgs.lenderAccount && 
                            window.selectedOrgs.borrowerAccount;

    const tableHTML = `
        <div class="table-header mb-4">
            <h2>${getTableTitle()}</h2>
        </div>
        <table class="min-w-full border dark:border-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                    <th class="p-3 text-left">Organización</th>
                    <th class="p-3 text-left">Cuenta</th>
                    <th class="p-3 text-left">Saldo</th>
                </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900">
                <tr class="lender-row border-b dark:border-gray-700">
                    <td class="p-3">${window.selectedOrgs.lender?.name || ''}</td>
                    <td class="p-3" title="${window.selectedOrgs.lenderAccount?.name || ''}">
                        ${window.selectedOrgs.lenderAccount?.id || ''}
                    </td>
                    <td class="p-3 balance-cell" data-type="lender" 
                        data-org="${window.selectedOrgs.lender?.id || ''}" 
                        data-account="${window.selectedOrgs.lenderAccount?.id || ''}">
                    </td>
                </tr>
                <tr class="borrower-row">
                    <td class="p-3">${window.selectedOrgs.borrower?.name || ''}</td>
                    <td class="p-3" title="${window.selectedOrgs.borrowerAccount?.name || ''}">
                        ${window.selectedOrgs.borrowerAccount?.id || ''}
                    </td>
                    <td class="p-3 balance-cell" data-type="borrower"
                        data-org="${window.selectedOrgs.borrower?.id || ''}" 
                        data-account="${window.selectedOrgs.borrowerAccount?.id || ''}">
                    </td>
                </tr>
            </tbody>
        </table>
        <button id="processButton" 
                class="mt-4 px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
                ${(!hasValidSelection || !window.dateRange?.start || !window.dateRange?.end) ? 'disabled' : ''}>
            Procesar Saldos
        </button>
    `;

    resultsDiv.innerHTML = hasValidSelection ? tableHTML : 
        '<p class="text-gray-500">Seleccione organizaciones y cuentas...</p>';

    if (hasValidSelection) {
        window.updateProcessButton();
    }
};
*/

// También necesitamos hacer global getTableTitle
window.getTableTitle = function() {
    let title = 'Saldos entre Organizaciones';
    if (window.dateRange?.start && window.dateRange?.end) {
        title += ` (${window.dateRange.start} - ${window.dateRange.end})`;
    }
    return title;
};


// En tabs.js
/*
window.selectLenderAccount = function(code, name) {
    console.log(' selectLenderAccount llamado:', {code, name});
    try {
        if (!window.selectedLender) {
            console.error(' No hay lender seleccionado');
            return;
        }
        
        // Actualizar código de cuenta
        window.selectedLender.accountCode = code;
        
        // Crear tabla
        console.log('Creando tabla para:', window.selectedLender);
        window.tablesManager.createTable(
            window.selectedLender.id, 
            window.selectedLender.name, 
            code
        );
    } catch (error) {
        console.error(' Error en selectLenderAccount:', error);
    }
};
*/

// En tabs.js, actualizar selectAccountCallback
// 4. En window.selectAccountCallback
window.selectAccountCallback = function(code, name, resultsId) {
    console.log('Account selected:', {code, name, resultsId});
    
    if (resultsId.includes('lender')) {
        console.log('Lender account selected, calling selectLenderAccount');
        window.selectLenderAccount(code, name);
    } else if (resultsId.includes('borrower')) {
        window.selectBorrowerAccount(code, name);
    }
    
    // Ocultar resultados
    document.getElementById(resultsId)?.classList.add('hidden');
};

// 5. Funciones de búsqueda y actualización **************** Funciones de búsqueda y actualización ************ Funciones de búsqueda y actualización
function initializeSearch() {
    console.log('🔍 Initializing search functionality');
    
    // Prestamista
    setupOrgSearch('lender-org-search', 'lender-search-results', (id, name) => {
        console.log('🎯 Callback del prestamista', {id, name});
        
        try {
            // Guardar lender
            window.selectedLender = {
                id: id,
                name: name,
                accountCode: null
            };
            console.log('✅ Lender guardado:', window.selectedLender);

            // Cargar cuentas del lender
            loadAccounts(id, 'lender');
        } catch (error) {
            console.error('❌ Error:', error);
        }
    });

    // Prestatario (mantener como está)
    setupOrgSearch('borrower-org-search', 'borrower-search-results', (id, name) => {
        alert('🎯 Callback del prestatario');
        console.log('🎯 Borrower ID:', id);
        console.log('🎯 Borrower Name:', name);
        
        try {
            alert('⏳ Intentando llamar a selectBorrowerOrg');
            window.selectBorrowerOrg(id, name);
            alert('✅ selectBorrowerOrg ejecutado');
        } catch (error) {
            alert('❌ Error: ' + error.message);
            console.error('❌ Error completo:', error);
        }
    });
}

// Funciones para búsqueda y selección de organizaciones
// Función original que sabemos que funciona
// Funciones para búsqueda y selección de organizaciones
function setupOrgSearch(inputId, resultsId, selectCallback) {
    console.log('🔍 setupOrgSearch llamado con:', { inputId, resultsId });
    const searchInput = document.getElementById(inputId);
    const searchResults = document.getElementById(resultsId);
    
    if (!searchInput || !searchResults) {
        console.error('❌ Elementos no encontrados');
        return;
    }

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        if (query.length < 3) {
            searchResults.classList.add('hidden');
            return;
        }

        // Buscar en sessionStorage
        const organizations = JSON.parse(sessionStorage.getItem('organizations') || '[]');
        const filtered = organizations.filter(org => 
            org.name.toLowerCase().includes(query.toLowerCase())
        );

        displayOrgResults(filtered, searchResults, selectCallback);
    });
}

// Para la búsqueda de prestatario, reutilizamos el mismo patrón
function setupBorrowerSearch() {
    const searchInput = document.getElementById('borrower-org-search');
    const searchResults = document.getElementById('borrower-search-results');
    
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length < 3) {
            searchResults.classList.add('hidden');
            return;
        }
 
        const organizations = JSON.parse(sessionStorage.getItem('organizations') || '[]');
        const filtered = organizations.filter(org => 
            org.name.toLowerCase().includes(query.toLowerCase())
        );
 
        displayOrgResults(filtered, searchResults, 'borrower');
    });
 }
 
 
// 1. En tabs.js, mantener la función window.selectOrganization
window.selectOrganization = async function(orgId, orgName, resultsId) {
    console.log('🎯 selectOrganization llamado:', {orgId, orgName, resultsId});
    
    if (resultsId.includes('lender')) {
        window.selectLenderOrg(orgId, orgName);
        // Cargar cuentas después de seleccionar
        //loadAccounts(orgId, 'lender');
    } else if (resultsId.includes('borrower')) {
        window.selectBorrowerOrg(orgId, orgName);
    }
};

// 2. En displayOrgResults, volver a la versión original
function displayOrgResults(organizations, resultsDiv, selectCallback) {
    console.log('📋 Mostrando resultados:', organizations.length);
    
    if (!organizations.length) {
        resultsDiv.innerHTML = '<div class="p-4 text-gray-500">No se encontraron organizaciones</div>';
    } else {
        resultsDiv.innerHTML = organizations.map(org => `
            <div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b"
                 onclick="selectOrganization('${org.id}', '${org.name}', '${resultsDiv.id}')"
                 role="button">
                <p class="font-medium text-gray-900 dark:text-white">${org.name}</p>
            </div>
        `).join('');
    }
    
    resultsDiv.classList.remove('hidden');
}


function setupAccountSearch(inputId, resultsId, selectCallback) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    
    if (!input || !results) return;

    input.addEventListener('input', function() {
        const query = this.value.trim();
        
        if (query.length < 3) {
            results.classList.add('hidden');
            return;
        }

        fetch(`/auth/codigo?q=${query}`)
            .then(response => response.text())
            .then(html => {
                results.innerHTML = html;
                results.classList.remove('hidden');
            });
    });
}

async function loadOrganizationsToStorage() {
    try {
        console.log('Loading organizations to storage');
        const response = await fetch('/api/organizations/list', {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Failed to load organizations');
        
        const data = await response.json();
        sessionStorage.setItem('organizations', JSON.stringify(data.organizations));
        console.log('Organizations loaded to storage:', data.organizations);
    } catch (error) {
        console.error('Error loading organizations:', error);
    }
}


const style = document.createElement('style');
style.textContent = `
    .tab-active {
        @apply text-primary-600 border-b-2 border-primary-600;
    }

    .tab-pane {
        @apply p-4 text-gray-900 dark:text-white;
    }

    #quick-menu {
        @apply fixed right-0 top-0 h-full w-64 bg-white dark:bg-gray-800 shadow-lg transform translate-x-full transition-transform z-50;
    }

    #quick-menu.visible {
        @apply translate-x-0;
    }
`;
document.head.appendChild(style);


// 5. Al final, la inicialización
document.addEventListener('DOMContentLoaded', () => {
    tabSystem.init();
    //initializeSearch(); // Añadir esta línea
});