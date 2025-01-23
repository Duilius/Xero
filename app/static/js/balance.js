// Variables globales
let searchTimeout;
const SEARCH_DELAY = 300;

// Un solo event listener para DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing balance.js');
    loadOrganizationsToStorage();
    initializeSearch();
    
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
function initializeSearch() {
    const searchInput = document.getElementById('org-search');
    const searchResults = document.getElementById('search-results');
    
    if (!searchInput || !searchResults) {
        console.error('Search elements not found');
        return;
    }

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 3) {
            hideSearchResults();
            return;
        }

        showSearchingIndicator();
        searchTimeout = setTimeout(() => performSearch(query), SEARCH_DELAY);
    });

    // Cerrar resultados al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            hideSearchResults();
        }
    });
}

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
 
 function hideSearchResults() {
    const resultsDiv = document.getElementById('search-results');
    if (resultsDiv) {
        resultsDiv.classList.add('hidden');
    }
 }
 
 // Búsqueda y resultados
 async function performSearch(query) {
    try {
        console.log('Performing search for:', query);
        const organizations = JSON.parse(sessionStorage.getItem('organizations') || '[]');
        const filtered = organizations.filter(org => 
            org.name.toLowerCase().includes(query.toLowerCase())
        );
        console.log('Filtered results:', filtered);
        displaySearchResults(filtered);
    } catch (error) {
        console.error('Search error:', error);
    } finally {
        hideSearchingIndicator();
    }
 }
 
 function displaySearchResults(organizations) {
    console.log('Displaying results:', organizations);
    const resultsDiv = document.getElementById('search-results');
    if (!resultsDiv) return;
 
    if (!organizations || organizations.length === 0) {
        resultsDiv.innerHTML = `
            <div class="p-4 text-gray-500 dark:text-gray-400">
                No organizations found
            </div>
        `;
    } else {
        resultsDiv.innerHTML = organizations.map(org => `
            <button 
                onclick="selectOrganization('${org.id}', '${org.name}')"
                class="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700">
                <p class="font-medium text-gray-900 dark:text-white">${org.name}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400">${org.id}</p>
            </button>
        `).join('');
    }
 
    resultsDiv.classList.remove('hidden');
 }
 
 // Manejo del balance
 async function selectOrganization(orgId, orgName) {
    console.log('Selected organization:', { id: orgId, name: orgName });
    hideSearchResults();
    showLoadingBalance();
 
    try {
        const response = await fetch(`/api/organizations/${orgId}/balance`, {
            credentials: 'include'
        });
 
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
 
        const data = await response.json();
        console.log('Balance data:', data);
        displayBalance(data);
    } catch (error) {
        console.error('Error loading balance:', error);
        showError('Error loading organization balance');
    } finally {
        hideLoadingBalance();
    }
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