//JavaScript para manejar las interacciones
// static/js/adjustments.js
function loadComparison() {
    const orgId = document.getElementById('company-select').value;
    if (!orgId) return;

    htmx.ajax('GET', `/api/adjustments/compare/${orgId}`, {
        target: '#comparison-data',
        swap: 'innerHTML'
    });
}

// Función para abrir el modal
function openAdjustmentModal(orgName, orgId) {
    const modal = document.getElementById('adjustment-modal');
    document.getElementById('org-name').textContent = orgName;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}


function openAdjustmentModal(orgName, orgId) {
    console.log('Opening modal for:', orgName, orgId);
    const modal = document.getElementById('adjustment-modal');
    if (modal) {
        // Actualizar título
        document.getElementById('org-name').textContent = orgName;

        // Filtrar el select
        const selectElement = document.getElementById('compare-company');
        Array.from(selectElement.options).forEach(option => {
            if (option.value === orgId) {
                option.remove(); // Eliminar la opción de la org seleccionada
            }
        });

        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

window.compareOrganizations = function() {
    const selectedOrgId = document.getElementById('compare-company').value;
    const url = `/adjustments/compare/${selectedOrgId}`;
    console.log('Attempting request with cookies:', document.cookie);  // Debug
    console.log('Attempting to request:', url);

     // Verificar todas las cookies
     console.log('All cookies:', document.cookie);

      // Verificar todas las cookies
    console.log('All cookies:', document.cookie);
    
    // Verificación más detallada
    if (!document.cookie) {
        console.error('No cookies present at all');
        //window.location.href = '/auth/login';
        return;
    }
    
     // Si no hay cookie de sesión, redirigir al login
     if (!document.cookie.includes('session=')) {
         console.error('Session cookie not found - current cookies:', document.cookie);
         console.error('No session cookie found');
         //window.location.href = '/auth/login';
         return;
     }

     fetch(url, {
        method: 'GET',
        credentials: 'include',  //# Cambiado de 'same-origin' a 'include'
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
    })
    .then(data => {
        document.getElementById('comparison-area').innerHTML = data;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}