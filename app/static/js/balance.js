// Variables globales
let searchTimeout;
const SEARCH_DELAY = 300;

// Un solo event listener para DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing balance.js');
    loadOrganizationsToStorage();
    
    // Forzar modo oscuro
    if (!localStorage.getItem('darkMode')) {
        localStorage.setItem('darkMode', 'true');
        document.documentElement.classList.add('dark');
    }
});

// Cargar organizaciones
async function loadOrganizationsToStorage() {
    try {
        console.log('Starting to load organizations...');
        const response = await fetch('/api/organizations/list', {
            credentials: 'include'
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) throw new Error('Failed to load organizations');
        
        const data = await response.json();
        console.log('Data received:', data);
        
        sessionStorage.setItem('organizations', JSON.stringify(data.organizations));
        console.log('Organizations stored in sessionStorage:', sessionStorage.getItem('organizations'));
    } catch (error) {
        console.error('Error loading organizations:', error);
    }
}

// Inicializar búsqueda


// Funciones de UI
function showSearchingIndicator() {
    const indicator = document.getElementById('search-indicator');
    if (indicator) {
        indicator.classList.remove('hidden');
    }
 }
 
 function hideSearchingIndicator() {
    const indicator = document.getElementById('search-indicator');
    if (indicator) {
        indicator.classList.add('hidden');
    }
 }
 
 // Manejo del CUADRO COMBINADO: 1° Formar tabla con ORGANIZACIONES 🙋‍♂️
 // Actualizar esta función
 async function selectOrganization2(organizationId, organizationName) {
    console.log('selectOrganization called with:', { organizationId, organizationName });
    try {
        // Mostrar indicador de búsqueda
        const searchIndicator = document.getElementById('search-indicator');
        if (searchIndicator) {
            console.log('Showing search indicator');
            searchIndicator.classList.remove('hidden');
        }
        
        const response = await fetch(`/api/organizations/${organizationId}`);
        console.log('Response received:', response.status);
        
        if (!response.ok) {
            throw new Error('Error loading organization data');
        }
        
        const data = await response.json();
        console.log('Organization data received:', data);
        
        // Actualizar input sin ocultar resultados
        const searchInput = document.getElementById('org-search');
        if (searchInput) {
            searchInput.value = organizationName;
        }

        // Mostrar resultados nuevos
        const searchResults = document.getElementById('search-results');
        if (searchResults) {
            // Mantener visible
            searchResults.classList.remove('hidden');
            
            searchResults.innerHTML = `
                <div class="p-4 border-b bg-white dark:bg-gray-800">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 id="${data.data.id}" class="font-bold text-gray-900 dark:text-white">${data.data.name}</h3>
                        </div>
                        <div class="px-2 py-1 text-xs font-semibold rounded ${
                            data.data.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }">
                            ${data.data.status}
                        </div>
                    </div>
                    <div class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                        <p class="text-sm text-gray-600 dark:text-gray-300">
                            Última sincronización: ${data.data.last_sync ? new Date(data.data.last_sync).toLocaleString() : 'Sin sincronizar'}
                        </p>
                    </div>
                </div>
            `;
            console.log('Results displayed');
        }
        
    } catch (error) {
        console.error('Error loading organization:', error);
        showError('Error al cargar datos de la organización');
    } finally {
        const searchIndicator = document.getElementById('search-indicator');
        if (searchIndicator) {
            searchIndicator.classList.add('hidden');
        }
    }
}


function updateOrganizationDisplay(data) {
    const orgInfo = document.getElementById('organizationInfo');
    if (orgInfo) {
        orgInfo.innerHTML = `
            <div class="bg-white shadow rounded-lg p-4">
                <h3 class="text-lg font-semibold mb-2">${data.organization_name}</h3>
                <p class="text-gray-600">ID: ${data.organization_id}</p>
                <div class="mt-4">
                    <!-- Aquí podemos agregar más información según lo que devuelva el endpoint -->
                    <pre class="text-sm">${JSON.stringify(data.data, null, 2)}</pre>
                </div>
            </div>
        `;
        orgInfo.classList.remove('hidden');
    }
}

function showLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.classList.remove('hidden');
    }
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.classList.add('hidden');
    }
}


function showMessage(message) {
    // Implementar mostrar mensaje al usuario
    console.log(message);
}
 
 function showLoadingBalance() {
    const balanceView = document.getElementById('balance-sheet-view');
    if (balanceView) {
        balanceView.innerHTML = `
            <div class="flex items-center justify-center h-64">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        `;
        balanceView.classList.remove('hidden');
    }
 }
 
 function hideLoadingBalance() {
    // Se reemplaza automáticamente cuando se muestra el balance
 }
 
 function showError(message) {
    console.error(message);
    // TODO: Implementar notificación visual de error
 }
 
 
 function displayBalance(data) {
    const balanceView = document.getElementById('balance-sheet-view');
    if (!balanceView) return;

    // Mostrar los datos del balance
    // En lugar de incluir el template directamente
    balanceView.innerHTML = `
        <div class="grid grid-cols-2 gap-6">
            <!-- Contenido del balance -->
            ...
        </div>
    `;
}


