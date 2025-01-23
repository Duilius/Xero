// relationships.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    const tabs = document.querySelectorAll('.tab-button');
    tabs.forEach(tab => {
        console.log('Registering click for tab:', tab.id);
        tab.addEventListener('click', function() {
            console.log('Tab clicked:', this.dataset.view);
            switchView(this.dataset.view);
        });
    });
});

function switchView(view) {
    try {
        const loansView = document.getElementById('loans-view');
        const relationshipsView = document.getElementById('relationships-view');
        const loansTab = document.getElementById('loans-tab');
        const relationshipsTab = document.getElementById('relationships-tab');

        if (loansView && relationshipsView && loansTab && relationshipsTab) {
            // Toggle active tab
            loansTab.classList.toggle('active-tab', view === 'loans');
            relationshipsTab.classList.toggle('active-tab', view === 'relationships');

            // Toggle views
            loansView.classList.toggle('hidden', view !== 'loans');
            relationshipsView.classList.toggle('hidden', view !== 'relationships');

            if (view === 'relationships') {
                loadOrganizationsList();
            }
        }
    } catch (error) {
        console.error('Error switching view:', error);
    }
}