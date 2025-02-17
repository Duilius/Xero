document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicializar tablesManager primero
    console.log('🔧 Inicializando LendingTablesManager');
    
    window.tablesManager = new window.LendingTablesManager();
    
    // 2. Inicializar estado global
    window.lendingState = new LendingState();
    
    // 3. Inicializar UI manager
    window.lendingUI = new LendingUI(window.lendingState);
    
    // 4. Inicializar búsqueda
    window.organizationSearch = new OrganizationSearchManager();

    // Definir selectLenderAccount antes de que se use
    window.selectLenderAccount = function(code, name) {
        console.log('💼 selectLenderAccount llamado:', {code, name});
        try {
            console.log('Estado anterior:', window.selectedLender);
            
            if (!window.selectedLender) {
                console.error('❌ No hay prestamista seleccionado');
                return;
            }

            // Actualizar datos de cuenta en selectedLender
            window.selectedLender.accountCode = code;
            window.selectedLender.accountName = name;
    
            // Crear tabla directamente
            console.log('Creando tabla para:', window.selectedLender);
            window.tablesManager.createTable(
                window.selectedLender.id, 
                window.selectedLender.name, 
                code
            );
        } catch (error) {
            console.error('❌ Error en selectLenderAccount:', error);
        }
    };
    
    // 5. Configurar búsqueda de lender
    window.organizationSearch.setupSearch({
        inputId: 'lender-org-search',
        resultsId: 'lender-search-results',
        onSelect: 'selectLenderOrg',
        type: 'lender'
    });
    
    // 6. Configurar búsqueda de borrower
    window.organizationSearch.setupSearch({
        inputId: 'borrower-org-search',
        resultsId: 'borrower-search-results',
        onSelect: 'selectBorrowerOrg',
        type: 'borrower'
    });

    
    // 8. Definir funciones globales
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

            // Agregar a la tabla usando tablesManager
            window.tablesManager.addBorrowerToTable(currentTableId, borrowerData);
            
            window.lendingUI.hideQuickMenu();
        } catch (error) {
            console.error('❌ Error en selectBorrowerOrg:', error);
        }
    };

    window.selectBorrowerAccount = function(code, name) {
        console.log('💼 selectBorrowerAccount llamado:', {code, name});
        try {
            const currentTableId = window.currentLendingTableId;
            if (!currentTableId || !window.selectedBorrower) {
                console.error('❌ No hay tabla activa o borrower seleccionado');
                return;
            }
    
            // Completar datos del borrower con el código de cuenta
            const borrowerData = {
                ...window.selectedBorrower,
                accountCode: code,
                accountName: name
            };
    
            // Agregar a la tabla
            window.tablesManager.addBorrowerToTable(currentTableId, borrowerData);
            
            // Limpiar UI
            window.lendingUI.hideQuickMenu();
        } catch (error) {
            console.error('❌ Error en selectBorrowerAccount:', error);
        }
    };

    window.selectLenderOrg = function(id, name) {
        console.log('🏦 Lender seleccionado:', {id, name});
        try {
            // Guardar datos del lender
            window.selectedLender = {
                id: id,
                name: name,
                accountCode: null,
                accountName: null
            };
    
            // Crear tabla inmediatamente
            window.tablesManager.createTable(id, name);
    
            // Actualizar UI
            window.lendingUI.updateLenderUI(name);
            
        } catch (error) {
            console.error('❌ Error en selectLenderOrg:', error);
        }
    };

    window.updateDateRange = function(startDate, endDate) {
        console.log('Updating dates before adjustment:', {startDate, endDate});
        
        if (startDate === 'no-date' || endDate === 'no-date') {
            window.dateRange = { start: null, end: null };
        } else {
            // Ajustar la fecha final para que incluya todo el día
            const endDateAdjusted = new Date(endDate);
            endDateAdjusted.setUTCHours(23, 59, 59, 999);
            
            console.log('Date adjustment:', {
                original: endDate,
                adjusted: endDateAdjusted.toISOString()
            });
    
            window.dateRange = {
                start: startDate,
                end: endDateAdjusted.toISOString()
            };
        }
    
        // Actualizar títulos de todas las tablas
        const tables = document.querySelectorAll('[id^="table-"]');
        tables.forEach(table => {
            const titleElement = table.querySelector('.text-lg.font-semibold');
            if (titleElement) {
                const lenderName = titleElement.textContent.split('(')[0].trim();
                const dateText = window.dateRange.start ? 
                    `(${formatDate(window.dateRange.start)} to ${formatDate(window.dateRange.end)})` : 
                    '(Select date range)';
                
                titleElement.textContent = `${lenderName} ${dateText}`;
            }
        });
    
        // Verificar estado de los botones PROCESS BALANCE
        tables.forEach(table => {
            window.tablesManager.checkProcessButtonStatus(table.id);
        });
    };
    
    function formatDate(dateStr) {
        // Asegurar que no perdemos el día en la conversión de zona horaria
        const date = new Date(dateStr);
        const utcDay = date.getUTCDate();
        const utcMonth = date.getUTCMonth();
        const utcYear = date.getUTCFullYear();
        
        return new Date(Date.UTC(utcYear, utcMonth, utcDay))
            .toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                timeZone: 'UTC'
            });
    }

    console.log('🚀 Módulos de lending inicializados');
});