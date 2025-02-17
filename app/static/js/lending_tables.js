// Definir la clase como propiedad de window
window.LendingTablesManager = class {
    constructor() {
        this.tables = new Map();
        this.colorSchemes = [
            { 
                header: 'bg-blue-50 border-blue-200', 
                row: 'hover:bg-blue-50',
                title: 'text-blue-800'
            },
            { 
                header: 'bg-emerald-50 border-emerald-200', 
                row: 'hover:bg-emerald-50',
                title: 'text-emerald-800'
            },
            { 
                header: 'bg-amber-50 border-amber-200', 
                row: 'hover:bg-amber-50',
                title: 'text-amber-800'
            },
            { 
                header: 'bg-violet-50 border-violet-200', 
                row: 'hover:bg-violet-50',
                title: 'text-violet-800'
            }
        ];
        this.currentColorIndex = 0;
        this.containerId = 'lending-tables-container';
        this.initializeContainer();

        // Agregar estilos para animaciones
        const style = document.createElement('style');
        style.textContent = `
            .table-content {
                transition: max-height 0.3s ease-out;
                overflow: hidden;
            }
        `;
        document.head.appendChild(style);
    }

    // En lending_tables.js, modifica initializeContainer
    initializeContainer() {
        console.log('🔍 Buscando contenedor .results-combinado');
        const resultsDiv = document.querySelector('.results-combinado');
        console.log('📍 Contenedor encontrado:', resultsDiv);

        const existingContainer = document.getElementById(this.containerId);
        if (!existingContainer) {
            const container = document.createElement('div');
            container.id = this.containerId;
            container.className = 'space-y-6 overflow-auto px-4';
            resultsDiv.appendChild(container);
            console.log('✅ Nuevo contenedor creado:', this.containerId);
        }
    }

    createTable(lenderId, lenderName, accountCode) {
        console.log('📊 Creando tabla para:', {lenderId, lenderName});
        
        const tableId = `table-${lenderId}-${Date.now()}`;
        window.currentLendingTableId = tableId; // Agregar esta línea
        const colorScheme = this.getNextColorScheme();
        
        // Crear estructura base de la tabla
        const tableHtml = this.generateTableHtml(tableId, lenderName, colorScheme);
        console.log('🎨 HTML generado:', tableHtml);
        
        // Agregar al contenedor
        const container = document.getElementById(this.containerId);
        console.log('📦 Container para tabla:', container);
        container.insertAdjacentHTML('beforeend', tableHtml);
        
        // Guardar referencia
        this.tables.set(tableId, {
            id: tableId,
            lenderId,
            lenderName,
            colorScheme,
            borrowers: new Set()
        });

        // Configurar event listeners
        this.setupTableListeners(tableId);
        
        return tableId;
    }

    generateTableHtml(tableId, lenderName, colorScheme) {
        return `
            <div id="${tableId}" class="bg-white rounded-lg shadow-md">
                <!-- Header con menú -->
                <div class="flex items-center justify-between p-4 ${colorScheme.header} border-b">
                    <div class="flex items-center gap-2">
                        <button class="text-red-500 hover:text-red-700 px-2 delete-table">🗑️</button>
                        <h2 class="text-lg font-semibold ml-2 ${colorScheme.title}">
                            ${lenderName} (Select date range)
                        </h2>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="window.tablesManager.processTableBalances('${tableId}')"
                                id="process-${tableId}"
                                class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed">
                            PROCESS BALANCE
                        </button>
                        <button class="text-gray-500 hover:text-gray-700 px-2 toggle-table">▼</button>
                        <div class="relative">
                            <button class="text-gray-500 hover:text-gray-700 px-2" 
                                    onclick="window.tablesManager.toggleTableMenu('${tableId}')">⋮</button>
                            <div id="menu-${tableId}" 
                                 class="absolute right-0 mt-2 py-2 w-48 bg-white rounded-lg shadow-xl hidden">
                                <a href="#" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">
                                    Compartir tabla
                                </a>
                                <a href="#" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">
                                    Descargar CSV
                                </a>
                                <a href="#" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">
                                    Copiar
                                </a>
                                <a href="#" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">
                                    Imprimir
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
    
                <!-- Table Content -->
                <div class="table-content" style="overflow: visible;">
                    <table class="w-full">
                        <thead>
                            <tr class="${colorScheme.header}">
                                <th class="p-2 text-left"></th> <!-- Columna para el botón eliminar -->
                                <th class="p-2 text-left">Last Sync</th>
                                <th class="p-2 text-left">Account</th>
                                <th class="p-2 text-right">LENT</th>
                                <th class="p-2 text-left">BORROWER</th>
                                <th class="p-2 text-left">Account</th>
                                <th class="p-2 text-right">PAID</th>
                                <th class="p-2 text-right">BALANCE</th>
                                <th class="p-2 text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td colspan="9">
                                    <button class="w-full py-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 add-borrower">
                                        + Borrower
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    setupTableListeners(tableId) {
        const tableElement = document.getElementById(tableId);
        if (!tableElement) return;

        // Delete table
        tableElement.querySelector('.delete-table').onclick = () => this.deleteTable(tableId);

        // Toggle expand/collapse
        tableElement.querySelector('.toggle-table').onclick = () => this.toggleTable(tableId);

        // Add borrower
        tableElement.querySelector('.add-borrower').onclick = () => this.triggerBorrowerSearch(tableId);
    }

    // Continuando en lending_tables.js, después de setupTableListeners

    deleteTable(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;
    
        // Crear modal de confirmación
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 shadow-xl max-w-md w-full mx-4">
                <h3 class="text-lg font-semibold mb-4">Delete Table</h3>
                <p class="text-gray-600 mb-6">
                    Are you sure you want to delete this table? This action cannot be undone.
                </p>
                <div class="flex justify-end space-x-4">
                    <button class="px-4 py-2 text-gray-600 hover:text-gray-800" id="cancel-delete">
                        Cancel
                    </button>
                    <button class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600" id="confirm-delete">
                        Delete
                    </button>
                </div>
            </div>
        `;
    
        document.body.appendChild(modal);
    
        // Event listeners para el modal
        document.getElementById('cancel-delete').onclick = () => {
            modal.remove();
        };
    
        document.getElementById('confirm-delete').onclick = () => {
            table.remove();
            this.tables.delete(tableId);
            modal.remove();
        };
    }
    
    toggleTable(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;
    
        const content = table.querySelector('.table-content');
        const toggleBtn = table.querySelector('.toggle-table');
        
        if (content.style.display === 'none') {
            // Expandir
            content.style.display = '';
            toggleBtn.textContent = '▼';
            content.style.maxHeight = content.scrollHeight + 'px';
        } else {
            // Colapsar
            content.style.maxHeight = '0px';
            setTimeout(() => {
                content.style.display = 'none';
                toggleBtn.textContent = '▲';
            }, 300);
        }
    }
    
    triggerBorrowerSearch(tableId) {
        console.log('🔍 ==> Activating search for table:', tableId);
        
        const table = this.tables.get(tableId);
        if (!table) {
            console.error('❌ Table not found');
            return;
        }
    
        // Guardar referencia a la tabla activa
        window.currentLendingTableId = tableId;
    
        // Mostrar QuickMenu
        const quickMenu = document.getElementById('quick-menu');
        if (quickMenu) {
            // Actualizar label con el contexto y el estilo de la tabla actual
            const label = quickMenu.querySelector('label');
            if (label) {
                label.textContent = `Add borrower to: ${table.lenderName}`;
                label.className = `block text-sm font-medium mb-2 p-2 ${table.colorScheme.header} ${table.colorScheme.title}`;
            }
    
            // Limpiar y ocultar resultados previos
            const resultsDiv = quickMenu.querySelector('#borrower-search-results');
            if (resultsDiv) {
                resultsDiv.innerHTML = '';
                resultsDiv.classList.add('hidden');
            }
    
            // Limpiar input de búsqueda
            const searchInput = quickMenu.querySelector('#borrower-org-search');
            if (searchInput) {
                searchInput.value = '';
                searchInput.focus();
            }
    
            // Mostrar el menú
            quickMenu.classList.remove('translate-x-full');
            // Asegurar que el botón permanezca visible
            const toggleBtn = document.querySelector('.menu-toggle');
            if (toggleBtn) {
                toggleBtn.style.right = '400px';
                toggleBtn.style.display = 'block';
                toggleBtn.style.zIndex = '9999';
            }
        }
    }

    // En lending_tables.js, después de triggerBorrowerSearch
    addBorrowerToTable(tableId, borrowerData) {
        console.log('👥 Agregando borrower a tabla:', {tableId, borrowerData});
        
        console.log('👥 Agregando borrower a tabla:', {
            tableId, 
            borrowerData,
            selectedLender: window.selectedLender  // Agregar log del lender
        });

        // Obtener datos del lender actuales
        const lenderCode = window.selectedLender?.accountCode;
        const lenderName = window.selectedLender?.accountName;

        const table = this.tables.get(tableId);
        if (!table) {
            console.error('❌ Tabla no encontrada:', tableId);
            return;
        }
     
        const tableElement = document.getElementById(tableId);
        const tbody = tableElement.querySelector('tbody');
        if (!tbody) return;
     
        // Obtener número de fila (excluyendo la fila del botón Add Borrower)
        const rowNumber = tbody.querySelectorAll('tr:not(:last-child)').length + 1;
     
        // Generar IDs únicos para los inputs y contenedores de resultados
        const lenderSearchId = `${tableId}-lender-${rowNumber}`;
        const lenderResultsId = `${tableId}-lender-results-${rowNumber}`;
        const borrowerSearchId = `${tableId}-borrower-${rowNumber}`;
        const borrowerResultsId = `${tableId}-borrower-results-${rowNumber}`;
     
        // Insertar fila antes del botón "Add Borrower"
        const newRow = document.createElement('tr');
        newRow.className = `${table.colorScheme.row} border-b`;
        newRow.dataset.borrowerId = borrowerData.id;
        newRow.dataset.rowNumber = rowNumber;
        
        newRow.innerHTML = `
            <td class="p-2 text-center">
                <button onclick="window.tablesManager.removeBorrower('${tableId}', '${borrowerData.id}')"
                        class="text-red-500 hover:text-red-700">🗑️</button>
            </td>
            <td class="p-2 text-sm">${this.formatTimeElapsed(borrowerData.lastSync)}</td>
            <td class="p-2 text-sm relative">
                <input type="text" 
                    id="${lenderSearchId}"
                    data-type="lender"
                    data-row="${rowNumber}"
                    class="w-full p-1 border rounded text-sm"
                    placeholder="Buscar cuenta prestamista..."
                    value="${lenderCode ? `${lenderCode} - ${lenderName}` : ''}"
                />
                <div id="${lenderResultsId}" 
                    class="absolute z-[1000] w-full bg-white border rounded-lg shadow-lg mt-1 hidden max-h-48 overflow-y-auto"
                    style="width: inherit; max-height: 200px; overflow-y: auto;">
                </div>
            </td>
            <td class="p-2 text-right text-sm"></td>
            <td class="p-2 text-sm">${borrowerData.name}</td>
            <td class="p-2 text-sm relative">
                <input type="text" 
                    id="${borrowerSearchId}"
                    data-type="borrower"
                    data-row="${rowNumber}"
                    class="w-full p-1 border rounded text-sm"
                    placeholder="Buscar cuenta prestatario..."
                />
                <div id="${borrowerResultsId}" 
                    class="absolute z-[1000] w-full bg-white border rounded-lg shadow-lg mt-1 hidden max-h-48 overflow-y-auto"
                    style="width: inherit; max-height: 200px; overflow-y: auto;">
                </div>
            </td>
            <td class="p-2 text-right text-sm"></td>
            <td class="p-2 text-right text-sm"></td>
            <td class="p-2 text-center">--</td>
        `;
     
        // Insertar antes del último tr (que contiene el botón Add Borrower)
        const lastRow = tbody.lastElementChild;
        tbody.insertBefore(newRow, lastRow);
     
        // Configurar la búsqueda para ambos inputs
        this.setupAccountSearch(lenderSearchId, lenderResultsId, borrowerData.id, 'lender');
        this.setupAccountSearch(borrowerSearchId, borrowerResultsId, borrowerData.id, 'borrower');
     
        // Actualizar el registro de borrowers
        table.borrowers.add(borrowerData.id);

        // Al final de la función
        this.checkProcessButtonStatus(tableId);
     }

    removeBorrower(tableId, borrowerId) {
        console.log('🗑️ Removiendo borrower:', {tableId, borrowerId});
        
        // 1. Obtener referencia a la tabla
        const table = this.tables.get(tableId);
        if (!table) {
            console.error('❌ Tabla no encontrada:', tableId);
            return;
        }
    
        // 2. Encontrar y eliminar la fila del DOM
        const row = document.querySelector(`#${tableId} tr[data-borrower-id="${borrowerId}"]`);
        if (row) {
            row.remove();
        }
    
        // 3. Eliminar del Set de borrowers
        table.borrowers.delete(borrowerId);
        
        console.log('✅ Borrower eliminado correctamente');

        // Verificar estado del botón después de eliminar
        this.checkProcessButtonStatus(tableId);
    }

    setupAccountSearch(inputId, resultsId, entityId, type) {
        const searchInput = document.getElementById(inputId);
        const resultsDiv = document.getElementById(resultsId);
        
        searchInput.addEventListener('input', async function() {
            const query = this.value.trim();
            
            if (query.length < 3) {
                resultsDiv.classList.add('hidden');
                // Restaurar scroll cuando se oculta
                document.body.style.overflow = 'auto';
                return;
            }
    
            try {
                // Cargar cuentas según el tipo
                const response = await fetch(`/auth/accounts/${type === 'lender' ? window.selectedLender.id : entityId}`);
                if (!response.ok) throw new Error('Error cargando cuentas');
                
                const accounts = await response.json();
                const filtered = accounts.filter(account => 
                    account.code.toLowerCase().includes(query.toLowerCase()) ||
                    account.name.toLowerCase().includes(query.toLowerCase())
                );

                resultsDiv.innerHTML = filtered.map(account => `
                    <div class="p-2 hover:bg-gray-50 cursor-pointer border-b text-sm"
                         onclick="window.tablesManager.selectAccountForRow('${inputId}', '${account.code}', '${account.name}', '${type}')">
                        ${account.code} - ${account.name}
                    </div>
                `).join('');
                
                resultsDiv.classList.remove('hidden');

                // Prevenir scroll cuando se muestra la lista
                document.body.style.overflow = 'hidden'; // Prevenir Scroll

            } catch (error) {
                console.error('Error en búsqueda:', error);
            }
        });

        // Seleccionar todo el texto al recibir foco
        searchInput.addEventListener('focus', function() {
            this.select();
        });
    
        // Cerrar resultados al hacer click fuera
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
                resultsDiv.classList.add('hidden');
                document.body.style.overflow = 'auto';  // Restaurar scroll
            }
        });

        searchInput.addEventListener('change', () => {
            const tableElement = searchInput.closest(`[id^="table-"]`);
            if (tableElement) {
                this.checkProcessButtonStatus(tableElement.id);
            }
        });
    }

    selectAccountForBorrower(borrowerId, code, name) {
        console.log('💼 Seleccionando cuenta para borrower:', {borrowerId, code, name});
        
        try {
            // Encontrar la fila del borrower en cualquier tabla
            const borrowerRow = document.querySelector(`tr[data-borrower-id="${borrowerId}"]`);
            if (!borrowerRow) {
                console.error('❌ Fila de borrower no encontrada');
                return;
            }
    
            // Actualizar la celda de Account con el código seleccionado
            const accountCell = borrowerRow.querySelector('td:nth-child(6)'); // La columna Account del borrower
            if (accountCell) {
                // Mantener el input pero actualizar su valor
                const searchInput = accountCell.querySelector('input');
                if (searchInput) {
                    searchInput.value = `${code} - ${name}`;
                }
                
                // Ocultar resultados
                const resultsDiv = accountCell.querySelector('div[id^="account-results"]');
                if (resultsDiv) {
                    resultsDiv.classList.add('hidden');
                }
            }
    
            // Actualizar el registro en this.tables
            for (const [tableId, table] of this.tables.entries()) {
                if (table.borrowers.has(borrowerId)) {
                    console.log('✅ Cuenta actualizada en tabla:', tableId);
                }
            }
        } catch (error) {
            console.error('❌ Error al seleccionar cuenta:', error);
        }
    }

    // Nuevo método
    formatTimeElapsed(lastSync) {
        const now = new Date();
        const syncDate = new Date(lastSync);
        const diff = Math.floor((now - syncDate) / 1000); // diferencia en segundos

        if (diff < 60) return '-1 minute ago'; // Clarificamos que son segundos
        if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
        return `${Math.floor(diff / 86400)} days ago`;
    }

    toggleTableMenu(tableId) {
        const menu = document.getElementById(`menu-${tableId}`);
        if (menu) {
            menu.classList.toggle('hidden');
        }
    }

    selectAccountForRow(inputId, code, name, type) {
        const input = document.getElementById(inputId);
        if (!input) return;
    
        // Actualizar valor del input
        input.value = `${code} - ${name}`;
        
        // Ocultar resultados
        const resultsDiv = input.parentElement.querySelector('div[id*="results"]');
        if (resultsDiv) {
            resultsDiv.classList.add('hidden');
        }
    
        // Marcar que la fila necesita actualizar saldos
        const row = input.closest('tr');
        if (row) {
            row.classList.add('needs-update');
        }
    
        // Mostrar el botón de procesar saldos de la tabla
        const table = input.closest(`[id^="table-"]`);
        // Verificar estado del botón
        const tableElement = input.closest(`[id^="table-"]`);
        if (tableElement) {
            this.checkProcessButtonStatus(tableElement.id);
        }
        if (table) {
            const processButton = document.getElementById(`process-${table.id}`);
            if (processButton) {
                processButton.classList.remove('hidden');
            }
        }
    }

    checkProcessButtonStatus(tableId) {
        // Asegurar que usamos el ID base de la tabla
        const baseTableId = tableId.split('-lender')[0].split('-borrower')[0];
        console.log('🔄 Checking process button status for base table:', baseTableId);
        
        const processButton = document.getElementById(`process-${baseTableId}`);
        if (!processButton) {
            console.error('❌ Process button not found:', `process-${baseTableId}`);
            return;
        }
    
        // Usar checkTableReadiness con el ID base
        const isTableReady = this.checkTableReadiness(baseTableId);
        
        // Actualizar estado del botón
        processButton.disabled = !isTableReady;
        
        // Actualizar estilo visual según estado
        if (isTableReady) {
            processButton.classList.remove('opacity-50', 'cursor-not-allowed');
            processButton.classList.add('hover:bg-blue-600');
        } else {
            processButton.classList.add('opacity-50', 'cursor-not-allowed');
            processButton.classList.remove('hover:bg-blue-600');
        }
    
        console.log('🔄 Button status updated:', { 
            baseTableId, 
            isEnabled: isTableReady,
            buttonFound: !!processButton
        });
        
    }
    
    async processBalances(tableId) {
        const table = this.tables.get(tableId);
        if (!table) return;
    
        // Por cada fila
        const rows = document.querySelectorAll(`#${tableId} tr[data-borrower-id]`);
        for (const row of rows) {
            // Obtener códigos de cuenta
            const lenderCode = window.selectedLender.accountCode;
            const borrowerCode = ''; // Obtener de la fila
    
            // Obtener saldos
            await this.fetchAndUpdateBalances(row, lenderCode, borrowerCode);
        }
    }

    checkTableReadiness(tableId) {
        console.log('📊 Checking table readiness:', tableId);
        
        // 1. Verificar que la tabla existe
        const table = this.tables.get(tableId);
        if (!table) {
            console.error('❌ Table not found:', tableId);
            return false;
        }
     
        // 2. Verificar rango de fechas
        const hasDateRange = window.dateRange && 
                            window.dateRange.start && 
                            window.dateRange.end;
        console.log('📅 Date Range:', {
            exists: !!window.dateRange,
            start: window.dateRange?.start,
            end: window.dateRange?.end,
            hasAll: hasDateRange
        });
     
        if (!hasDateRange) {
            console.log('❌ Missing date range');
            return false;
        }
     
        // 3. Verificar cada fila
        const rows = document.querySelectorAll(`#${tableId} tr[data-borrower-id]`);
        if (rows.length === 0) {
            console.log('❌ No borrower rows found');
            return false;
        }
     
        const allRowsComplete = Array.from(rows).every(row => {
            const lenderInput = row.querySelector('input[data-type="lender"]');
            const borrowerInput = row.querySelector('input[data-type="borrower"]');
            const borrowerId = row.dataset.borrowerId;
     
            // Extraer solo el código contable (antes del guion)
            const lenderCode = lenderInput?.value?.split('-')[0]?.trim();
            const borrowerCode = borrowerInput?.value?.split('-')[0]?.trim();
     
            const isRowComplete = lenderCode && borrowerCode && borrowerId;
     
            if (!isRowComplete) {
                console.log('❌ Incomplete row:', { 
                    rowNumber: row.dataset.rowNumber,
                    lenderCode,
                    borrowerCode,
                    borrowerId
                });
            }
     
            return isRowComplete;
        });
     
        const isReady = allRowsComplete && hasDateRange;
        
        console.log('✅ Table readiness:', { 
            tableId,
            lenderId: tableId.split('-')[1], // Obtener tenant_id del lender del ID de la tabla
            hasDateRange,
            rowsCount: rows.length,
            isReady
        });
     
        return isReady;
     }

    /* PROCESAR SALDOS ######### PROCESAR SALDOS ########### PROCESAR SALDOS ############## */ 
    async processTableBalances(tableId) {
        console.log('Processing balances for table:', tableId);
        
        try {
            // 1. Obtener todas las filas de la tabla
            const rows = document.querySelectorAll(`#${tableId} tr[data-borrower-id]`);
            
            // 2. Mostrar indicador de procesamiento
            this.showProcessingState(tableId);
            
            // 3. Procesar cada fila
            for (const row of rows) {
                await this.processRowBalances(tableId, row);
            }
            
            // 4. Actualizar estado final
            this.showProcessComplete(tableId);
            
        } catch (error) {
            console.error('Error processing table balances:', error);
            this.showProcessError(tableId);
        }
    }
    
    async processRowBalances(tableId, rowElement) {
        try {
            // Mostrar indicador de procesamiento en la fila
            rowElement.classList.add('processing');
            
            // Obtener tenant_id completo
            const parts = tableId.split('-');
            parts.shift(); // Eliminar 'table'
            const timestamp = parts.pop(); // Eliminar el timestamp del final
            const lenderTenantId = parts.join('-'); // Unir el resto para obtener el tenant_id completo

            console.log('TableId:', tableId);
            console.log('Extracted lenderTenantId:', lenderTenantId);
            
            const lenderCode = rowElement.querySelector('input[data-type="lender"]').value.split('-')[0].trim();
            const borrowerTenantId = rowElement.dataset.borrowerId;
            const borrowerCode = rowElement.querySelector('input[data-type="borrower"]').value.split('-')[0].trim();
            
            // Obtener saldos
            const [lenderBalance, borrowerBalance] = await Promise.all([
                XeroBalanceService.getAccountBalance(lenderTenantId, lenderCode, window.dateRange.start, window.dateRange.end),
                XeroBalanceService.getAccountBalance(borrowerTenantId, borrowerCode, window.dateRange.start, window.dateRange.end)
            ]);
    
            // Actualizar la fila con los resultados
            this.updateRowWithBalances(rowElement, lenderBalance, borrowerBalance);
            
            // Marcar como procesado
            rowElement.classList.remove('processing');
            rowElement.classList.add('processed');
            
        } catch (error) {
            console.error('Error processing row:', error);
            rowElement.classList.add('process-error');
        }
    }
    
    // Métodos auxiliares para UI
    showProcessingState(tableId) {
        const button = document.getElementById(`process-${tableId}`);
        if (button) {
            button.disabled = true;
            button.innerHTML = '<span class="spinner"></span> Processing...';
        }
    }
    
    showProcessComplete(tableId) {
        const button = document.getElementById(`process-${tableId}`);
        if (button) {
            button.disabled = false;
            button.innerHTML = 'PROCESS BALANCE';
            // Agregar indicador de éxito a la tabla
            document.getElementById(tableId).classList.add('process-complete');
        }
    }
    
    showProcessError(tableId) {
        const button = document.getElementById(`process-${tableId}`);
        if (button) {
            button.disabled = false;
            button.innerHTML = 'PROCESS BALANCE';
            // Agregar indicador de error a la tabla
            document.getElementById(tableId).classList.add('process-error');
        }
    }
    
    updateRowWithBalances(rowElement, lenderBalance, borrowerBalance) {
        try {
            console.log('🔄 Calculando diferencias...', {
                lenderBalance,
                borrowerBalance
            });
    
            // Calcular diferencias correctamente
            //lenderBalance.difference = lenderBalance.finalBalance - lenderBalance.initialBalance;
            //borrowerBalance.difference = borrowerBalance.finalBalance - borrowerBalance.initialBalance;

            lenderBalance.difference = lenderBalance.finalBalance;
            borrowerBalance.difference = borrowerBalance.finalBalance;
    
            // Si el balance es 0, mostrar "No Transactions"
            if (lenderBalance.finalBalance === 0) {
                lenderBalance.difference = "No Transactions";
            }
            if (borrowerBalance.finalBalance === 0) {
                borrowerBalance.difference = "No Transactions";
            }
    
            // Obtener celdas relevantes
            const cells = rowElement.querySelectorAll('td');
            if (cells.length >= 8) {
                // LENT - saldo del prestamista
                cells[3].textContent = this.formatAmount(lenderBalance.difference);
                
                // PAID - saldo del prestatario (negativo porque es lo que debe)
                cells[6].textContent = this.formatAmount(borrowerBalance.difference);
                
                // BALANCE - diferencia entre LENT y PAID
                cells[7].textContent = this.formatAmount(
                    (lenderBalance.difference || 0) - (borrowerBalance.difference || 0)
                );
            }
    
            console.log('✅ Saldos actualizados en la fila');
        } catch (error) {
            console.error('❌ Error actualizando saldos:', error);
        }
    }
    
    
    formatAmount(amount) {
        if (amount === null || amount === undefined) return '0.00';
        return new Intl.NumberFormat('en-US', {
            style: 'decimal',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(Math.abs(amount)); // Usar Math.abs para mostrar valores positivos
    }

    getNextColorScheme() {
        const scheme = this.colorSchemes[this.currentColorIndex];
        this.currentColorIndex = (this.currentColorIndex + 1) % this.colorSchemes.length;
        return scheme;
    }
}