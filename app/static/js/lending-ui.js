class LendingUI {
    constructor(state) {
        this.state = state;
    }

    updateLenderUI(name) {
        const searchInput = document.getElementById('lender-org-search');
        if (searchInput) {
            searchInput.value = name;
        }
        document.getElementById('lender-search-results')?.classList.add('hidden');
    }

    updateBorrowerUI(name) {
        const searchInput = document.getElementById('borrower-org-search');
        if (searchInput) {
            searchInput.value = name;
        }
        document.getElementById('borrower-search-results')?.classList.add('hidden');
    }

    hideQuickMenu() {
        const quickMenu = document.getElementById('quick-menu');
        if (quickMenu) {
            quickMenu.classList.add('translate-x-full');
        }
    }
}