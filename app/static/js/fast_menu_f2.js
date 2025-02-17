setupQuickMenu(){
    // Crear botón para abrir/cerrar el menú
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'menu-toggle fixed right-0 top-1/2 -translate-y-1/2 bg-primary-600 text-white p-2 rounded-l-lg shadow-lg z-40 transition-all duration-300';
    toggleBtn.innerHTML = '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>';
    //toggleBtn.onclick = () => this.toggleQuickMenu();
    toggleBtn.onclick = () => menu.classList.toggle('translate-x-full');
    
    
    // Crear contenedor del menú
    const menu = document.createElement('div');
    menu.id = 'quick-menu';
    menu.className = 'fixed right-0 top-0 h-full w-64 bg-white dark:bg-gray-800 shadow-lg transform translate-x-full transition-transform duration-300 z-50';
    
    document.body.appendChild(toggleBtn);
    document.body.appendChild(menu);

    // Cargar contenido HTML del menú y agregar lógica
    fetch('/fast_menu_f2')
        .then(response => response.text())
        .then(html => {
            menu.innerHTML = html;

            // Inicializar eventos del menú
            this.initializeMenuEvents();
        })
        .catch(error => console.error('Error al cargar el menú:', error));
}

// Inicializar eventos y manejar datos compartidos
initializeMenuEvents() {
    // Fecha seleccionada
    const datePicker = document.getElementById('date-picker');
    datePicker.addEventListener('change', (e) => {
        const selectedDate = e.target.value;
        console.log('Fecha seleccionada:', selectedDate);
        // Actualizar el home con la fecha seleccionada
        this.updateHomeWithFilters({ date: selectedDate });
    });

    // Organización seleccionada
    const orgSelect = document.getElementById('organization-select');
    this.loadOrganizations(orgSelect);
    orgSelect.addEventListener('change', (e) => {
        const selectedOrg = e.target.value;
        console.log('Organización seleccionada:', selectedOrg);
        // Actualizar el home con la organización seleccionada
        this.updateHomeWithFilters({ organization: selectedOrg });
    });

    // Buscar código
    const searchButton = document.getElementById('search-button');
    searchButton.addEventListener('click', () => {
        const searchInput = document.getElementById('code-search').value;
        console.log('Código a buscar:', searchInput);
        // Realizar búsqueda en el servidor
        this.searchCode(searchInput);
    });
}

// Cargar organizaciones desde el servidor
loadOrganizations(selectElement) {
    fetch('/api/organizations') // Endpoint de ejemplo
        .then(response => response.json())
        .then(data => {
            data.forEach(org => {
                const option = document.createElement('option');
                option.value = org.id;
                option.textContent = org.name;
                selectElement.appendChild(option);
            });
        })
        .catch(error => console.error('Error al cargar organizaciones:', error));
}

// Actualizar el home con filtros
updateHomeWithFilters(filters) {
    // Comunicar los filtros al home
    window.dispatchEvent(new CustomEvent('updateFilters', { detail: filters }));
}

// Buscar códigos en el servidor
searchCode(code) {
    fetch(`/api/search?code=${encodeURIComponent(code)}`)
        .then(response => response.json())
        .then(data => {
            console.log('Resultados de búsqueda:', data);
            // Actualizar resultados en el home
            window.dispatchEvent(new CustomEvent('updateSearchResults', { detail: data }));
        })
        .catch(error => console.error('Error al buscar el código:', error));
}