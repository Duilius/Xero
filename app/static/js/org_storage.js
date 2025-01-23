// /app/static/js/org_storage.js
const OrgStorage = {
    // Guardar organizaciones en sessionStorage
    setOrganizations(orgs) {
        try {
            sessionStorage.setItem('connected_orgs', JSON.stringify(orgs));
            console.log('Organizations saved to storage');
        } catch (e) {
            console.error('Error saving organizations:', e);
        }
    },

    // Obtener organizaciones
    getOrganizations() {
        try {
            return JSON.parse(sessionStorage.getItem('connected_orgs') || '[]');
        } catch (e) {
            console.error('Error getting organizations:', e);
            return [];
        }
    },

    // Guardar organización seleccionada
    setSelectedOrg(org) {
        try {
            sessionStorage.setItem('selected_org', JSON.stringify(org));
        } catch (e) {
            console.error('Error saving selected organization:', e);
        }
    },

    // Obtener organización seleccionada
    getSelectedOrg() {
        try {
            return JSON.parse(sessionStorage.getItem('selected_org'));
        } catch (e) {
            console.error('Error getting selected organization:', e);
            return null;
        }
    }
};