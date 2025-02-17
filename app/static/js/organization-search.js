class OrganizationSearchManager {
    constructor() {
        this.organizations = [];
        this._loadOrganizations();
    }

    _loadOrganizations() {
        this.organizations = JSON.parse(sessionStorage.getItem('organizations') || '[]');
    }

    setupSearch(config) {
        const { inputId, resultsId, onSelect, type = 'generic' } = config;
        const searchInput = document.getElementById(inputId);
        const searchResults = document.getElementById(resultsId);

        if (!searchInput || !searchResults) {
            console.error(`❌ Elementos de búsqueda no encontrados para ${type}`);
            return;
        }

        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim();
            this._handleSearch(query, searchResults, onSelect);
        });

        // Cerrar resultados al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.add('hidden');
            }
        });
    }

    _handleSearch(query, resultsDiv, onSelect) {
        if (query.length < 3) {
            resultsDiv.classList.add('hidden');
            return;
        }

        const filtered = this.organizations.filter(org => 
            org.name.toLowerCase().includes(query.toLowerCase())
        );

        this._displayResults(filtered, resultsDiv, onSelect);
    }

    _displayResults(organizations, resultsDiv, onSelect) {
        if (!organizations.length) {
            resultsDiv.innerHTML = '<div class="p-4 text-gray-500">No se encontraron organizaciones</div>';
        } else {
            resultsDiv.innerHTML = organizations.map(org => `
                <div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b"
                     onclick="window.organizationSearch.handleSelection('${org.id}', '${org.name}', '${onSelect}')"
                     role="button">
                    <p class="font-medium text-gray-900 dark:text-white">${org.name}</p>
                </div>
            `).join('');
        }
        
        resultsDiv.classList.remove('hidden');
    }

    handleSelection(id, name, callback) {
        if (typeof window[callback] === 'function') {
            window[callback](id, name);
        } else {
            console.error(`❌ Callback ${callback} no encontrado`);
        }
    }
}