class LendingState {
    constructor() {
        this.selectedLender = null;
        this.selectedBorrower = null;
        this.lenderAccount = null;
        this.borrowerAccount = null;
        this.dateRange = {
            start: null,
            end: null
        };
    }

    setLender(id, name) {
        this.selectedLender = { id, name, accountCode: null };
        return this.selectedLender;
    }

    setBorrower(id, name) {
        this.selectedBorrower = { id, name, accountCode: null };
        return this.selectedBorrower;
    }

    setLenderAccount(code, name) {
        if (!this.selectedLender) {
            throw new Error('No hay prestamista seleccionado');
        }
        this.lenderAccount = { code, name };
        this.selectedLender.accountCode = code;
        return this.lenderAccount;
    }

    setBorrowerAccount(code, name) {
        if (!this.selectedBorrower) {
            throw new Error('No hay prestatario seleccionado');
        }
        this.borrowerAccount = { code, name };
        this.selectedBorrower.accountCode = code;
        return this.borrowerAccount;
    }

    setDateRange(start, end) {
        this.dateRange = { start, end };
        return this.dateRange;
    }

    reset() {
        this.selectedLender = null;
        this.selectedBorrower = null;
        this.lenderAccount = null;
        this.borrowerAccount = null;
        this.dateRange = { start: null, end: null };
    }
}