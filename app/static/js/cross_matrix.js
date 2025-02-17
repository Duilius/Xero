// static/js/cross_matrix.js

// Almacenamiento de estado
const state = {
    selectedAccounts: new Set(),
    selectedOrgs: new Set(),
    accountsData: {},
    matrixData: {}
};

// Inicialización
async function initializeCrossMatrix() {
    try {
        // Cargar estructura de cuentas
        const response = await fetch('/api/codigos');
        const data = await response.json();
        
        if (data.status === 'success') {
            state.accountsData = data.data;
            setupAccountSelector();
            setupOrgSelector();
        }
    } catch (error) {
        console.error('Error initializing:', error);
        showError('Error al cargar datos iniciales');
    }
}

// Configurar selector de cuentas
function setupAccountSelector() {
    const accountList = document.getElementById('accountList');
    const uniqueAccounts = new Set();
    
    // Recolectar cuentas únicas de todas las organizaciones
    Object.values(state.accountsData).forEach(org => {
        org.accounts.forEach(account => {
            uniqueAccounts.add(JSON.stringify({
                id: account.AccountID,
                code: account.Code,
                name: account.Name,
                type: account.Type
            }));
        });
    });
    
    // Crear elementos de lista
    Array.from(uniqueAccounts).forEach(accountStr => {
        const account = JSON.parse(accountStr);
        const div = document.createElement('div');
        div.className = 'account-item p-2 hover:bg-gray-100 cursor-pointer';
        div.innerHTML = `
            <span class="font-mono">${account.code}</span>
            <span class="ml-2">${account.name}</span>
            <span class="ml-2 text-sm text-gray-500">${account.type}</span>
        `;
        div.onclick = () => toggleAccount(account);
        accountList.appendChild(div);
    });
}

// Configurar selector de organizaciones
function setupOrgSelector() {
    const orgList = document.getElementById('orgList');
    
    Object.entries(state.accountsData).forEach(([orgName, orgData]) => {
        const div = document.createElement('div');
        div.className = 'org-item p-2 hover:bg-gray-100 cursor-pointer';
        div.innerHTML = `
            <span>${orgName}</span>
        `;
        div.onclick = () => toggleOrg(orgName, orgData.tenant_id);
        orgList.appendChild(div);
    });
}

// Manejar selección de cuenta
function toggleAccount(account) {
    const accountKey = account.id;
    if (state.selectedAccounts.has(accountKey)) {
        state.selectedAccounts.delete(accountKey);
    } else {
        state.selectedAccounts.add(accountKey);
    }
    updateMatrix();
}

// Manejar selección de organización
function toggleOrg(orgName, tenantId) {
    const orgKey = tenantId;
    if (state.selectedOrgs.has(orgKey)) {
        state.selectedOrgs.delete(orgKey);
    } else {
        state.selectedOrgs.add(orgKey);
    }
    updateMatrix();
}

// Actualizar matriz cruzada
async function updateMatrix() {
    if (state.selectedAccounts.size === 0 || state.selectedOrgs.size === 0) {
        return;
    }
    
    const matrix = document.getElementById('crossMatrix');
    const tbody = matrix.querySelector('tbody');
    tbody.innerHTML = '';
    
    // Crear encabezados
    const header = matrix.querySelector('thead tr');
    header.innerHTML = '<th class="border p-2">Cuenta/Org</th>';
    Array.from(state.selectedOrgs).forEach(orgId => {
        const orgName = Object.entries(state.accountsData)
            .find(([_, data]) => data.tenant_id === orgId)[0];
        header.innerHTML += `<th class="border p-2">${orgName}</th>`;
    });
    
    // Llenar datos
    Array.from(state.selectedAccounts).forEach(accountId => {
        const row = document.createElement('tr');
        const accountInfo = getAccountInfo(accountId);
        
        // Primera columna: nombre de cuenta
        row.innerHTML = `<td class="border p-2">${accountInfo.code} - ${accountInfo.name}</td>`;
        
        // Columnas de organizaciones
        Array.from(state.selectedOrgs).forEach(orgId => {
            const value = state.matrixData[`${accountId}-${orgId}`] || '';
            row.innerHTML += `<td class="border p-2">${value}</td>`;
        });
        
        tbody.appendChild(row);
    });
}

// Funciones auxiliares
function getAccountInfo(accountId) {
    for (const org of Object.values(state.accountsData)) {
        const account = org.accounts.find(acc => acc.AccountID === accountId);
        if (account) {
            return account;
        }
    }
    return null;
}

function showError(message) {
    // Implementar mostrar error al usuario
    console.error(message);
}

// Inicializar cuando el documento esté listo
document.addEventListener('DOMContentLoaded', initializeCrossMatrix);