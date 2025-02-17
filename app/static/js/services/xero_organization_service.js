// app/static/js/services/xero_organization_service.js
class XeroOrganizationService {
    async getFinancialYearEnd(token, orgId) {
        const response = await fetch('/api/xero/organization', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch organization details');
        
        const data = await response.json();
        return {
            day: data.FinancialYearEndDay,
            month: data.FinancialYearEndMonth,
            currency: data.BaseCurrency
        };
    }
}

window.xeroOrgService = new XeroOrganizationService();