/* ############# SINCRONiZA CON XERO ===> Botón "Sync With Xero" ################################### */
// En balance.js
// balance.js
// balance.js actualizado
async function syncWithXero() {
    const button = document.querySelector('[hx-get="/api/sync"]');
    const originalHtml = button.innerHTML;

    button.addEventListener('click', async function(e) {
        e.preventDefault();
        button.innerHTML = `<svg class="animate-spin h-5 w-5 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg> Syncing...`;
        
        try {
            const orgs = JSON.parse(sessionStorage.getItem('organizations') || '[]');
            
            // Esperar a que todas las sincronizaciones terminen
            await Promise.all(orgs.map(org => 
                fetch(`/api/accounts/sync/${org.id}`).then(response => {
                    if (!response.ok) {
                        throw new Error(`Sync failed for org ${org.id}`);
                    }
                    return response;
                })
            ));
            
            // Actualizar timestamp solo si todo fue exitoso
            //document.getElementById('sync-status').textContent = 
            //    `Last synced: ${new Date().toLocaleString()}`;
                
        } catch (error) {
            console.error('Sync error:', error);
            // Manejar el error en la UI
        } finally {
            button.innerHTML = originalHtml;
        }
    });
}

/* ##################   SINCRONIZACION POR EMPRESA  ######################## */
async function showSyncDialog() {
    const orgs = JSON.parse(sessionStorage.getItem('organizations') || '[]');
    
    // Crear el diálogo modal con una tabla para mejor visualización
    const dialog = document.createElement('div');
    dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    dialog.innerHTML = `
        <div class="bg-white p-6 rounded-lg shadow-xl max-w-4xl w-full">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold">Select Organizations to Sync</h2>
                <button onclick="closeDialog()" class="text-gray-500 hover:text-gray-700">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            <div class="max-h-[60vh] overflow-y-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                <input type="checkbox" id="select-all" class="form-checkbox">
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Organization
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Last Sync
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${orgs.map(org => `
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <input type="checkbox" value="${org.id}" class="form-checkbox org-checkbox">
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    ${org.name}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500" id="last-sync-${org.id}">
                                    ${org.last_sync}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm" id="status-${org.id}">
                                    Ready
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="mt-4 flex justify-end space-x-3">
                <button class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300" onclick="closeDialog()">Cancel</button>
                <button id="sync-button" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" onclick="syncSelected()">
                    Sync Selected
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Manejar selección de todas las organizaciones
    const selectAllCheckbox = document.getElementById('select-all');
    selectAllCheckbox.addEventListener('change', (e) => {
        document.querySelectorAll('.org-checkbox').forEach(checkbox => {
            checkbox.checked = e.target.checked;
        });
    });

    // Cargar el último estado de sincronización para cada organización
    await loadSyncStatus(orgs);
}

async function loadSyncStatus(orgs) {
    try {
        for (const org of orgs) {
            const lastSyncElement = document.getElementById(`last-sync-${org.id}`);
            //alert("eeeeee "+ org.last_sync);
            try {
                const response = await fetch(`/api/organizations/${org.id}`);
                const data = await response.json();
                
                if (org.last_sync) {
                    lastSyncElement.textContent = new Date(org.last_sync).toLocaleString();
                } else {
                    lastSyncElement.textContent = 'Never'; /* 'Never' */
                }
            } catch (error) {
                lastSyncElement.textContent = 'Error loading';
            }
        }
    } catch (error) {
        console.error('Error loading sync status:', error);
    }
}


async function syncSelected() {
    const selectedOrgs = Array.from(document.querySelectorAll('.org-checkbox:checked'))
        .map(cb => ({ id: cb.value }));
    
    if (selectedOrgs.length === 0) {
        alert('Please select at least one organization');
        return;
    }

    const syncButton = document.getElementById('sync-button');
    syncButton.disabled = true;
    syncButton.innerHTML = 'Syncing...';

    try {
        // Sincronizar organizaciones de 5 en 5 para no sobrecargar
        const batchSize = 5;
        for (let i = 0; i < selectedOrgs.length; i += batchSize) {
            const batch = selectedOrgs.slice(i, i + batchSize);
            await Promise.all(batch.map(org => syncOrganization(org.id)));
        }
        
        //alert('Synchronization completed successfully!');
    } catch (error) {
        console.error('Sync error:', error);
        alert('Error during synchronization');
    } finally {
        //closeDialog(); /* Enviar a grabar en tablas y actualizar LocalSession */
        syncButton.innerHTML = 'Sync Selected';
    }
}


async function syncOrganization(orgId) {
    const statusElement = document.getElementById(`status-${orgId}`);
    const lastSyncElement = document.getElementById(`last-sync-${orgId}`);
    
    try {
        statusElement.textContent = 'Syncing...';
        statusElement.className = 'text-blue-500';
        
        const response = await fetch(`/api/accounts/sync/${orgId}`);
        if (!response.ok) throw new Error(`Sync failed for org ${orgId}`);
        
        const now = new Date().toLocaleString();
        lastSyncElement.textContent = now;
        statusElement.textContent = 'Completed';
        statusElement.className = 'text-green-500';
    } catch (error) {
        statusElement.textContent = 'Failed';
        statusElement.className = 'text-red-500';
        throw error;
    }
}


function closeDialog() {
    const dialog = document.querySelector('.fixed');
    if (dialog) {
        dialog.remove();
    }
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    const syncButton = document.querySelector('[hx-get="/api/sync"]');
    if (syncButton) {
        syncButton.removeAttribute('hx-get'); // Remover el atributo hx-get para evitar el comportamiento por defecto
        syncButton.addEventListener('click', showSyncDialog);
    }
});

document.addEventListener('DOMContentLoaded', syncWithXero);